#!/usr/bin/env python3
"""Serve the generated reader and its repository-backed notes API."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import discussions
import local_library


WEB_ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = WEB_ROOT.parent
DIST_ROOT = WEB_ROOT / "dist"
NOTES_ROOT = BOOK_ROOT / "Notes/Annotations"
DISCUSSIONS_ROOT = BOOK_ROOT / "Notes/Discussions"
READING_ROOT = BOOK_ROOT / "Reading"
SOURCES_ROOT = BOOK_ROOT / "Sources"
DEFAULT_NOTE_PATHS = {f"{chapter:02d}": NOTES_ROOT / f"{chapter:02d}.json" for chapter in range(1, 21)}
DEFAULT_CHAPTER_PATHS = discussions.discover_chapter_paths(READING_ROOT)
DEFAULT_FOOTNOTE_PATHS = {
    chapter_id: BOOK_ROOT / f"References/Footnotes-{chapter_id}.md"
    for chapter_id in DEFAULT_CHAPTER_PATHS
}

MAX_REQUEST_BYTES = 1_000_000
MAX_LIBRARY_REQUEST_BYTES = 28_000_000
CONTEXT_BUILD_TTL_SECONDS = 300
NOTES_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/notes\Z")
DISCUSSION_LIST_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/discussions\Z")
DISCUSSION_PREVIEW_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/discussions/context-preview\Z")
DISCUSSION_ROUTE_RE = re.compile(r"\A/api/discussions/([^/]+)\Z")
DISCUSSION_MESSAGES_ROUTE_RE = re.compile(r"\A/api/discussions/([^/]+)/messages\Z")
LIBRARY_IMPORT_CONFIRM_ROUTE_RE = re.compile(r"\A/api/library/imports/([^/]+)/confirm\Z")
LIBRARY_SOURCE_ROUTE_RE = re.compile(r"\A/api/library/sources/([^/]+)\Z")
LIBRARY_DERIVED_ROUTE_RE = re.compile(r"\A/api/library/sources/([^/]+)/derived\Z")
SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
TIMESTAMP_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z")


class ValidationError(ValueError):
    """Raised when a note document does not match schema version 1."""


def empty_note_document(chapter_id: str) -> dict[str, Any]:
    return {"schemaVersion": 1, "bookId": "qfg", "chapterId": chapter_id, "notes": []}


def validate_timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not TIMESTAMP_RE.fullmatch(value):
        raise ValidationError(f"{field} must be a UTC ISO 8601 timestamp ending in Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} is not a valid timestamp") from error
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise ValidationError(f"{field} has invalid fields: {'; '.join(details)}")


def normalize_note_document(value: Any, chapter_id: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("document must be a JSON object")
    require_exact_keys(value, {"schemaVersion", "bookId", "chapterId", "notes"}, "document")

    if value["schemaVersion"] != 1:
        raise ValidationError("schemaVersion must be 1")
    if value["bookId"] != "qfg":
        raise ValidationError("bookId must be qfg")
    if value["chapterId"] != chapter_id:
        raise ValidationError("chapterId does not match the requested chapter")
    if not isinstance(value["notes"], list):
        raise ValidationError("notes must be an array")

    normalized_notes: list[dict[str, Any]] = []
    note_ids: set[str] = set()
    ranges_by_block: dict[str, list[tuple[int, int]]] = {}

    note_keys = {"id", "sourceRevision", "anchor", "body", "format", "createdAt", "updatedAt"}
    anchor_keys = {"blockId", "startOffset", "endOffset", "exact", "prefix", "suffix"}

    for index, note in enumerate(value["notes"]):
        field = f"notes[{index}]"
        if not isinstance(note, dict):
            raise ValidationError(f"{field} must be an object")
        require_exact_keys(note, note_keys, field)

        note_id = note["id"]
        if not isinstance(note_id, str):
            raise ValidationError(f"{field}.id must be a UUID string")
        try:
            UUID(note_id)
        except ValueError as error:
            raise ValidationError(f"{field}.id must be a UUID string") from error
        if note_id in note_ids:
            raise ValidationError(f"duplicate note id: {note_id}")
        note_ids.add(note_id)

        source_revision = note["sourceRevision"]
        if not isinstance(source_revision, str) or not SHA256_RE.fullmatch(source_revision):
            raise ValidationError(f"{field}.sourceRevision must be a lowercase SHA-256 hex digest")

        anchor = note["anchor"]
        if not isinstance(anchor, dict):
            raise ValidationError(f"{field}.anchor must be an object")
        require_exact_keys(anchor, anchor_keys, f"{field}.anchor")

        block_id = anchor["blockId"]
        start = anchor["startOffset"]
        end = anchor["endOffset"]
        exact = anchor["exact"]
        prefix = anchor["prefix"]
        suffix = anchor["suffix"]
        if not isinstance(block_id, str) or not block_id.strip():
            raise ValidationError(f"{field}.anchor.blockId must be non-empty")
        if not isinstance(start, int) or isinstance(start, bool) or start < 0:
            raise ValidationError(f"{field}.anchor.startOffset must be a non-negative integer")
        if not isinstance(end, int) or isinstance(end, bool) or end <= start:
            raise ValidationError(f"{field}.anchor.endOffset must be greater than startOffset")
        if not isinstance(exact, str) or not exact.strip():
            raise ValidationError(f"{field}.anchor.exact must be non-empty")
        exact_utf16_length = len(exact.encode("utf-16-le")) // 2
        if end - start != exact_utf16_length:
            raise ValidationError(f"{field}.anchor offsets must match the exact text length")
        if not isinstance(prefix, str) or len(prefix) > 32:
            raise ValidationError(f"{field}.anchor.prefix must contain at most 32 characters")
        if not isinstance(suffix, str) or len(suffix) > 32:
            raise ValidationError(f"{field}.anchor.suffix must contain at most 32 characters")

        for existing_start, existing_end in ranges_by_block.setdefault(block_id, []):
            if start < existing_end and end > existing_start:
                raise ValidationError(f"{field}.anchor overlaps another note in {block_id}")
        ranges_by_block[block_id].append((start, end))

        body = note["body"]
        if not isinstance(body, str) or not body.strip():
            raise ValidationError(f"{field}.body must be non-blank plain text")
        if note["format"] != "plain-text":
            raise ValidationError(f"{field}.format must be plain-text")

        created_at = validate_timestamp(note["createdAt"], f"{field}.createdAt")
        updated_at = validate_timestamp(note["updatedAt"], f"{field}.updatedAt")
        created_datetime = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        updated_datetime = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if updated_datetime < created_datetime:
            raise ValidationError(f"{field}.updatedAt cannot be earlier than createdAt")

        normalized_notes.append(
            {
                "id": note_id,
                "sourceRevision": source_revision,
                "anchor": {
                    "blockId": block_id,
                    "startOffset": start,
                    "endOffset": end,
                    "exact": exact,
                    "prefix": prefix,
                    "suffix": suffix,
                },
                "body": body,
                "format": "plain-text",
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )

    normalized_notes.sort(key=lambda note: (note["createdAt"], note["id"]))
    return {"schemaVersion": 1, "bookId": "qfg", "chapterId": chapter_id, "notes": normalized_notes}


def serialize_note_document(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def content_revision(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def etag_for(content: bytes) -> str:
    return f'"{content_revision(content)}"'


def write_notes_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class ReaderHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        dist_root: Path,
        note_paths: dict[str, Path],
        discussion_root: Path,
        chapter_paths: dict[str, Path],
        footnote_paths: dict[str, Path],
        sources_root: Path,
        openai_client: Any,
        write_token: str | None = None,
    ) -> None:
        handler = partial(ReaderRequestHandler, directory=str(dist_root.resolve()))
        super().__init__(server_address, handler)
        self.dist_root = dist_root.resolve()
        self.note_paths = {chapter: path.resolve() for chapter, path in note_paths.items()}
        self.discussion_root = discussion_root.resolve()
        self.chapter_paths = {chapter: path.resolve() for chapter, path in chapter_paths.items()}
        self.footnote_paths = {chapter: path.resolve() for chapter, path in footnote_paths.items()}
        self.openai_client = openai_client
        self.local_library = local_library.LocalLibrary(sources_root)
        self.local_library.ensure()
        client_builder = getattr(openai_client, "context_builder", None)
        base_builder = client_builder or discussions.ContextBuilder()
        self.context_builder = discussions.ContextBuilder(
            metadata_path=base_builder.metadata_path,
            translation_index_path=base_builder.translation_index_path,
            chapter_paths=self.chapter_paths,
            footnote_paths=self.footnote_paths,
            local_library=self.local_library,
        )
        if client_builder is not None:
            openai_client.context_builder = self.context_builder
        self.write_token = write_token or secrets.token_urlsafe(32)
        self.notes_lock = threading.Lock()
        self.discussions_lock = threading.Lock()
        self.active_discussions: set[str] = set()
        self.context_builds_lock = threading.Lock()
        self.context_builds: dict[str, dict[str, Any]] = {}
        self.library_previews_lock = threading.Lock()
        self.library_previews: dict[str, dict[str, Any]] = {}
        port = self.server_address[1]
        self.allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}


class ReaderRequestHandler(SimpleHTTPRequestHandler):
    server: ReaderHTTPServer

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def send_json(self, status: int, value: Any, *, etag: str | None = None) -> None:
        content = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        if etag is not None:
            self.send_header("ETag", etag)
        self.end_headers()
        self.wfile.write(content)

    def send_api_error(self, status: int, code: str, message: str) -> None:
        self.send_json(status, {"error": {"code": code, "message": message}})

    def notes_route(self) -> tuple[str, Path] | None:
        path = urlsplit(self.path).path
        match = NOTES_ROUTE_RE.fullmatch(path)
        if not match:
            return None
        chapter_id = match.group(1)
        note_path = self.server.note_paths.get(chapter_id)
        if note_path is None:
            return None
        return chapter_id, note_path

    def discussion_list_route(self) -> tuple[str, Path] | None:
        path = urlsplit(self.path).path
        match = DISCUSSION_LIST_ROUTE_RE.fullmatch(path)
        if not match:
            return None
        chapter_id = match.group(1)
        chapter_path = self.server.chapter_paths.get(chapter_id)
        if chapter_path is None:
            return None
        return chapter_id, chapter_path

    def discussion_preview_route(self) -> tuple[str, Path] | None:
        path = urlsplit(self.path).path
        match = DISCUSSION_PREVIEW_ROUTE_RE.fullmatch(path)
        if not match:
            return None
        chapter_id = match.group(1)
        chapter_path = self.server.chapter_paths.get(chapter_id)
        if chapter_path is None or chapter_id not in self.server.note_paths:
            return None
        return chapter_id, chapter_path

    def discussion_route(self) -> tuple[str, Path] | None:
        path = urlsplit(self.path).path
        match = DISCUSSION_ROUTE_RE.fullmatch(path)
        if not match:
            return None
        try:
            discussion_path = discussions.find_discussion_path(self.server.discussion_root, match.group(1))
        except discussions.DiscussionValidationError:
            return None
        if discussion_path is None:
            return None
        return match.group(1), discussion_path

    def discussion_messages_route(self) -> tuple[str, Path] | None:
        path = urlsplit(self.path).path
        match = DISCUSSION_MESSAGES_ROUTE_RE.fullmatch(path)
        if not match:
            return None
        try:
            discussion_path = discussions.find_discussion_path(self.server.discussion_root, match.group(1))
        except discussions.DiscussionValidationError:
            return None
        if discussion_path is None:
            return None
        return match.group(1), discussion_path

    def authorize_write(self) -> bool:
        if self.headers.get("Origin") not in self.server.allowed_origins:
            self.send_api_error(403, "origin_rejected", "Request origin is not allowed")
            return False
        if not secrets.compare_digest(self.headers.get("X-QFG-Write-Token", ""), self.server.write_token):
            self.send_api_error(403, "token_rejected", "Write token is invalid")
            return False
        return True

    def read_json_body(self, *, max_bytes: int = MAX_REQUEST_BYTES) -> Any | None:
        if self.headers.get_content_type() != "application/json":
            self.send_api_error(415, "unsupported_media_type", "Content-Type must be application/json")
            return None
        try:
            content_length = int(self.headers.get("Content-Length") or "")
        except ValueError:
            content_length = -1
        if content_length < 0:
            self.send_api_error(411, "length_required", "A valid Content-Length is required")
            return None
        if content_length > max_bytes:
            self.send_api_error(413, "request_too_large", "Request body is too large")
            return None
        try:
            return json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_api_error(422, "invalid_json", "Request body must be valid JSON")
            return None

    def send_stream_headers(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()

    def write_stream_event(self, value: Any) -> None:
        line = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        try:
            self.wfile.write(line)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def chapter_context(self, chapter_id: str) -> tuple[str, str, str]:
        source = self.server.chapter_paths[chapter_id].read_text(encoding="utf-8")
        chapter_markdown, title = discussions.strip_front_matter(source)
        revision = hashlib.sha256(chapter_markdown.encode("utf-8")).hexdigest()
        return chapter_markdown, title, revision

    def note_context(self, chapter_id: str) -> dict[str, Any]:
        path = self.server.note_paths[chapter_id]
        return normalize_note_document(json.loads(path.read_bytes()), chapter_id)

    def context_options(self, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        excluded_note_ids = discussions.normalize_excluded_note_ids(payload.get("excludedNoteIds"))
        included_translation_source_lines = discussions.normalize_translation_source_lines(
            payload.get("includedTranslationSourceLines"), "includedTranslationSourceLines"
        )
        excluded_translation_source_lines = discussions.normalize_translation_source_lines(
            payload.get("excludedTranslationSourceLines"), "excludedTranslationSourceLines"
        )
        excluded_book_passage_ids = discussions.normalize_excluded_book_passage_ids(
            payload.get("excludedBookPassageIds")
        )
        book_passage_limit = discussions.normalize_book_passage_limit(payload.get("bookPassageLimit"))
        included_local_chunk_ids = discussions.normalize_included_local_chunk_ids(
            payload.get("includedLocalChunkIds")
        )
        options = {
            "excluded_note_ids": excluded_note_ids,
            "included_translation_source_lines": included_translation_source_lines,
            "excluded_translation_source_lines": excluded_translation_source_lines,
            "excluded_book_passage_ids": excluded_book_passage_ids,
            "book_passage_limit": book_passage_limit,
            "included_local_chunk_ids": included_local_chunk_ids,
        }
        selections = {
            "excludedNoteIds": sorted(excluded_note_ids),
            "includedTranslationSourceLines": sorted(included_translation_source_lines),
            "excludedTranslationSourceLines": sorted(excluded_translation_source_lines),
            "excludedBookPassageIds": sorted(excluded_book_passage_ids),
            "bookPassageLimit": book_passage_limit,
            "includedLocalChunkIds": sorted(included_local_chunk_ids),
        }
        return options, selections

    def build_context_bundle(
        self, document: dict[str, Any], chapter_markdown: str, note_document: dict[str, Any], options: dict[str, Any]
    ) -> discussions.ContextBundle:
        request = discussions.ContextRequest.from_discussion(
            document,
            chapter_markdown,
            prompt_version=discussions.PROMPT_VERSION,
            note_document=note_document,
            **options,
        )
        return self.server.context_builder.build(request)

    def save_context_build(self, record: dict[str, Any]) -> tuple[str, float]:
        now = time.time()
        build_id = secrets.token_urlsafe(24)
        expires_at = now + CONTEXT_BUILD_TTL_SECONDS
        record = {**record, "expiresAt": expires_at}
        with self.server.context_builds_lock:
            self.server.context_builds = {
                key: value for key, value in self.server.context_builds.items() if value["expiresAt"] > now
            }
            self.server.context_builds[build_id] = record
        return build_id, expires_at

    def get_context_build(self, build_id: Any) -> dict[str, Any]:
        if not isinstance(build_id, str) or not build_id:
            raise discussions.DiscussionValidationError("contextBuildId is required")
        with self.server.context_builds_lock:
            record = self.server.context_builds.get(build_id)
            if record is None or record["expiresAt"] <= time.time():
                self.server.context_builds.pop(build_id, None)
                raise discussions.DiscussionValidationError("context preview expired; preview again")
        return record

    def consume_context_build(self, build_id: str) -> None:
        with self.server.context_builds_lock:
            self.server.context_builds.pop(build_id, None)

    def save_library_preview(self, preview: dict[str, Any]) -> tuple[str, float]:
        now = time.time()
        preview_id = secrets.token_urlsafe(24)
        expires_at = now + CONTEXT_BUILD_TTL_SECONDS
        with self.server.library_previews_lock:
            self.server.library_previews = {
                key: value
                for key, value in self.server.library_previews.items()
                if value["expiresAt"] > now
            }
            self.server.library_previews[preview_id] = {**preview, "expiresAt": expires_at}
        return preview_id, expires_at

    def pop_library_preview(self, preview_id: str) -> dict[str, Any]:
        with self.server.library_previews_lock:
            preview = self.server.library_previews.pop(preview_id, None)
        if preview is None or preview["expiresAt"] <= time.time():
            raise local_library.LocalLibraryError("import preview expired; preview again")
        return preview

    def run_discussion_stream(
        self,
        document: dict[str, Any],
        path: Path,
        chapter_markdown: str,
        *,
        note_document: dict[str, Any],
        excluded_note_ids: frozenset[str] = frozenset(),
        included_translation_source_lines: frozenset[int] = frozenset(),
        excluded_translation_source_lines: frozenset[int] = frozenset(),
        excluded_book_passage_ids: frozenset[str] = frozenset(),
        book_passage_limit: int = 5,
        included_local_chunk_ids: frozenset[str] = frozenset(),
        context_bundle: discussions.ContextBundle | None = None,
    ) -> None:
        discussion_id = document["id"]
        self.send_stream_headers()
        pending_content = discussions.serialize_discussion_document(document)
        self.write_stream_event(
            {
                "type": "response.started",
                "discussion": discussions.discussion_for_client(document),
                "etag": discussions.document_etag(pending_content),
            }
        )
        try:
            completed_event = None
            for event in self.server.openai_client.stream(
                document,
                chapter_markdown,
                note_document=note_document,
                excluded_note_ids=excluded_note_ids,
                included_translation_source_lines=included_translation_source_lines,
                excluded_translation_source_lines=excluded_translation_source_lines,
                excluded_book_passage_ids=excluded_book_passage_ids,
                book_passage_limit=book_passage_limit,
                included_local_chunk_ids=included_local_chunk_ids,
                context_bundle=context_bundle,
            ):
                if event.get("type") == "response.delta":
                    self.write_stream_event(event)
                elif event.get("type") == "response.completed":
                    completed_event = event
            if completed_event is None:
                raise discussions.OpenAIClientError("stream_interrupted", "OpenAI 回复在完成前中断。", True)
            completed = discussions.complete_pending_message(document, completed_event)
            content = discussions.serialize_discussion_document(completed)
            with self.server.discussions_lock:
                discussions.write_atomically(path, content)
            self.write_stream_event(
                {
                    "type": "response.completed",
                    "discussion": discussions.discussion_for_client(completed),
                    "etag": discussions.document_etag(content),
                }
            )
        except discussions.OpenAIClientError as error:
            failed = discussions.fail_pending_message(document, error)
            content = discussions.serialize_discussion_document(failed)
            with self.server.discussions_lock:
                discussions.write_atomically(path, content)
            self.write_stream_event(
                {
                    "type": "response.error",
                    "discussion": discussions.discussion_for_client(failed),
                    "etag": discussions.document_etag(content),
                    "error": {"code": error.code, "message": error.message, "retryable": error.retryable},
                }
            )
        except Exception:
            error = discussions.OpenAIClientError(
                "local_stream_error", "处理 AI 回复时发生本地错误，可以重试。", True
            )
            try:
                failed = discussions.fail_pending_message(document, error)
                content = discussions.serialize_discussion_document(failed)
                with self.server.discussions_lock:
                    discussions.write_atomically(path, content)
                self.write_stream_event(
                    {
                        "type": "response.error",
                        "discussion": discussions.discussion_for_client(failed),
                        "etag": discussions.document_etag(content),
                        "error": {"code": error.code, "message": error.message, "retryable": True},
                    }
                )
            except (OSError, discussions.DiscussionValidationError):
                self.write_stream_event(
                    {
                        "type": "response.error",
                        "error": {"code": "local_write_failed", "message": "讨论状态无法保存。", "retryable": False},
                    }
                )
        finally:
            with self.server.discussions_lock:
                self.server.active_discussions.discard(discussion_id)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/session":
            self.send_json(
                200,
                {
                    "writeToken": self.server.write_token,
                    "aiConfigured": self.server.openai_client.configured,
                    "model": self.server.openai_client.model,
                },
            )
            return

        if path == "/api/library":
            try:
                self.send_json(200, self.server.local_library.list_sources())
            except local_library.LocalLibraryError as error:
                self.send_api_error(500, "library_unavailable", str(error))
            return

        route = self.notes_route()
        if route is not None:
            chapter_id, note_path = route
            try:
                content = note_path.read_bytes()
                document = normalize_note_document(json.loads(content), chapter_id)
            except FileNotFoundError:
                self.send_api_error(404, "notes_not_found", "Chapter notes file was not found")
                return
            except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
                self.send_api_error(500, "invalid_notes_file", str(error))
                return
            self.send_json(200, document, etag=etag_for(content))
            return

        discussion_list_route = self.discussion_list_route()
        if discussion_list_route is not None:
            chapter_id, _ = discussion_list_route
            try:
                summaries = discussions.list_discussion_summaries(self.server.discussion_root, chapter_id)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError, discussions.DiscussionValidationError) as error:
                self.send_api_error(500, "invalid_discussion_file", str(error))
                return
            self.send_json(200, {"discussions": summaries})
            return

        discussion_route = self.discussion_route()
        if discussion_route is not None:
            _, discussion_path = discussion_route
            try:
                document, content = discussions.load_discussion(discussion_path)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError, discussions.DiscussionValidationError) as error:
                self.send_api_error(500, "invalid_discussion_file", str(error))
                return
            self.send_json(
                200,
                discussions.discussion_for_client(document),
                etag=discussions.document_etag(content),
            )
            return

        if path.startswith("/api/"):
            self.send_api_error(404, "not_found", "API route was not found")
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        library_confirm_match = LIBRARY_IMPORT_CONFIRM_ROUTE_RE.fullmatch(path)
        library_source_match = LIBRARY_SOURCE_ROUTE_RE.fullmatch(path)
        is_library_route = path in {"/api/library/imports/preview", "/api/library/index/rebuild"} or bool(
            library_confirm_match or library_source_match
        )
        if is_library_route:
            if not self.authorize_write():
                return
            payload = self.read_json_body(max_bytes=MAX_LIBRARY_REQUEST_BYTES)
            if payload is None:
                return
            try:
                if path == "/api/library/imports/preview":
                    if not isinstance(payload, dict) or set(payload) != {"filename", "contentBase64", "metadata"}:
                        raise local_library.LocalLibraryError("import preview request has invalid fields")
                    if not isinstance(payload["contentBase64"], str):
                        raise local_library.LocalLibraryError("contentBase64 must be a string")
                    try:
                        content = base64.b64decode(payload["contentBase64"], validate=True)
                    except (binascii.Error, ValueError) as error:
                        raise local_library.LocalLibraryError("contentBase64 is invalid") from error
                    preview = self.server.local_library.preview_import(
                        payload["filename"], content, payload["metadata"]
                    )
                    preview_id, expires_at = self.save_library_preview(preview)
                    public_preview = {key: value for key, value in preview.items() if key not in {"content", "chunks"}}
                    self.send_json(200, {
                        "previewId": preview_id,
                        "expiresAt": datetime.fromtimestamp(expires_at).astimezone().isoformat(),
                        **public_preview,
                    })
                    return
                if library_confirm_match:
                    if payload != {"confirm": True}:
                        raise local_library.LocalLibraryError("confirm must be true")
                    preview = self.pop_library_preview(library_confirm_match.group(1))
                    source = self.server.local_library.confirm_import(preview)
                    self.send_json(201, {"source": source})
                    return
                if path == "/api/library/index/rebuild":
                    if payload != {"confirm": True}:
                        raise local_library.LocalLibraryError("confirm must be true")
                    self.send_json(200, self.server.local_library.rebuild_index())
                    return
                if library_source_match:
                    source = self.server.local_library.update_source(library_source_match.group(1), payload)
                    self.send_json(200, {"source": source})
                    return
            except local_library.LocalLibraryError as error:
                self.send_api_error(422, "invalid_library_request", str(error))
                return
            except OSError:
                self.send_api_error(500, "library_write_failed", "Local library could not be updated")
                return

        create_route = self.discussion_list_route()
        preview_route = self.discussion_preview_route()
        continue_route = self.discussion_messages_route()
        if create_route is None and preview_route is None and continue_route is None:
            self.send_api_error(404, "not_found", "API route was not found")
            return
        if not self.authorize_write():
            return
        if not self.server.openai_client.configured:
            self.send_api_error(503, "api_not_configured", "尚未配置 OpenAI API Key。")
            return
        payload = self.read_json_body()
        if payload is None:
            return

        if preview_route is not None:
            chapter_id, _ = preview_route
            try:
                if not isinstance(payload, dict):
                    raise discussions.DiscussionValidationError("request must be an object")
                required = {"sourceRevision", "anchor", "scriptures", "footnotes", "message"}
                allowed = required | {
                    "excludedNoteIds",
                    "includedTranslationSourceLines",
                    "excludedTranslationSourceLines",
                    "excludedBookPassageIds",
                    "bookPassageLimit",
                    "includedLocalChunkIds",
                    "discussionId",
                    "discussionEtag",
                }
                if not set(payload) <= allowed or not required <= set(payload):
                    raise discussions.DiscussionValidationError("preview request has invalid fields")
                options, selections = self.context_options(payload)
                chapter_markdown, chapter_title, current_revision = self.chapter_context(chapter_id)
                if payload["sourceRevision"] != current_revision:
                    self.send_api_error(409, "chapter_source_changed", "章节内容已变更，请刷新页面后重试。")
                    return
                discussion_id = payload.get("discussionId")
                expected_etag = payload.get("discussionEtag")
                if discussion_id is None:
                    if expected_etag is not None:
                        raise discussions.DiscussionValidationError("discussionEtag requires discussionId")
                    document = discussions.create_discussion_document(
                        {key: value for key, value in payload.items() if key in required},
                        chapter_id,
                        chapter_title,
                    )
                    kind = "create"
                else:
                    if not isinstance(expected_etag, str):
                        raise discussions.DiscussionValidationError("discussionEtag is required for a reply preview")
                    discussion_path = discussions.find_discussion_path(self.server.discussion_root, discussion_id)
                    if discussion_path is None:
                        raise discussions.DiscussionValidationError("discussion was not found")
                    existing, content = discussions.load_discussion(discussion_path, chapter_id)
                    if discussions.document_etag(content) != expected_etag:
                        self.send_api_error(409, "revision_conflict", "Discussion changed on disk")
                        return
                    if existing["sourceRevision"] != payload["sourceRevision"]:
                        raise discussions.DiscussionValidationError("discussion source revision does not match preview")
                    if discussions.normalize_anchor(payload["anchor"]) != existing["anchor"]:
                        raise discussions.DiscussionValidationError("reply preview anchor does not match discussion")
                    supplied_context = discussions.normalize_context(
                        {
                            "chapterTitle": existing["context"]["chapterTitle"],
                            "scriptures": payload["scriptures"],
                            "footnotes": payload["footnotes"],
                        }
                    )
                    if supplied_context != existing["context"]:
                        raise discussions.DiscussionValidationError("reply preview snapshots do not match discussion")
                    document = discussions.append_discussion_turn(existing, payload["message"])
                    kind = "continue"
                note_document = self.note_context(chapter_id)
                bundle = self.build_context_bundle(document, chapter_markdown, note_document, options)
                budget = discussions.estimate_request_budget(
                    document,
                    bundle,
                    max_output_tokens=getattr(
                        self.server.openai_client, "max_output_tokens", discussions.DEFAULT_MAX_OUTPUT_TOKENS
                    ),
                    context_window_tokens=getattr(
                        self.server.openai_client,
                        "context_window_tokens",
                        discussions.DEFAULT_CONTEXT_WINDOW_TOKENS,
                    ),
                )
                build_id, expires_at = self.save_context_build(
                    {
                        "kind": kind,
                        "chapterId": chapter_id,
                        "discussionId": discussion_id,
                        "expectedEtag": expected_etag,
                        "message": payload["message"],
                        "document": document,
                        "options": options,
                        "selections": selections,
                        "bundleHash": discussions.bundle_hash(bundle),
                    }
                )
            except (discussions.DiscussionValidationError, discussions.ContextBuildError, ValidationError) as error:
                self.send_api_error(422, "invalid_context_preview", str(error))
                return
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                self.send_api_error(500, "context_preview_unavailable", "无法读取本轮上下文。")
                return
            self.send_json(
                200,
                {
                    "contextBuildId": build_id,
                    "expiresAt": datetime.fromtimestamp(expires_at).astimezone().isoformat(),
                    "preview": bundle.preview,
                    "estimates": budget,
                },
            )
            return

        if create_route is not None:
            chapter_id, _ = create_route
            try:
                chapter_markdown, chapter_title, current_revision = self.chapter_context(chapter_id)
                create_required = {
                    "sourceRevision", "anchor", "scriptures", "footnotes", "message", "contextBuildId"
                }
                create_allowed = create_required | {
                    "excludedNoteIds",
                    "includedTranslationSourceLines",
                    "excludedTranslationSourceLines",
                    "excludedBookPassageIds",
                    "bookPassageLimit",
                    "includedLocalChunkIds",
                }
                if not isinstance(payload, dict) or payload.get("sourceRevision") != current_revision:
                    self.send_api_error(409, "chapter_source_changed", "章节内容已变更，请刷新页面后重试。")
                    return
                if not create_required <= set(payload) or not set(payload) <= create_allowed:
                    raise discussions.DiscussionValidationError("create request has invalid fields")
                record = self.get_context_build(payload.get("contextBuildId"))
                options, selections = self.context_options(payload)
                if (
                    record["kind"] != "create"
                    or record["chapterId"] != chapter_id
                    or record["message"] != payload.get("message")
                    or record["selections"] != selections
                ):
                    raise discussions.DiscussionValidationError("context preview does not match this request")
                document = record["document"]
                if discussions.normalize_anchor(payload["anchor"]) != document["anchor"]:
                    raise discussions.DiscussionValidationError("context preview anchor does not match request")
                supplied_context = discussions.normalize_context(
                    {
                        "chapterTitle": chapter_title,
                        "scriptures": payload["scriptures"],
                        "footnotes": payload["footnotes"],
                    }
                )
                if supplied_context != document["context"]:
                    raise discussions.DiscussionValidationError("context preview snapshots do not match request")
                note_document = self.note_context(chapter_id)
                bundle = self.build_context_bundle(document, chapter_markdown, note_document, options)
                if discussions.bundle_hash(bundle) != record["bundleHash"]:
                    self.send_api_error(409, "context_changed", "上下文来源已变更，请重新预览。")
                    return
                budget = discussions.estimate_request_budget(
                    document,
                    bundle,
                    max_output_tokens=getattr(
                        self.server.openai_client, "max_output_tokens", discussions.DEFAULT_MAX_OUTPUT_TOKENS
                    ),
                    context_window_tokens=getattr(
                        self.server.openai_client,
                        "context_window_tokens",
                        discussions.DEFAULT_CONTEXT_WINDOW_TOKENS,
                    ),
                )
                if budget["status"] == "over_budget":
                    self.send_api_error(422, "context_over_budget", "上下文超过预算，请排除可选证据后重新预览。")
                    return
                document = discussions.attach_context_bundle(document, bundle, selections)
                discussion_path = discussions.discussion_path(
                    self.server.discussion_root, chapter_id, document["id"]
                )
                content = discussions.serialize_discussion_document(document)
                with self.server.discussions_lock:
                    if discussion_path.exists():
                        self.send_api_error(409, "discussion_exists", "Discussion already exists")
                        return
                    discussions.write_atomically(discussion_path, content)
                    self.server.active_discussions.add(document["id"])
                self.consume_context_build(payload["contextBuildId"])
            except discussions.DiscussionValidationError as error:
                self.send_api_error(422, "invalid_discussion", str(error))
                return
            except (ValidationError, json.JSONDecodeError, UnicodeDecodeError):
                self.send_api_error(500, "invalid_notes_file", "当前章节笔记无法读取。")
                return
            except OSError:
                self.send_api_error(500, "write_failed", "Discussion could not be saved")
                return
            self.run_discussion_stream(
                document,
                discussion_path,
                chapter_markdown,
                note_document=note_document,
                **options,
                context_bundle=bundle,
            )
            return

        discussion_id, discussion_path = continue_route
        expected_revision = self.headers.get("If-Match")
        if expected_revision is None:
            self.send_api_error(428, "revision_required", "If-Match is required")
            return
        try:
            optional_context_fields = {
                "excludedNoteIds",
                "includedTranslationSourceLines",
                "excludedTranslationSourceLines",
                "excludedBookPassageIds",
                "bookPassageLimit",
                "includedLocalChunkIds",
            }
            valid_message_request = (
                isinstance(payload, dict)
                and "message" in payload
                and set(payload) <= {"message", "contextBuildId"} | optional_context_fields
                and "contextBuildId" in payload
            )
            if not isinstance(payload, dict) or not (valid_message_request or set(payload) == {"retry"}):
                raise discussions.DiscussionValidationError("request must contain message or retry")
            with self.server.discussions_lock:
                if discussion_id in self.server.active_discussions:
                    self.send_api_error(409, "discussion_busy", "Discussion already has a response in progress")
                    return
                document, current_content = discussions.load_discussion(discussion_path)
                if expected_revision != discussions.document_etag(current_content):
                    self.send_api_error(409, "revision_conflict", "Discussion changed on disk")
                    return
                if "retry" in payload:
                    if payload["retry"] is not True:
                        raise discussions.DiscussionValidationError("retry must be true")
                    pending = discussions.retry_failed_turn(document)
                    turn = pending["turns"][-1]
                    if turn["legacyContext"] or turn["contextSnapshot"] is None:
                        raise discussions.DiscussionValidationError(
                            "legacy failed turns cannot be retried without inventing historical context"
                        )
                    options, selections = self.context_options(turn["contextSnapshot"]["selections"])
                else:
                    record = self.get_context_build(payload.get("contextBuildId"))
                    options, selections = self.context_options(payload)
                    if (
                        record["kind"] != "continue"
                        or record["discussionId"] != discussion_id
                        or record["expectedEtag"] != expected_revision
                        or record["message"] != payload["message"]
                        or record["selections"] != selections
                    ):
                        raise discussions.DiscussionValidationError("context preview does not match this reply")
                    pending = record["document"]
                chapter_markdown, _, _ = self.chapter_context(document["chapterId"])
                note_document = self.note_context(document["chapterId"])
                bundle = self.build_context_bundle(pending, chapter_markdown, note_document, options)
                expected_bundle_hash = (
                    turn["contextSnapshot"]["bundleHash"] if "retry" in payload else record["bundleHash"]
                )
                if discussions.bundle_hash(bundle) != expected_bundle_hash:
                    self.send_api_error(409, "context_changed", "上下文来源已变更，无法复用已冻结的上下文。")
                    return
                budget = discussions.estimate_request_budget(
                    pending,
                    bundle,
                    max_output_tokens=getattr(
                        self.server.openai_client, "max_output_tokens", discussions.DEFAULT_MAX_OUTPUT_TOKENS
                    ),
                    context_window_tokens=getattr(
                        self.server.openai_client,
                        "context_window_tokens",
                        discussions.DEFAULT_CONTEXT_WINDOW_TOKENS,
                    ),
                )
                if budget["status"] == "over_budget":
                    self.send_api_error(422, "context_over_budget", "上下文超过预算，请减少可选证据或新建讨论。")
                    return
                if "retry" not in payload:
                    pending = discussions.attach_context_bundle(pending, bundle, selections)
                pending_content = discussions.serialize_discussion_document(pending)
                discussions.write_atomically(discussion_path, pending_content)
                self.server.active_discussions.add(discussion_id)
                if "retry" not in payload:
                    self.consume_context_build(payload["contextBuildId"])
        except (discussions.DiscussionValidationError, discussions.ContextBuildError) as error:
            self.send_api_error(422, "invalid_discussion", str(error))
            return
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValidationError):
            self.send_api_error(500, "discussion_unavailable", "Discussion could not be loaded or saved")
            return
        self.run_discussion_stream(
            pending,
            discussion_path,
            chapter_markdown,
            note_document=note_document,
            **options,
            context_bundle=bundle,
        )

    def do_DELETE(self) -> None:
        path = urlsplit(self.path).path
        library_match = LIBRARY_DERIVED_ROUTE_RE.fullmatch(path)
        if library_match is not None:
            if not self.authorize_write():
                return
            try:
                removed = self.server.local_library.remove_derived_index(library_match.group(1))
            except local_library.LocalLibraryError as error:
                self.send_api_error(422, "invalid_library_request", str(error))
                return
            except OSError:
                self.send_api_error(500, "library_write_failed", "Derived index could not be removed")
                return
            self.send_json(200, {"removedChunks": removed, "originalPreserved": True})
            return
        route = self.discussion_route()
        if route is None:
            self.send_api_error(404, "not_found", "API route was not found")
            return
        if not self.authorize_write():
            return
        expected_revision = self.headers.get("If-Match")
        if expected_revision is None:
            self.send_api_error(428, "revision_required", "If-Match is required")
            return
        discussion_id, discussion_path = route
        try:
            with self.server.discussions_lock:
                if discussion_id in self.server.active_discussions:
                    self.send_api_error(409, "discussion_busy", "Discussion has a response in progress")
                    return
                _, content = discussions.load_discussion(discussion_path)
                if expected_revision != discussions.document_etag(content):
                    self.send_api_error(409, "revision_conflict", "Discussion changed on disk")
                    return
                discussion_path.unlink()
        except FileNotFoundError:
            self.send_api_error(404, "not_found", "Discussion was not found")
            return
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, discussions.DiscussionValidationError):
            self.send_api_error(500, "delete_failed", "Discussion could not be deleted")
            return
        self.send_json(200, {"deleted": discussion_id})

    def do_PUT(self) -> None:
        route = self.notes_route()
        if route is None:
            self.send_api_error(404, "not_found", "API route was not found")
            return

        if self.headers.get("Origin") not in self.server.allowed_origins:
            self.send_api_error(403, "origin_rejected", "Request origin is not allowed")
            return
        if not secrets.compare_digest(self.headers.get("X-QFG-Write-Token", ""), self.server.write_token):
            self.send_api_error(403, "token_rejected", "Write token is invalid")
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self.send_api_error(415, "unsupported_media_type", "Content-Type must be application/json")
            return

        content_length_header = self.headers.get("Content-Length")
        try:
            content_length = int(content_length_header or "")
        except ValueError:
            content_length = -1
        if content_length < 0:
            self.send_api_error(411, "length_required", "A valid Content-Length is required")
            return
        if content_length > MAX_REQUEST_BYTES:
            self.send_api_error(413, "request_too_large", "Request body is too large")
            return

        chapter_id, note_path = route
        try:
            incoming = json.loads(self.rfile.read(content_length))
            normalized_document = normalize_note_document(incoming, chapter_id)
            normalized_content = serialize_note_document(normalized_document)
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            self.send_api_error(422, "invalid_document", str(error))
            return

        expected_revision = self.headers.get("If-Match")
        if expected_revision is None:
            self.send_api_error(428, "revision_required", "If-Match is required")
            return

        with self.server.notes_lock:
            try:
                current_content = note_path.read_bytes()
            except FileNotFoundError:
                self.send_api_error(404, "notes_not_found", "Chapter notes file was not found")
                return
            current_etag = etag_for(current_content)
            if expected_revision != current_etag:
                self.send_api_error(409, "revision_conflict", "Chapter notes changed on disk")
                return
            try:
                if normalized_content != current_content:
                    write_notes_atomically(note_path, normalized_content)
            except OSError:
                self.send_api_error(500, "write_failed", "Chapter notes could not be saved")
                return

        self.send_json(200, normalized_document, etag=etag_for(normalized_content))


def build_server(
    port: int,
    *,
    dist_root: Path = DIST_ROOT,
    note_paths: dict[str, Path] | None = None,
    discussion_root: Path = DISCUSSIONS_ROOT,
    chapter_paths: dict[str, Path] | None = None,
    footnote_paths: dict[str, Path] | None = None,
    sources_root: Path | None = None,
    openai_client: Any | None = None,
    write_token: str | None = None,
) -> ReaderHTTPServer:
    resolved_chapter_paths = chapter_paths or DEFAULT_CHAPTER_PATHS
    resolved_footnote_paths = (
        footnote_paths
        if footnote_paths is not None
        else DEFAULT_FOOTNOTE_PATHS if chapter_paths is None else {}
    )
    return ReaderHTTPServer(
        ("127.0.0.1", port),
        dist_root=dist_root,
        note_paths=note_paths or DEFAULT_NOTE_PATHS,
        discussion_root=discussion_root,
        chapter_paths=resolved_chapter_paths,
        footnote_paths=resolved_footnote_paths,
        sources_root=(
            sources_root
            if sources_root is not None
            else SOURCES_ROOT if discussion_root == DISCUSSIONS_ROOT
            else discussion_root.parent.parent / "Sources"
        ),
        openai_client=openai_client or discussions.client_from_environment(),
        write_token=write_token,
    )


def inject_api_key_from_macos_internet_password(label: str) -> None:
    normalized_label = label.strip()
    if not normalized_label:
        raise SystemExit("Keychain internet-password label cannot be empty.")
    security_path = Path("/usr/bin/security")
    if not security_path.is_file():
        raise SystemExit("The macOS security command is unavailable on this system.")

    lookup_variants = (("-l", normalized_label), ("-s", normalized_label))
    for selector, value in lookup_variants:
        try:
            result = subprocess.run(
                [str(security_path), "find-internet-password", "-w", selector, value],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as error:
            raise SystemExit("Unable to open the macOS password store.") from error
        api_key = result.stdout.strip()
        if result.returncode == 0 and api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            return
    raise SystemExit(
        f'Could not read a website password named "{normalized_label}". '
        "Confirm its visible name in the Passwords app and allow Keychain access when prompted."
    )


def inject_api_key_from_macos_generic_password(service: str) -> None:
    normalized_service = service.strip()
    if not normalized_service:
        raise SystemExit("Keychain generic-password service cannot be empty.")
    security_path = Path("/usr/bin/security")
    if not security_path.is_file():
        raise SystemExit("The macOS security command is unavailable on this system.")
    try:
        result = subprocess.run(
            [str(security_path), "find-generic-password", "-w", "-s", normalized_service],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise SystemExit("Unable to open the macOS password store.") from error
    api_key = result.stdout.strip()
    if result.returncode != 0 or not api_key:
        raise SystemExit(
            f'Could not read a generic password with service "{normalized_service}". '
            "Confirm that the Keychain item exists and allow access when prompted."
        )
    os.environ["OPENAI_API_KEY"] = api_key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    keychain_group = parser.add_mutually_exclusive_group()
    keychain_group.add_argument(
        "--keychain-internet-password-label",
        metavar="LABEL",
        help="Read OPENAI_API_KEY from a macOS website-password item without printing it.",
    )
    keychain_group.add_argument(
        "--keychain-generic-password-service",
        metavar="SERVICE",
        help="Read OPENAI_API_KEY from a macOS generic-password item without printing it.",
    )
    args = parser.parse_args()

    if args.keychain_internet_password_label:
        inject_api_key_from_macos_internet_password(args.keychain_internet_password_label)
    elif args.keychain_generic_password_service:
        inject_api_key_from_macos_generic_password(args.keychain_generic_password_service)

    chapter_pages = [DIST_ROOT / f"chapters/{chapter:02d}/index.html" for chapter in range(1, 21)]
    if any(not chapter.is_file() for chapter in chapter_pages):
        raise SystemExit("Build output is missing. Run Web/scripts/build.py first.")
    for chapter_id, note_path in DEFAULT_NOTE_PATHS.items():
        if not note_path.is_file():
            raise SystemExit(f"Notes file for chapter {chapter_id} is missing: {note_path}")

    server = build_server(args.port)
    print(f"Reader available at http://127.0.0.1:{server.server_address[1]}/chapters/01/")
    if server.openai_client.configured:
        print(f"AI discussion enabled with model {server.openai_client.model}.")
    else:
        print("AI discussion disabled: OPENAI_API_KEY is not set.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
