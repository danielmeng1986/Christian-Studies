from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = WEB_ROOT / "scripts/build.py"


def load_build_module():
    spec = importlib.util.spec_from_file_location("qfg_reader_build", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_build_module()


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.article_counts: dict[str, int] = {}
        self.block_ids: list[str] = []
        self.block_anchor_ids: list[str] = []
        self.footnote_refs: list[str] = []
        self.footnote_templates: list[str] = []
        self.scripture_refs: list[str] = []
        self.in_article = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "article" and attributes.get("id") == "chapter-article":
            self.in_article = True
        if tag == "template" and attributes.get("data-footnote-id"):
            self.footnote_templates.append(attributes["data-footnote-id"] or "")
        if not self.in_article:
            return
        self.article_counts[tag] = self.article_counts.get(tag, 0) + 1
        if "data-block-id" in attributes and attributes["data-block-id"]:
            self.block_ids.append(attributes["data-block-id"] or "")
            self.block_anchor_ids.append(attributes.get("id") or "")
        if "footnote-ref" in (attributes.get("class") or ""):
            self.footnote_refs.append(attributes.get("data-footnote-id") or "")
        if "scripture-ref" in (attributes.get("class") or ""):
            self.scripture_refs.append(attributes.get("data-scripture-id") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self.in_article:
            self.in_article = False


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        BUILD.build()
        self.output_path = BUILD.OUTPUT_PATH
        self.output = self.output_path.read_text(encoding="utf-8")

    def test_chapter_structure(self) -> None:
        parser = StructureParser()
        parser.feed(self.output)
        self.assertEqual(parser.article_counts.get("h1"), 1)
        self.assertEqual(parser.article_counts.get("h2"), 8)
        self.assertEqual(len(parser.block_ids), len(set(parser.block_ids)))
        self.assertEqual(parser.block_anchor_ids, parser.block_ids)
        self.assertGreater(len(parser.block_ids), 60)

    def test_template_and_navigation(self) -> None:
        self.assertNotIn("{{ARTICLE_HTML}}", self.output)
        self.assertIn('id="chapter-navigation"', self.output)
        self.assertIn('data-theme-choice="light"', self.output)
        self.assertIn('data-theme-choice="sepia"', self.output)
        self.assertIn('data-theme-choice="dark"', self.output)
        self.assertRegex(self.output, r'data-source-revision="[0-9a-f]{64}"')
        self.assertEqual(self.output.count('class="chapter-menu__option"'), 20)
        self.assertIn('aria-selected="true" aria-current="page" href="/chapters/05/"', self.output)
        self.assertIn('role="listbox" aria-label="选择章节"', self.output)
        for chapter_id in range(1, 21):
            self.assertTrue((BUILD.DIST_ROOT / f"chapters/{chapter_id:02d}/index.html").is_file())

    def test_notes_list_can_collapse_to_recent_items(self) -> None:
        app_js = (BUILD.ASSET_ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("sortedNotes.slice(0, 3)", app_js)
        self.assertIn('id="toggle-all-notes"', self.output)

    def test_ai_discussion_controls_are_built(self) -> None:
        app_js = (BUILD.ASSET_ROOT / "app.js").read_text(encoding="utf-8")
        app_css = (BUILD.ASSET_ROOT / "app.css").read_text(encoding="utf-8")
        self.assertIn('id="selection-note-action"', self.output)
        self.assertIn('id="selection-discuss-action"', self.output)
        self.assertIn('id="discussions-tab"', self.output)
        self.assertIn('id="discussion-start-form"', self.output)
        self.assertIn('id="study-panel-resizer"', self.output)
        self.assertIn('role="separator"', self.output)
        self.assertIn("selectionReferences(range)", app_js)
        self.assertIn('event.type === "response.delta"', app_js)
        self.assertIn('shell.classList.toggle("discussion-focus"', app_js)
        self.assertIn("qfg-reader-discussion-panel-width", app_js)
        self.assertIn(".app-shell.discussion-focus", app_css)

    def test_each_chapter_has_a_repository_note_source(self) -> None:
        for chapter in range(1, 21):
            chapter_id = f"{chapter:02d}"
            note_path = BUILD.BOOK_ROOT / f"Notes/Annotations/{chapter_id}.json"
            document = json.loads(note_path.read_text(encoding="utf-8"))
            self.assertEqual(document["bookId"], "qfg")
            self.assertEqual(document["chapterId"], chapter_id)
            self.assertIsInstance(document["notes"], list)

    def test_footnotes_are_compiled_and_interactive(self) -> None:
        parser = StructureParser()
        parser.feed(self.output)
        self.assertEqual(len(parser.footnote_refs), 35)
        self.assertEqual(len(parser.footnote_templates), 35)
        self.assertEqual(set(parser.footnote_refs), set(parser.footnote_templates))
        self.assertNotIn("Footnotes-05.md#", self.output)
        self.assertIn("译者注1", parser.footnote_templates)
        self.assertIn("译者注2", parser.footnote_templates)

    def test_scriptures_are_compiled_and_interactive(self) -> None:
        parser = StructureParser()
        parser.feed(self.output)
        self.assertEqual(len(parser.scripture_refs), 28)
        self.assertEqual(len(set(parser.scripture_refs)), 26)
        self.assertNotIn("scripture:", self.output)
        self.assertIn('aria-controls="reference-panel"', self.output)
        self.assertIn('id="show-all-references"', self.output)

        match = re.search(
            r'<script type="application/json" id="scripture-data">(.*?)</script>',
            self.output,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        self.assertEqual(payload["defaultTranslation"], "cuv-s")
        self.assertEqual(payload["translationOrder"], ["cuv-s", "kjv", "asv"])
        self.assertEqual(len(payload["references"]), 26)
        luke = payload["references"]["LUK.4.23"]["versions"]
        self.assertEqual(luke["cuv-s"]["citation"], "路 4:23")
        self.assertEqual(luke["kjv"]["citation"], "Luke 4:23")
        self.assertEqual(luke["asv"]["citation"], "Luke 4:23")
        self.assertEqual(payload["translations"]["asv"]["label"], "American Standard Version 1901")
        self.assertNotIn("  ", luke["kjv"]["text"])
        self.assertIn("1CO.2.4,5;15.25,26", payload["references"])

    def test_scripture_uri_validation(self) -> None:
        config, _, books = BUILD.load_scripture_context()
        parsed = BUILD.parse_scripture_uri(
            "scripture:1TH.1.5-10;2.13?version=kjv",
            books,
            config["available_translations"],
        )
        self.assertEqual(parsed["id"], "1TH.1.5-10;2.13")
        self.assertEqual(parsed["initialTranslation"], "kjv")
        with self.assertRaisesRegex(ValueError, "Reversed"):
            BUILD.parse_scripture_uri("scripture:LUK.1.45-44", books, config["available_translations"])
        with self.assertRaisesRegex(ValueError, "Unknown Scripture book"):
            BUILD.parse_scripture_uri("scripture:XYZ.1.1", books, config["available_translations"])
        with self.assertRaisesRegex(ValueError, "Disallowed"):
            BUILD.parse_scripture_uri("scripture:LUK.1.1?version=web", books, config["available_translations"])
        with self.assertRaisesRegex(ValueError, "Empty Scripture translation"):
            BUILD.parse_scripture_uri("scripture:LUK.1.1?version=", books, config["available_translations"])

    def test_scripture_passage_joining_matches_project_format(self) -> None:
        config, translations, books = BUILD.load_scripture_context()
        reference = BUILD.parse_scripture_uri(
            "scripture:LUK.1.44-45",
            books,
            config["available_translations"],
        )
        versions = BUILD.build_scripture_data([reference], config, translations, books)["references"][reference["id"]][
            "versions"
        ]
        self.assertEqual(
            versions["cuv-s"]["text"],
            "因为你问安的声音一入我耳，我腹里的胎就欢喜跳动。"
            "这相信的女子是有福的！因为主对她所说的话都要应验。」",
        )
        self.assertEqual(versions["cuv-s"]["citation"], "路 1:44–45")
        self.assertIn("joy. And blessed", versions["kjv"]["text"])
        self.assertEqual(versions["kjv"]["citation"], "Luke 1:44–45")

    def test_output_excludes_private_and_machine_specific_data(self) -> None:
        self.assertNotIn(str(BUILD.REPO_ROOT), self.output)
        self.assertNotIn("Notes/Annotations", self.output)
        self.assertNotIn("sourceRevision", self.output)

    def test_ai_markdown_rendering_assets_are_present(self) -> None:
        app_js = (BUILD.ASSET_ROOT / "app.js").read_text(encoding="utf-8")
        app_css = (BUILD.ASSET_ROOT / "app.css").read_text(encoding="utf-8")
        self.assertIn("message.renderedContent", app_js)
        self.assertIn(".markdown-content blockquote", app_css)
        self.assertIn(".markdown-content table", app_css)

    def test_repeated_build_is_deterministic(self) -> None:
        paths = [BUILD.DIST_ROOT / f"chapters/{chapter:02d}/index.html" for chapter in range(1, 21)]
        first = {path: hashlib.sha256(path.read_bytes()).digest() for path in paths}
        BUILD.build()
        second = {path: hashlib.sha256(path.read_bytes()).digest() for path in paths}
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
