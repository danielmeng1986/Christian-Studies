from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = WEB_ROOT / "scripts/context_builder.py"


def load_module():
    spec = importlib.util.spec_from_file_location("qfg_reader_context_builder", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load context builder module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTEXT = load_module()


def metadata_source(*, book_id: str = "qfg") -> str:
    return f"""book_id: {book_id}
display_title: 追寻敬虔
title: A Quest for Godliness
subtitle: The Puritan Vision of the Christian Life
author: J. I. Packer
translator: null
publisher: Crossway
publication_year: 1990
language: zh
tags: [puritans, christian-life]
"""


def request(chapter_markdown: str) -> object:
    revision = hashlib.sha256(chapter_markdown.encode("utf-8")).hexdigest()
    return CONTEXT.ContextRequest(
        book_id="qfg",
        chapter_id="05",
        chapter_title="测试章",
        source_revision=revision,
        anchor={
            "blockId": "05-p-0001",
            "startOffset": 0,
            "endOffset": 4,
            "exact": "虚构选区",
            "prefix": "",
            "suffix": "",
        },
        scriptures=[{"id": "TST.1.1", "text": "虚构经文"}],
        footnotes=[{"id": "1", "text": "虚构脚注"}],
        chapter_markdown=chapter_markdown,
        prompt_version=2,
    )


class ContextBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.metadata_path = Path(self.temporary.name) / "book.yml"
        self.metadata_path.write_text(metadata_source(), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_loads_declared_book_identity_without_unrequested_metadata(self) -> None:
        metadata = CONTEXT.load_book_metadata(self.metadata_path)
        self.assertEqual(
            metadata,
            {
                "bookId": "qfg",
                "displayTitle": "追寻敬虔",
                "title": "A Quest for Godliness",
                "subtitle": "The Puritan Vision of the Christian Life",
                "author": "J. I. Packer",
                "publisher": "Crossway",
                "publicationYear": 1990,
                "language": "zh",
                "tags": ["puritans", "christian-life"],
            },
        )
        self.assertNotIn("translator", metadata)

    def test_build_is_deterministic_and_contains_no_network_or_writes(self) -> None:
        chapter = "\n# 测试章\n\n虚构章节正文。\n"
        builder = CONTEXT.ContextBuilder(self.metadata_path)
        first = builder.build(request(chapter))
        second = builder.build(request(chapter))
        self.assertEqual(first, second)
        self.assertEqual(first.envelope["book"]["author"], "J. I. Packer")
        self.assertEqual(first.envelope["chapter"]["sourceChanged"], False)
        self.assertEqual(first.manifest["included"]["scriptureIds"], ["TST.1.1"])
        self.assertEqual(first.manifest["included"]["footnoteIds"], ["1"])
        self.assertEqual(first.manifest["capabilities"]["webSearch"], False)
        self.assertEqual(first.preview["scriptureCount"], 1)
        self.assertEqual(first.estimates["method"], "characters")

    def test_rejects_missing_metadata_instead_of_guessing(self) -> None:
        self.metadata_path.write_text("title: A Quest for Godliness\n", encoding="utf-8")
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "missing"):
            CONTEXT.load_book_metadata(self.metadata_path)

    def test_rejects_book_identity_mismatch(self) -> None:
        self.metadata_path.write_text(metadata_source(book_id="another-book"), encoding="utf-8")
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "does not match"):
            CONTEXT.ContextBuilder(self.metadata_path).build(request("# 测试章\n"))

    def test_rejects_nested_or_unsupported_yaml(self) -> None:
        self.metadata_path.write_text(metadata_source() + "  nested: value\n", encoding="utf-8")
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "must not be nested"):
            CONTEXT.load_book_metadata(self.metadata_path)


if __name__ == "__main__":
    unittest.main()
