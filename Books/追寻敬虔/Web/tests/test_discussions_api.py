from __future__ import annotations

import hashlib
import http.client
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
SERVE_PATH = WEB_ROOT / "scripts/serve.py"


def load_serve_module():
    spec = importlib.util.spec_from_file_location("qfg_reader_serve_discussion_tests", SERVE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load server script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SERVE = load_serve_module()


class FakeOpenAIClient:
    configured = True
    model = "gpt-test"

    def stream(self, document, chapter_markdown, **context_options):
        assert "完整章节" in chapter_markdown
        assert context_options["note_document"]["chapterId"] == "05"
        yield {"type": "response.delta", "delta": "流式"}
        yield {"type": "response.delta", "delta": "回复"}
        yield {
            "type": "response.completed",
            "content": "流式回复",
            "responseId": "resp_test",
            "model": self.model,
            "usage": {"inputTokens": 50, "outputTokens": 8, "totalTokens": 58},
        }


class DiscussionAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.dist = root / "dist"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<!doctype html><title>test</title>\n", encoding="utf-8")
        note_path = root / "Notes/Annotations/05.json"
        note_path.parent.mkdir(parents=True)
        note_document = SERVE.empty_note_document("05")
        note_document["notes"] = [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "sourceRevision": "a" * 64,
                "anchor": {
                    "blockId": "05-p-0002",
                    "startOffset": 0,
                    "endOffset": 4,
                    "exact": "完整章节",
                    "prefix": "",
                    "suffix": "正文。",
                },
                "body": "脱敏测试笔记",
                "format": "plain-text",
                "createdAt": "2026-08-29T08:00:00.000Z",
                "updatedAt": "2026-08-29T08:00:00.000Z",
            }
        ]
        note_path.write_bytes(SERVE.serialize_note_document(note_document))
        self.discussion_root = root / "Notes/Discussions"
        self.chapter_markdown = "\n# 第五章\n\n完整章节正文。\n"
        self.revision = hashlib.sha256(self.chapter_markdown.encode("utf-8")).hexdigest()
        chapter_path = root / "Reading/05.md"
        chapter_path.parent.mkdir(parents=True)
        chapter_path.write_text(
            "---\nbook: 追寻敬虔\nchapter: 05\n---\n" + self.chapter_markdown,
            encoding="utf-8",
        )
        self.server = SERVE.build_server(
            0,
            dist_root=self.dist,
            note_paths={"05": note_path},
            discussion_root=self.discussion_root,
            chapter_paths={"05": chapter_path},
            openai_client=FakeOpenAIClient(),
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

    def request(self, method: str, path: str, payload: dict | None = None, extra_headers: dict | None = None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        headers = {}
        if body is not None:
            headers.update(
                {
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "Origin": self.origin,
                    "X-QFG-Write-Token": "test-write-token",
                }
            )
        headers.update(extra_headers or {})
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        result = response.status, dict(response.getheaders()), content
        connection.close()
        return result

    def create_payload(self) -> dict:
        return {
            "sourceRevision": self.revision,
            "anchor": {
                "blockId": "05-p-0002",
                "startOffset": 0,
                "endOffset": 4,
                "exact": "完整章节",
                "prefix": "",
                "suffix": "",
            },
            "scriptures": [],
            "footnotes": [],
            "message": "第一个问题",
        }

    @staticmethod
    def stream_events(content: bytes) -> list[dict]:
        return [json.loads(line) for line in content.decode("utf-8").splitlines() if line]

    def test_create_list_open_continue_and_retry_contract(self) -> None:
        status, _, content = self.request("POST", "/api/chapters/05/discussions", self.create_payload())
        self.assertEqual(status, 200)
        events = self.stream_events(content)
        self.assertEqual([event["type"] for event in events[:3]], ["response.started", "response.delta", "response.delta"])
        completed = events[-1]
        self.assertEqual(completed["type"], "response.completed")
        discussion = completed["discussion"]
        self.assertEqual(discussion["messages"][-1]["content"], "流式回复")
        self.assertEqual(discussion["messages"][-1]["renderedContent"], "<p>流式回复</p>\n")
        discussion_id = discussion["id"]
        disk_path = self.discussion_root / "05" / f"{discussion_id}.json"
        self.assertTrue(disk_path.is_file())

        status, _, content = self.request("GET", "/api/chapters/05/discussions")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["discussions"][0]["id"], discussion_id)

        status, headers, content = self.request("GET", f"/api/discussions/{discussion_id}")
        self.assertEqual(status, 200)
        etag = headers["ETag"]
        opened = json.loads(content)
        self.assertEqual(len(opened["messages"]), 2)
        self.assertEqual(opened["messages"][-1]["renderedContent"], "<p>流式回复</p>\n")

        status, _, content = self.request(
            "POST",
            f"/api/discussions/{discussion_id}/messages",
            {"message": "继续追问"},
            {"If-Match": etag},
        )
        self.assertEqual(status, 200)
        continued_event = self.stream_events(content)[-1]
        continued = continued_event["discussion"]
        self.assertEqual(len(continued["messages"]), 4)
        self.assertEqual(continued["messages"][-2]["content"], "继续追问")

        status, _, content = self.request(
            "DELETE",
            f"/api/discussions/{discussion_id}",
            extra_headers={
                "Origin": self.origin,
                "X-QFG-Write-Token": "test-write-token",
                "If-Match": continued_event["etag"],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content), {"deleted": discussion_id})
        self.assertFalse(disk_path.exists())

    def test_rejects_stale_source_revision_without_creating_file(self) -> None:
        payload = self.create_payload()
        payload["sourceRevision"] = "a" * 64
        status, _, content = self.request("POST", "/api/chapters/05/discussions", payload)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(content)["error"]["code"], "chapter_source_changed")
        self.assertEqual(list(self.discussion_root.rglob("*.json")), [])

    def test_context_preview_lists_notes_and_accepts_round_exclusion(self) -> None:
        payload = self.create_payload()
        status, _, content = self.request(
            "POST", "/api/chapters/05/discussions/context-preview", payload
        )
        self.assertEqual(status, 200)
        preview = json.loads(content)["preview"]
        self.assertEqual(preview["notes"][0]["body"], "脱敏测试笔记")

        payload["excludedNoteIds"] = ["11111111-1111-4111-8111-111111111111"]
        status, _, content = self.request(
            "POST", "/api/chapters/05/discussions/context-preview", payload
        )
        self.assertEqual(status, 200)
        preview = json.loads(content)["preview"]
        self.assertEqual(preview["notes"], [])
        self.assertTrue(preview["noteCandidates"][0]["excluded"])


if __name__ == "__main__":
    unittest.main()
