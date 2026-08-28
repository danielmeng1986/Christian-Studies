from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = WEB_ROOT / "scripts/discussions.py"


def load_module():
    spec = importlib.util.spec_from_file_location("qfg_reader_discussions", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load discussions module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DISCUSSIONS = load_module()


def sample_payload(source_revision: str) -> dict:
    return {
        "sourceRevision": source_revision,
        "anchor": {
            "blockId": "05-p-0001",
            "startOffset": 2,
            "endOffset": 6,
            "exact": "测试文字",
            "prefix": "之前",
            "suffix": "之后",
        },
        "scriptures": [
            {
                "id": "JHN.1.1",
                "translationId": "cuv-s",
                "translationLabel": "和合本（简体）",
                "citation": "约 1:1",
                "text": "太初有道。",
            }
        ],
        "footnotes": [{"id": "1", "text": "脚注正文"}],
        "message": "请解释这段话。",
    }


class DiscussionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chapter_markdown = "\n# 第五章\n\n完整章节正文。\n"
        self.revision = hashlib.sha256(self.chapter_markdown.encode("utf-8")).hexdigest()
        self.document = DISCUSSIONS.create_discussion_document(
            sample_payload(self.revision), "05", "第五章"
        )

    def test_create_complete_and_round_trip(self) -> None:
        self.assertEqual([message["status"] for message in self.document["messages"]], ["completed", "pending"])
        completed = DISCUSSIONS.complete_pending_message(
            self.document,
            {
                "content": "这是回复。",
                "model": "gpt-test",
                "responseId": "resp_123",
                "usage": {"inputTokens": 100, "outputTokens": 20, "totalTokens": 120},
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = DISCUSSIONS.discussion_path(Path(directory), "05", completed["id"])
            content = DISCUSSIONS.serialize_discussion_document(completed)
            DISCUSSIONS.write_atomically(path, content)
            loaded, loaded_content = DISCUSSIONS.load_discussion(path, "05")
        self.assertEqual(loaded, completed)
        self.assertEqual(loaded_content, content)
        self.assertTrue(DISCUSSIONS.document_etag(content).startswith('"'))

    def test_failed_turn_can_retry_without_duplicating_user_message(self) -> None:
        failed = DISCUSSIONS.fail_pending_message(
            self.document,
            DISCUSSIONS.OpenAIClientError("network_error", "网络失败", True),
        )
        retried = DISCUSSIONS.retry_failed_turn(failed)
        self.assertEqual(len(retried["messages"]), 2)
        self.assertEqual(retried["messages"][-1]["status"], "pending")
        self.assertEqual(retried["messages"][0]["content"], "请解释这段话。")

    def test_prompt_contains_local_context_and_no_tools(self) -> None:
        client = DISCUSSIONS.OpenAIResponsesClient("secret", model="gpt-test")
        payload = client._request_payload(self.document, self.chapter_markdown)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertIn("完整章节正文", serialized)
        self.assertIn("太初有道", serialized)
        self.assertIn("脚注正文", serialized)
        self.assertFalse(payload["store"])
        self.assertTrue(payload["stream"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("secret", serialized)

    def test_sse_stream_is_normalized(self) -> None:
        stream = BytesIO(
            b'data: {"type":"response.output_text.delta","delta":"hello "}\n\n'
            b'data: {"type":"response.output_text.delta","delta":"world"}\n\n'
            b'data: {"type":"response.completed","response":{"id":"resp_1","model":"gpt-test",'
            b'"usage":{"input_tokens":10,"output_tokens":2,"total_tokens":12}}}\n\n'
        )
        client = DISCUSSIONS.OpenAIResponsesClient("secret", model="gpt-test")
        events = list(client._read_stream(stream))
        self.assertEqual(events[-1]["content"], "hello world")
        self.assertEqual(events[-1]["usage"]["totalTokens"], 12)

    def test_utf16_anchor_validation_supports_non_bmp_characters(self) -> None:
        payload = sample_payload(self.revision)
        payload["anchor"] = {
            "blockId": "05-p-0001",
            "startOffset": 0,
            "endOffset": 3,
            "exact": "A🙏",
            "prefix": "",
            "suffix": "",
        }
        document = DISCUSSIONS.create_discussion_document(payload, "05", "第五章")
        self.assertEqual(document["anchor"]["endOffset"], 3)

    def test_client_view_renders_safe_assistant_markdown_only(self) -> None:
        completed = DISCUSSIONS.complete_pending_message(
            self.document,
            {
                "content": "## 标题\n\n- 列表\n\n[危险](javascript:alert(1))\n\n<script>alert(2)</script>",
                "model": "gpt-test",
                "responseId": "resp_markdown",
                "usage": {"inputTokens": 10, "outputTokens": 10, "totalTokens": 20},
            },
        )
        client_view = DISCUSSIONS.discussion_for_client(completed)
        rendered = client_view["messages"][-1]["renderedContent"]
        self.assertIn("<h2>标题</h2>", rendered)
        self.assertIn("<li>列表</li>", rendered)
        self.assertNotIn("href=", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("renderedContent", completed["messages"][-1])
        self.assertNotIn("renderedContent", client_view["messages"][0])


if __name__ == "__main__":
    unittest.main()
