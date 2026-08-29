from __future__ import annotations

import hashlib
import importlib.util
import json
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


def request(chapter_markdown: str, **overrides) -> object:
    revision = hashlib.sha256(chapter_markdown.encode("utf-8")).hexdigest()
    values = dict(
        book_id="qfg",
        chapter_id="05",
        chapter_title="测试章",
        source_revision=revision,
        anchor={
            "blockId": "05-p-0002",
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
    values.update(overrides)
    return CONTEXT.ContextRequest(**values)


class ContextBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.metadata_path = Path(self.temporary.name) / "book.yml"
        self.metadata_path.write_text(metadata_source(), encoding="utf-8")
        self.translation_path = Path(self.temporary.name) / "translations.json"
        self.translation_path.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "english": "Owen, John",
                            "chinese": "約翰．歐文",
                            "sourceLine": 416,
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

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
        chapter = "\n# 测试章\n\n虚构选区正文。\n"
        builder = CONTEXT.ContextBuilder(self.metadata_path, self.translation_path)
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

    def test_classifies_and_excludes_user_notes_without_mutation(self) -> None:
        chapter = "# 测试章\n\n虚构选区正文。\n"
        notes = {
            "schemaVersion": 1,
            "bookId": "qfg",
            "chapterId": "05",
            "notes": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "sourceRevision": "a" * 64,
                    "anchor": {"blockId": "05-p-0002", "startOffset": 0, "endOffset": 4, "exact": "虚构选区"},
                    "body": "同一选区笔记",
                    "updatedAt": "2026-08-29T08:00:00.000Z",
                },
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "sourceRevision": "b" * 64,
                    "anchor": {"blockId": "05-p-0002", "startOffset": 2, "endOffset": 6, "exact": "选区正文"},
                    "body": "重叠笔记",
                    "updatedAt": "2026-08-29T09:00:00.000Z",
                },
                {
                    "id": "33333333-3333-4333-8333-333333333333",
                    "sourceRevision": "c" * 64,
                    "anchor": {"blockId": "05-p-0002", "startOffset": 6, "endOffset": 7, "exact": "。"},
                    "body": "同段候选",
                    "updatedAt": "2026-08-29T10:00:00.000Z",
                },
            ],
        }
        original = json.loads(json.dumps(notes))
        bundle = CONTEXT.ContextBuilder(self.metadata_path, self.translation_path).build(
            request(
                chapter,
                note_document=notes,
                excluded_note_ids=frozenset({"22222222-2222-4222-8222-222222222222"}),
            )
        )
        self.assertEqual([note["relation"] for note in bundle.envelope["personalStudy"]["notes"]], ["exact"])
        self.assertEqual(bundle.manifest["included"]["noteIds"], ["11111111-1111-4111-8111-111111111111"])
        self.assertEqual([note["relation"] for note in bundle.preview["noteCandidates"]], ["overlap", "sameBlock"])
        self.assertEqual(notes, original)

    def test_resolves_chinese_and_reversed_english_translation_names(self) -> None:
        chapter = "# 测试章\n\n虚构选区正文。\n"
        builder = CONTEXT.ContextBuilder(self.metadata_path, self.translation_path)
        chinese = builder.build(request(chapter, question="約翰·歐文是谁？"))
        english = builder.build(request(chapter, question="What did John   Owen write?"))
        for bundle in (chinese, english):
            entity = bundle.envelope["referenceResolution"]["entities"][0]
            self.assertEqual(entity["indexForm"], "Owen, John")
            self.assertEqual(entity["canonicalSearchName"], "John Owen")
            self.assertEqual(bundle.manifest["included"]["translationSourceLines"], [416])

    def test_ambiguous_translation_candidates_require_explicit_selection(self) -> None:
        self.translation_path.write_text(
            json.dumps(
                {
                    "entries": [
                        {"english": "Example, Alpha", "chinese": "同名人", "sourceLine": 10},
                        {"english": "Example, Beta", "chinese": "同名人", "sourceLine": 20},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        chapter = "# 测试章\n\n虚构选区正文。\n"
        builder = CONTEXT.ContextBuilder(self.metadata_path, self.translation_path)
        default = builder.build(request(chapter, question="同名人是谁？"))
        self.assertEqual(default.envelope["referenceResolution"]["entities"], [])
        self.assertEqual(
            [item["sourceLine"] for item in default.preview["translationCandidates"]],
            [10, 20],
        )
        selected = builder.build(
            request(
                chapter,
                question="同名人是谁？",
                included_translation_source_lines=frozenset({20}),
            )
        )
        self.assertEqual(selected.manifest["included"]["translationSourceLines"], [20])
        self.assertEqual(selected.envelope["referenceResolution"]["entities"][0]["english"], "Example, Beta")

    def test_rejects_nested_or_unsupported_yaml(self) -> None:
        self.metadata_path.write_text(metadata_source() + "  nested: value\n", encoding="utf-8")
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "must not be nested"):
            CONTEXT.load_book_metadata(self.metadata_path)

    def test_resolves_heading_path_selected_block_and_neighboring_paragraphs(self) -> None:
        chapter = "# 测试章\n\n开头段落。\n\n## 第一小节\n\n目标段落内容。\n\n后续段落。\n"
        focus = CONTEXT.resolve_reading_focus(
            chapter,
            "05",
            {
                "blockId": "05-p-0004",
                "startOffset": 0,
                "endOffset": 4,
                "exact": "目标段落",
                "prefix": "",
                "suffix": "内容。",
            },
        )
        self.assertEqual(focus["headingPath"], ["测试章", "第一小节"])
        self.assertEqual(focus["previousBlock"], {"blockId": "05-p-0002", "text": "开头段落。"})
        self.assertEqual(focus["selectedBlock"]["text"], "目标段落内容。")
        self.assertEqual(focus["nextBlock"], {"blockId": "05-p-0005", "text": "后续段落。"})

    def test_chapter_boundaries_return_null_neighbors(self) -> None:
        chapter = "# 测试章\n\n第一段。\n\n最后一段。\n"
        first = CONTEXT.resolve_reading_focus(
            chapter,
            "05",
            {
                "blockId": "05-p-0002",
                "startOffset": 0,
                "endOffset": 3,
                "exact": "第一段",
                "prefix": "",
                "suffix": "。",
            },
        )
        last = CONTEXT.resolve_reading_focus(
            chapter,
            "05",
            {
                "blockId": "05-p-0003",
                "startOffset": 0,
                "endOffset": 4,
                "exact": "最后一段",
                "prefix": "",
                "suffix": "。",
            },
        )
        self.assertIsNone(first["previousBlock"])
        self.assertEqual(first["nextBlock"]["blockId"], "05-p-0003")
        self.assertEqual(last["previousBlock"]["blockId"], "05-p-0002")
        self.assertIsNone(last["nextBlock"])

    def test_heading_selection_is_explicit_and_uses_paragraph_neighbors(self) -> None:
        chapter = "# 测试章\n\n前文。\n\n## 被选小节\n\n后文。\n"
        focus = CONTEXT.resolve_reading_focus(
            chapter,
            "05",
            {
                "blockId": "05-h2-0003",
                "startOffset": 0,
                "endOffset": 4,
                "exact": "被选小节",
                "prefix": "",
                "suffix": "",
            },
        )
        self.assertEqual(focus["selectedBlock"]["kind"], "heading")
        self.assertEqual(focus["headingPath"], ["测试章", "被选小节"])
        self.assertEqual(focus["previousBlock"]["text"], "前文。")
        self.assertEqual(focus["nextBlock"]["text"], "后文。")

    def test_block_map_matches_link_projection_and_nested_paragraph_ids(self) -> None:
        chapter = (
            "# 测试章\n\n"
            "[普通链接](https://example.test) [经文](scripture:JHN.1.1) "
            "[1](../References/Footnotes-05.md#1) 尾\n\n"
            "> 引用段落\n\n"
            "- 列表段落\n"
        )
        blocks = CONTEXT.build_block_map(chapter, "05")
        self.assertEqual([block.block_id for block in blocks], ["05-h1-0001", "05-p-0002", "05-p-0003", "05-p-0004"])
        self.assertEqual(blocks[1].text, "普通链接 经文  尾")
        self.assertEqual(blocks[2].text, "引用段落")
        self.assertEqual(blocks[3].text, "列表段落")

    def test_utf16_offsets_support_non_bmp_selection(self) -> None:
        focus = CONTEXT.resolve_reading_focus(
            "# 测试章\n\nA🙏B\n",
            "05",
            {
                "blockId": "05-p-0002",
                "startOffset": 1,
                "endOffset": 3,
                "exact": "🙏",
                "prefix": "A",
                "suffix": "B",
            },
        )
        self.assertEqual(focus["selection"]["exact"], "🙏")

    def test_rejects_stale_or_split_selection_without_relocation(self) -> None:
        chapter = "# 测试章\n\n当前正文。\n"
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "does not match"):
            CONTEXT.resolve_reading_focus(
                chapter,
                "05",
                {
                    "blockId": "05-p-0002",
                    "startOffset": 0,
                    "endOffset": 2,
                    "exact": "旧文",
                    "prefix": "",
                    "suffix": "正文。",
                },
            )
        with self.assertRaisesRegex(CONTEXT.ContextBuildError, "split"):
            CONTEXT.resolve_reading_focus(
                "# 测试章\n\n🙏\n",
                "05",
                {
                    "blockId": "05-p-0002",
                    "startOffset": 0,
                    "endOffset": 1,
                    "exact": "错误",
                    "prefix": "",
                    "suffix": "",
                },
            )


if __name__ == "__main__":
    unittest.main()
