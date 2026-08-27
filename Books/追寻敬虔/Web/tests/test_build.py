from __future__ import annotations

import hashlib
import importlib.util
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
        self.in_article = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "article" and attributes.get("id") == "chapter-article":
            self.in_article = True
        if not self.in_article:
            return
        self.article_counts[tag] = self.article_counts.get(tag, 0) + 1
        if "data-block-id" in attributes and attributes["data-block-id"]:
            self.block_ids.append(attributes["data-block-id"] or "")

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
        self.assertGreater(len(parser.block_ids), 60)

    def test_template_and_navigation(self) -> None:
        self.assertNotIn("{{ARTICLE_HTML}}", self.output)
        self.assertIn('id="chapter-navigation"', self.output)
        self.assertIn('data-theme-choice="light"', self.output)
        self.assertIn('data-theme-choice="sepia"', self.output)
        self.assertIn('data-theme-choice="dark"', self.output)

    def test_output_excludes_private_and_machine_specific_data(self) -> None:
        self.assertNotIn(str(BUILD.REPO_ROOT), self.output)
        self.assertNotIn("Notes/Annotations", self.output)
        self.assertNotIn("sourceRevision", self.output)

    def test_repeated_build_is_deterministic(self) -> None:
        first = hashlib.sha256(self.output_path.read_bytes()).digest()
        BUILD.build()
        second = hashlib.sha256(self.output_path.read_bytes()).digest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
