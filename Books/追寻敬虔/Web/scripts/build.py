#!/usr/bin/env python3
"""Build the deterministic Chapter 05 reading prototype."""

from __future__ import annotations

import argparse
import html
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt


WEB_ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = WEB_ROOT.parent
REPO_ROOT = BOOK_ROOT.parents[1]
SOURCE_PATH = BOOK_ROOT / "Reading/第2部分-清教徒与圣经/05-約翰．歐文論從神而來的交通.md"
TEMPLATE_PATH = WEB_ROOT / "src/templates/chapter.html"
ASSET_ROOT = WEB_ROOT / "src/assets"
DIST_ROOT = WEB_ROOT / "dist"
OUTPUT_PATH = DIST_ROOT / "chapters/05/index.html"

FRONT_MATTER_RE = re.compile(r"\A---\n(?P<meta>.*?)\n---\n", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def strip_front_matter(source: str) -> tuple[str, dict[str, str]]:
    match = FRONT_MATTER_RE.match(source)
    if not match:
        return source, {}

    metadata: dict[str, str] = {}
    for line in match.group("meta").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"')
    return source[match.end() :], metadata


def render_markdown(markdown_source: str) -> str:
    parser = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    tokens = parser.parse(markdown_source)
    block_index = 0

    for token in tokens:
        if token.type not in {"heading_open", "paragraph_open"}:
            continue
        block_index += 1
        tag = token.tag if token.tag in {"h1", "h2"} else "p"
        token.attrSet("data-block-id", f"05-{tag}-{block_index:04d}")

    return parser.renderer.render(tokens, parser.options, {})


def build() -> Path:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    body, metadata = strip_front_matter(source)
    title_match = TITLE_RE.search(body)
    title = title_match.group(1).strip() if title_match else "第五章"
    article_html = render_markdown(body).rstrip()

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    page_title = f"{title}｜追寻敬虔"
    output = template.replace("{{PAGE_TITLE}}", html.escape(page_title, quote=True))
    output = output.replace("{{ARTICLE_HTML}}", article_html)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    (DIST_ROOT / "assets").mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")

    for asset_name in ("app.css", "app.js"):
        source_asset = ASSET_ROOT / asset_name
        target_asset = DIST_ROOT / "assets" / asset_name
        target_asset.write_bytes(source_asset.read_bytes())

    return OUTPUT_PATH.relative_to(REPO_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output = build()
    print(f"Built {output}")


if __name__ == "__main__":
    main()
