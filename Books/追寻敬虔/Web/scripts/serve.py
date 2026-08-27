#!/usr/bin/env python3
"""Serve the generated reader and its repository-backed notes API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID


WEB_ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = WEB_ROOT.parent
DIST_ROOT = WEB_ROOT / "dist"
NOTES_ROOT = BOOK_ROOT / "Notes/Annotations"
DEFAULT_NOTE_PATHS = {"05": NOTES_ROOT / "05.json"}

MAX_REQUEST_BYTES = 1_000_000
NOTES_ROUTE_RE = re.compile(r"\A/api/chapters/([^/]+)/notes\Z")
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
        write_token: str | None = None,
    ) -> None:
        handler = partial(ReaderRequestHandler, directory=str(dist_root.resolve()))
        super().__init__(server_address, handler)
        self.dist_root = dist_root.resolve()
        self.note_paths = {chapter: path.resolve() for chapter, path in note_paths.items()}
        self.write_token = write_token or secrets.token_urlsafe(32)
        self.notes_lock = threading.Lock()
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

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/session":
            self.send_json(200, {"writeToken": self.server.write_token})
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

        if path.startswith("/api/"):
            self.send_api_error(404, "not_found", "API route was not found")
            return
        super().do_GET()

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
    write_token: str | None = None,
) -> ReaderHTTPServer:
    return ReaderHTTPServer(
        ("127.0.0.1", port),
        dist_root=dist_root,
        note_paths=note_paths or DEFAULT_NOTE_PATHS,
        write_token=write_token,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()

    chapter = DIST_ROOT / "chapters/05/index.html"
    if not chapter.is_file():
        raise SystemExit("Build output is missing. Run Web/scripts/build.py first.")
    for chapter_id, note_path in DEFAULT_NOTE_PATHS.items():
        if not note_path.is_file():
            raise SystemExit(f"Notes file for chapter {chapter_id} is missing: {note_path}")

    server = build_server(args.port)
    print(f"Reader available at http://127.0.0.1:{server.server_address[1]}/chapters/05/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
