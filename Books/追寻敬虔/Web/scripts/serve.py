#!/usr/bin/env python3
"""Serve the generated reader and its repository-backed notes API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
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


WEB_ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = WEB_ROOT.parent
DIST_ROOT = WEB_ROOT / "dist"
NOTES_ROOT = BOOK_ROOT / "Notes/Annotations"
DISCUSSIONS_ROOT = BOOK_ROOT / "Notes/Discussions"
READING_ROOT = BOOK_ROOT / "Reading"
DEFAULT_NOTE_PATHS = {f"{chapter:02d}": NOTES_ROOT / f"{chapter:02d}.json" for chapter in range(1, 21)}
DEFAULT_CHAPTER_PATHS = discussions.discover_chapter_paths(READING_ROOT)

MAX_REQUEST_BYTES = 1_000_000
NOTES_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/notes\Z")
DISCUSSION_LIST_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/discussions\Z")
DISCUSSION_PREVIEW_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/discussions/context-preview\Z")
DISCUSSION_ROUTE_RE = re.compile(r"\A/api/discussions/([^/]+)\Z")
DISCUSSION_MESSAGES_ROUTE_RE = re.compile(r"\A/api/discussions/([^/]+)/messages\Z")
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
        openai_client: Any,
        write_token: str | None = None,
    ) -> None:
        handler = partial(ReaderRequestHandler, directory=str(dist_root.resolve()))
        super().__init__(server_address, handler)
        self.dist_root = dist_root.resolve()
        self.note_paths = {chapter: path.resolve() for chapter, path in note_paths.items()}
        self.discussion_root = discussion_root.resolve()
        self.chapter_paths = {chapter: path.resolve() for chapter, path in chapter_paths.items()}
        self.openai_client = openai_client
        self.write_token = write_token or secrets.token_urlsafe(32)
        self.notes_lock = threading.Lock()
        self.discussions_lock = threading.Lock()
        self.active_discussions: set[str] = set()
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

    def read_json_body(self) -> Any | None:
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
        if content_length > MAX_REQUEST_BYTES:
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
                }
                if not set(payload) <= allowed or not required <= set(payload):
                    raise discussions.DiscussionValidationError("preview request has invalid fields")
                excluded_note_ids = discussions.normalize_excluded_note_ids(payload.get("excludedNoteIds"))
                included_translation_source_lines = discussions.normalize_translation_source_lines(
                    payload.get("includedTranslationSourceLines"), "includedTranslationSourceLines"
                )
                excluded_translation_source_lines = discussions.normalize_translation_source_lines(
                    payload.get("excludedTranslationSourceLines"), "excludedTranslationSourceLines"
                )
                document = discussions.create_discussion_document(
                    {key: value for key, value in payload.items() if key in required},
                    chapter_id,
                    self.chapter_context(chapter_id)[1],
                )
                chapter_markdown, _, current_revision = self.chapter_context(chapter_id)
                if payload["sourceRevision"] != current_revision:
                    self.send_api_error(409, "chapter_source_changed", "章节内容已变更，请刷新页面后重试。")
                    return
                note_document = self.note_context(chapter_id)
                builder = getattr(self.server.openai_client, "context_builder", None) or discussions.ContextBuilder()
                request = discussions.ContextRequest.from_discussion(
                    document,
                    chapter_markdown,
                    prompt_version=discussions.PROMPT_VERSION,
                    note_document=note_document,
                    excluded_note_ids=excluded_note_ids,
                    included_translation_source_lines=included_translation_source_lines,
                    excluded_translation_source_lines=excluded_translation_source_lines,
                )
                bundle = builder.build(request)
            except (discussions.DiscussionValidationError, discussions.ContextBuildError, ValidationError) as error:
                self.send_api_error(422, "invalid_context_preview", str(error))
                return
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                self.send_api_error(500, "context_preview_unavailable", "无法读取本轮上下文。")
                return
            self.send_json(200, {"preview": bundle.preview, "estimates": bundle.estimates})
            return

        if create_route is not None:
            chapter_id, _ = create_route
            try:
                chapter_markdown, chapter_title, current_revision = self.chapter_context(chapter_id)
                if not isinstance(payload, dict) or payload.get("sourceRevision") != current_revision:
                    self.send_api_error(409, "chapter_source_changed", "章节内容已变更，请刷新页面后重试。")
                    return
                excluded_note_ids = discussions.normalize_excluded_note_ids(payload.get("excludedNoteIds"))
                included_translation_source_lines = discussions.normalize_translation_source_lines(
                    payload.get("includedTranslationSourceLines"), "includedTranslationSourceLines"
                )
                excluded_translation_source_lines = discussions.normalize_translation_source_lines(
                    payload.get("excludedTranslationSourceLines"), "excludedTranslationSourceLines"
                )
                document = discussions.create_discussion_document(
                    {
                        key: value
                        for key, value in payload.items()
                        if key
                        not in {
                            "excludedNoteIds",
                            "includedTranslationSourceLines",
                            "excludedTranslationSourceLines",
                        }
                    },
                    chapter_id,
                    chapter_title,
                )
                note_document = self.note_context(chapter_id)
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
                excluded_note_ids=excluded_note_ids,
                included_translation_source_lines=included_translation_source_lines,
                excluded_translation_source_lines=excluded_translation_source_lines,
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
            }
            valid_message_request = (
                isinstance(payload, dict)
                and "message" in payload
                and set(payload) <= {"message"} | optional_context_fields
            )
            if not isinstance(payload, dict) or not (valid_message_request or set(payload) == {"retry"}):
                raise discussions.DiscussionValidationError("request must contain message or retry")
            excluded_note_ids = discussions.normalize_excluded_note_ids(payload.get("excludedNoteIds"))
            included_translation_source_lines = discussions.normalize_translation_source_lines(
                payload.get("includedTranslationSourceLines"), "includedTranslationSourceLines"
            )
            excluded_translation_source_lines = discussions.normalize_translation_source_lines(
                payload.get("excludedTranslationSourceLines"), "excludedTranslationSourceLines"
            )
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
                else:
                    pending = discussions.append_discussion_turn(document, payload["message"])
                chapter_markdown, _, _ = self.chapter_context(document["chapterId"])
                note_document = self.note_context(document["chapterId"])
                pending_content = discussions.serialize_discussion_document(pending)
                discussions.write_atomically(discussion_path, pending_content)
                self.server.active_discussions.add(discussion_id)
        except discussions.DiscussionValidationError as error:
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
            excluded_note_ids=excluded_note_ids,
            included_translation_source_lines=included_translation_source_lines,
            excluded_translation_source_lines=excluded_translation_source_lines,
        )

    def do_DELETE(self) -> None:
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
    openai_client: Any | None = None,
    write_token: str | None = None,
) -> ReaderHTTPServer:
    return ReaderHTTPServer(
        ("127.0.0.1", port),
        dist_root=dist_root,
        note_paths=note_paths or DEFAULT_NOTE_PATHS,
        discussion_root=discussion_root,
        chapter_paths=chapter_paths or DEFAULT_CHAPTER_PATHS,
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
