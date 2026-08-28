from __future__ import annotations

import http.client
import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch


WEB_ROOT = Path(__file__).resolve().parents[1]
SERVE_PATH = WEB_ROOT / "scripts/serve.py"


def load_serve_module():
    spec = importlib.util.spec_from_file_location("qfg_reader_serve", SERVE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load server script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SERVE = load_serve_module()


def sample_document(body: str = "测试笔记") -> dict:
    return {
        "schemaVersion": 1,
        "bookId": "qfg",
        "chapterId": "05",
        "notes": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "sourceRevision": "a" * 64,
                "anchor": {
                    "blockId": "05-p-0001",
                    "startOffset": 2,
                    "endOffset": 6,
                    "exact": "测试文字",
                    "prefix": "之前",
                    "suffix": "之后",
                },
                "body": body,
                "format": "plain-text",
                "createdAt": "2026-08-27T08:00:00.000Z",
                "updatedAt": "2026-08-27T08:00:00.000Z",
            }
        ],
    }


class NotesAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.dist = root / "dist"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<!doctype html><title>test</title>\n", encoding="utf-8")
        self.note_path = root / "Notes/Annotations/05.json"
        self.note_path.parent.mkdir(parents=True)
        self.note_path.write_bytes(SERVE.serialize_note_document(SERVE.empty_note_document("05")))

        self.server = SERVE.build_server(
            0,
            dist_root=self.dist,
            note_paths={"05": self.note_path},
            write_token="test-write-token",
        )
        self.port = self.server.server_address[1]
        self.origin = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, method: str, path: str, body: bytes | None = None, headers: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        content = response.read()
        result = response.status, dict(response.getheaders()), content
        connection.close()
        return result

    def get_notes(self):
        status, headers, content = self.request("GET", "/api/chapters/05/notes")
        self.assertEqual(status, 200)
        return headers["ETag"], json.loads(content)

    def put_notes(self, document: dict, etag: str, **header_overrides):
        body = json.dumps(document, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "Origin": self.origin,
            "X-QFG-Write-Token": "test-write-token",
            "If-Match": etag,
        }
        headers.update(header_overrides)
        return self.request("PUT", "/api/chapters/05/notes", body, headers)

    def test_session_and_empty_notes_are_readable(self) -> None:
        status, _, content = self.request("GET", "/api/session")
        self.assertEqual(status, 200)
        session = json.loads(content)
        self.assertEqual(session["writeToken"], "test-write-token")
        self.assertFalse(session["aiConfigured"])
        self.assertIsInstance(session["model"], str)
        _, document = self.get_notes()
        self.assertEqual(document, SERVE.empty_note_document("05"))

    def test_valid_write_is_atomic_and_git_readable(self) -> None:
        etag, _ = self.get_notes()
        status, response_headers, content = self.put_notes(sample_document(), etag)
        self.assertEqual(status, 200)
        self.assertIn("ETag", response_headers)
        self.assertEqual(json.loads(content), sample_document())
        disk_text = self.note_path.read_text(encoding="utf-8")
        self.assertTrue(disk_text.endswith("\n"))
        self.assertIn('\n  "notes": [\n', disk_text)
        self.assertEqual(json.loads(disk_text), sample_document())

    def test_stale_revision_cannot_overwrite_disk(self) -> None:
        etag, _ = self.get_notes()
        status, _, _ = self.put_notes(sample_document(), etag)
        self.assertEqual(status, 200)
        saved = self.note_path.read_bytes()
        status, _, content = self.put_notes(sample_document("过期写入"), etag)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(content)["error"]["code"], "revision_conflict")
        self.assertEqual(self.note_path.read_bytes(), saved)

    def test_rejects_wrong_origin_token_and_schema(self) -> None:
        etag, _ = self.get_notes()
        status, _, _ = self.put_notes(sample_document(), etag, Origin="https://example.com")
        self.assertEqual(status, 403)
        status, _, _ = self.put_notes(sample_document(), etag, **{"X-QFG-Write-Token": "wrong"})
        self.assertEqual(status, 403)
        invalid = sample_document()
        invalid["chapterId"] = "06"
        status, _, content = self.put_notes(invalid, etag)
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(content)["error"]["code"], "invalid_document")

    def test_rejects_unknown_chapter_and_missing_revision(self) -> None:
        status, _, _ = self.request("GET", "/api/chapters/99/notes")
        self.assertEqual(status, 404)
        body = json.dumps(sample_document(), ensure_ascii=False).encode("utf-8")
        status, _, content = self.request(
            "PUT",
            "/api/chapters/05/notes",
            body,
            {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Origin": self.origin,
                "X-QFG-Write-Token": "test-write-token",
            },
        )
        self.assertEqual(status, 428)
        self.assertEqual(json.loads(content)["error"]["code"], "revision_required")

    def test_atomic_write_failure_preserves_original(self) -> None:
        original = self.note_path.read_bytes()
        with patch.object(os, "replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                SERVE.write_notes_atomically(self.note_path, b"replacement\n")
        self.assertEqual(self.note_path.read_bytes(), original)
        self.assertEqual(list(self.note_path.parent.glob(".*.tmp")), [])

    def test_macos_website_password_is_injected_without_logging_it(self) -> None:
        fake_key = "test-only-secret"
        result = CompletedProcess([], 0, stdout=f"{fake_key}\n", stderr="")
        with patch.object(SERVE.subprocess, "run", return_value=result) as run:
            with patch.dict(os.environ, {}, clear=True):
                SERVE.inject_api_key_from_macos_internet_password("OpenAPI Key")
                self.assertEqual(os.environ["OPENAI_API_KEY"], fake_key)
        command = run.call_args.args[0]
        self.assertEqual(command[-2:], ["-l", "OpenAPI Key"])
        self.assertNotIn(fake_key, command)

    def test_macos_website_password_lookup_falls_back_to_server_name(self) -> None:
        results = [
            CompletedProcess([], 44, stdout="", stderr="not found"),
            CompletedProcess([], 0, stdout="fallback-secret\n", stderr=""),
        ]
        with patch.object(SERVE.subprocess, "run", side_effect=results) as run:
            with patch.dict(os.environ, {}, clear=True):
                SERVE.inject_api_key_from_macos_internet_password("OpenAPI Key")
                self.assertEqual(os.environ["OPENAI_API_KEY"], "fallback-secret")
        self.assertEqual(run.call_args_list[-1].args[0][-2:], ["-s", "OpenAPI Key"])

    def test_macos_generic_password_is_injected_without_exposing_it(self) -> None:
        fake_key = "generic-test-secret"
        result = CompletedProcess([], 0, stdout=f"{fake_key}\n", stderr="")
        with patch.object(SERVE.subprocess, "run", return_value=result) as run:
            with patch.dict(os.environ, {}, clear=True):
                SERVE.inject_api_key_from_macos_generic_password("org.openai.qfg-reader")
                self.assertEqual(os.environ["OPENAI_API_KEY"], fake_key)
        command = run.call_args.args[0]
        self.assertEqual(command[-2:], ["-s", "org.openai.qfg-reader"])
        self.assertNotIn(fake_key, command)


if __name__ == "__main__":
    unittest.main()
