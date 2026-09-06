from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = WEB_ROOT / "scripts/edition_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("qfg_edition_review", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REVIEW = load_module()


class EditionReviewTests(unittest.TestCase):
    def markdown(self, text: str, edition: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "05.md"
            path.write_text(f"---\nchapter: 05\nedition_id: {edition}\n---\n# 标题\n\n{text}\n", encoding="utf-8")
            return REVIEW.load_markdown(path, edition_id=edition, chapter_id="05")

    def test_blocks_align_and_content_is_not_copied_to_sidecar(self) -> None:
        source = self.markdown("旧版正文", "legacy-zh")
        target = self.markdown("新版正文", "chatgpt-zh-cn")
        document = REVIEW.build_review_document(source, target)
        self.assertEqual(len(document["pairs"]), 2)
        serialized = REVIEW.serialize(document).decode()
        self.assertNotIn("旧版正文", serialized)
        self.assertNotIn("新版正文", serialized)

    def test_changed_target_hash_invalidates_approval(self) -> None:
        source = self.markdown("旧版正文", "legacy-zh")
        target = self.markdown("新版正文", "chatgpt-zh-cn")
        document = REVIEW.build_review_document(source, target)
        for pair in document["pairs"]:
            REVIEW.apply_review_update(document, {"pairId": pair["pairId"], "status": "approved"})
        REVIEW.approve_chapter(document)
        changed_target = self.markdown("修改后的新版正文", "chatgpt-zh-cn")
        rebuilt = REVIEW.build_review_document(source, changed_target, document)
        self.assertEqual(rebuilt["pairs"][0]["status"], "approved")
        self.assertEqual(rebuilt["pairs"][1]["status"], "draft")
        self.assertNotEqual(rebuilt["chapterStatus"], "approved")

    def test_chapter_approval_requires_every_block(self) -> None:
        source = self.markdown("旧版正文", "legacy-zh")
        target = self.markdown("新版正文", "chatgpt-zh-cn")
        document = REVIEW.build_review_document(source, target)
        with self.assertRaisesRegex(REVIEW.ReviewError, "Every block"):
            REVIEW.approve_chapter(document)

    def test_open_comment_blocks_approval_and_can_be_resolved(self) -> None:
        source = self.markdown("旧版正文", "legacy-zh")
        target = self.markdown("新版正文", "chatgpt-zh-cn")
        document = REVIEW.build_review_document(source, target)
        pair = document["pairs"][1]
        REVIEW.add_review_comment(document, {"pairId": pair["pairId"], "text": "请调整这一句。"})
        comment = pair["comments"][0]
        self.assertEqual(comment["status"], "open")
        with self.assertRaisesRegex(REVIEW.ReviewError, "Resolve every comment"):
            REVIEW.apply_review_update(document, {"pairId": pair["pairId"], "status": "approved"})
        REVIEW.set_comment_status(
            document,
            {"pairId": pair["pairId"], "commentId": comment["commentId"], "status": "resolved"},
        )
        REVIEW.apply_review_update(document, {"pairId": pair["pairId"], "status": "approved"})
        self.assertEqual(pair["status"], "approved")

    def test_target_edit_returns_block_to_draft_but_preserves_comment(self) -> None:
        source = self.markdown("旧版正文", "legacy-zh")
        target = self.markdown("新版正文", "chatgpt-zh-cn")
        document = REVIEW.build_review_document(source, target)
        pair = document["pairs"][1]
        REVIEW.add_review_comment(document, {"pairId": pair["pairId"], "text": "改得更自然一些。"})
        changed_target = self.markdown("修改后的新版正文", "chatgpt-zh-cn")
        rebuilt = REVIEW.build_review_document(source, changed_target, document)
        self.assertEqual(rebuilt["pairs"][1]["status"], "draft")
        self.assertEqual(rebuilt["pairs"][1]["comments"][0]["text"], "改得更自然一些。")

    def test_pilot_sidecars_match_current_markdown(self) -> None:
        book_root = WEB_ROOT.parent
        source = REVIEW.load_markdown(
            book_root / "Reading/第2部分-清教徒与圣经/05-約翰．歐文論從神而來的交通.md",
            edition_id="legacy-zh",
            chapter_id="05",
        )
        target = REVIEW.load_markdown(
            book_root / "Reading/chatgpt-zh-cn/05-约翰·欧文论神如何向人传达真理.md",
            edition_id="chatgpt-zh-cn",
            chapter_id="05",
        )
        review_path = book_root / "Metadata/Edition-Reviews/chatgpt-zh-cn/05.json"
        document = json.loads(review_path.read_text(encoding="utf-8"))
        rebuilt = REVIEW.build_review_document(source, target, document)
        self.assertEqual(rebuilt, document)
        self.assertEqual(len(document["pairs"]), 69)


if __name__ == "__main__":
    unittest.main()
