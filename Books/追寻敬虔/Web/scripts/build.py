#!/usr/bin/env python3
"""Build the deterministic multi-chapter reading application."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, unquote

from markdown_it import MarkdownIt


WEB_ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = WEB_ROOT.parent
REPO_ROOT = BOOK_ROOT.parents[1]
READING_ROOT = BOOK_ROOT / "Reading"
FOOTNOTE_ROOT = BOOK_ROOT / "References"
SCRIPTURE_CONFIG_PATH = BOOK_ROOT / "Metadata/scripture-config.json"
BIBLE_ROOT = REPO_ROOT / "References/Bible-Texts"
BIBLE_MANIFEST_PATH = BIBLE_ROOT / "manifest.json"
BIBLE_BOOKS_PATH = BIBLE_ROOT / "books.json"
TEMPLATE_PATH = WEB_ROOT / "src/templates/chapter.html"
ASSET_ROOT = WEB_ROOT / "src/assets"
DIST_ROOT = WEB_ROOT / "dist"
OUTPUT_PATH = DIST_ROOT / "chapters/05/index.html"

FRONT_MATTER_RE = re.compile(r"\A---\n(?P<meta>.*?)\n---\n", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FOOTNOTE_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$\n(?P<body>.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
FOOTNOTE_LINK_RE = re.compile(r"(?:^|/)Footnotes-(?P<chapter>\d{2})\.md#(?P<fragment>.+)$")
SCRIPTURE_FIRST_SEGMENT_RE = re.compile(r"^(?P<book>[1-3]?[A-Z]{2,3})\.(?P<chapter>[1-9]\d*)\.(?P<verses>.+)$")
SCRIPTURE_NEXT_SEGMENT_RE = re.compile(r"^(?P<chapter>[1-9]\d*)\.(?P<verses>.+)$")
SCRIPTURE_VERSE_PART_RE = re.compile(r"^(?P<start>[1-9]\d*)(?:-(?P<end>[1-9]\d*))?$")


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


def markdown_parser() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})


def load_scripture_context() -> tuple[dict, dict[str, dict], dict[str, dict]]:
    config = json.loads(SCRIPTURE_CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(BIBLE_MANIFEST_PATH.read_text(encoding="utf-8"))
    books_document = json.loads(BIBLE_BOOKS_PATH.read_text(encoding="utf-8"))
    translations = {item["id"]: item for item in manifest["translations"]}
    books = {item["code"]: item for item in books_document["books"]}

    if config.get("schema_version") != 1:
        raise ValueError("Unsupported Scripture configuration schema")
    available = config.get("available_translations")
    default = config.get("default_translation")
    if not isinstance(available, list) or not available or len(set(available)) != len(available):
        raise ValueError("available_translations must be a non-empty list of unique IDs")
    if default not in available:
        raise ValueError("default_translation must occur in available_translations")
    unknown = [translation_id for translation_id in available if translation_id not in translations]
    if unknown:
        raise ValueError(f"Unknown configured translation(s): {', '.join(unknown)}")
    labels = config.get("translation_labels", {})
    if not isinstance(labels, dict):
        raise ValueError("translation_labels must be an object")
    for translation_id, label in labels.items():
        if translation_id not in available or not isinstance(label, str) or not label.strip():
            raise ValueError(f"Invalid translation label override: {translation_id}")
    return config, translations, books


def parse_verse_spec(verse_spec: str, target: str) -> tuple[str, list[int]]:
    normalized_parts: list[str] = []
    verses: list[int] = []
    seen: set[int] = set()
    for part in verse_spec.split(","):
        match = SCRIPTURE_VERSE_PART_RE.fullmatch(part)
        if not match:
            raise ValueError(f"Invalid Scripture verse selector: {target}")
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        if end < start:
            raise ValueError(f"Reversed Scripture verse range: {target}")
        selected = list(range(start, end + 1))
        if any(verse in seen for verse in selected):
            raise ValueError(f"Overlapping Scripture verse selector: {target}")
        seen.update(selected)
        verses.extend(selected)
        normalized_parts.append(str(start) if start == end else f"{start}-{end}")
    return ",".join(normalized_parts), verses


def parse_scripture_uri(href: str, books: dict[str, dict], allowed_translations: list[str]) -> dict:
    target = href.removeprefix("scripture:")
    path, separator, query = target.partition("?")
    params = parse_qs(query, strict_parsing=True, keep_blank_values=True) if separator else {}
    if set(params) - {"version"} or any(len(values) != 1 for values in params.values()):
        raise ValueError(f"Invalid Scripture query: {href}")
    initial_translation = params.get("version", [None])[0]
    if initial_translation == "":
        raise ValueError(f"Empty Scripture translation: {href}")
    if initial_translation and initial_translation not in allowed_translations:
        raise ValueError(f"Disallowed Scripture translation {initial_translation}: {href}")

    raw_segments = path.split(";")
    first = SCRIPTURE_FIRST_SEGMENT_RE.fullmatch(raw_segments[0]) if raw_segments else None
    if not first:
        raise ValueError(f"Invalid Scripture URI: {href}")
    book = first.group("book")
    if book not in books:
        raise ValueError(f"Unknown Scripture book {book}: {href}")

    segments: list[dict] = []
    canonical_segments: list[str] = []
    for index, raw_segment in enumerate(raw_segments):
        match = first if index == 0 else SCRIPTURE_NEXT_SEGMENT_RE.fullmatch(raw_segment)
        if not match:
            raise ValueError(f"Invalid Scripture continuation: {href}")
        chapter = int(match.group("chapter"))
        normalized_spec, verses = parse_verse_spec(match.group("verses"), href)
        segments.append({"chapter": chapter, "verseSpec": normalized_spec, "verses": verses})
        canonical_segments.append(f"{chapter}.{normalized_spec}")

    canonical = f"{book}.{canonical_segments[0]}"
    if len(canonical_segments) > 1:
        canonical += ";" + ";".join(canonical_segments[1:])
    return {
        "id": canonical,
        "book": book,
        "segments": segments,
        "initialTranslation": initial_translation,
    }


def render_markdown(
    markdown_source: str,
    chapter_id: str,
    books: dict[str, dict],
    available_translations: list[str],
    default_translation: str,
) -> tuple[str, list[str], list[dict], list[dict[str, str]]]:
    parser = markdown_parser()
    tokens = parser.parse(markdown_source)
    block_index = 0
    referenced_footnotes: list[str] = []
    referenced_scriptures: list[dict] = []
    outline_headings: list[dict[str, str]] = []
    scripture_ids: set[str] = set()

    for token_index, token in enumerate(tokens):
        if token.type == "inline" and token.children:
            for child in token.children:
                if child.type != "link_open":
                    continue
                href = child.attrGet("href") or ""
                if href.startswith("scripture:"):
                    reference = parse_scripture_uri(href, books, available_translations)
                    scripture_id = reference["id"]
                    initial_translation = reference["initialTranslation"] or default_translation
                    child.attrSet("href", f"#scripture-{scripture_id}")
                    child.attrSet("class", "scripture-ref")
                    child.attrSet("data-scripture-id", scripture_id)
                    child.attrSet("data-initial-version", initial_translation)
                    child.attrSet("aria-controls", "reference-panel")
                    child.attrSet("aria-expanded", "false")
                    if scripture_id not in scripture_ids:
                        scripture_ids.add(scripture_id)
                        referenced_scriptures.append(reference)
                    continue
                match = FOOTNOTE_LINK_RE.search(href)
                if not match:
                    continue
                if match.group("chapter") != chapter_id:
                    raise ValueError(f"Footnote link points outside chapter {chapter_id}: {href}")
                footnote_id = unquote(match.group("fragment"))
                child.attrSet("href", f"#footnote-{footnote_id}")
                child.attrSet("class", "footnote-ref")
                child.attrSet("data-footnote-id", footnote_id)
                child.attrSet("aria-controls", "reference-panel")
                child.attrSet("aria-expanded", "false")
                if footnote_id not in referenced_footnotes:
                    referenced_footnotes.append(footnote_id)
        if token.type not in {"heading_open", "paragraph_open"}:
            continue
        block_index += 1
        tag = token.tag if token.tag in {"h1", "h2"} else "p"
        block_id = f"{chapter_id}-{tag}-{block_index:04d}"
        token.attrSet("id", block_id)
        token.attrSet("data-block-id", block_id)
        if token.type == "heading_open":
            inline = tokens[token_index + 1] if token_index + 1 < len(tokens) else None
            if inline is None or inline.type != "inline" or not inline.content.strip():
                raise ValueError(f"Missing text for chapter heading: {block_id}")
            outline_headings.append({"id": block_id, "level": tag, "text": inline.content.strip()})

    return (
        parser.renderer.render(tokens, parser.options, {}),
        referenced_footnotes,
        referenced_scriptures,
        outline_headings,
    )


def render_section_navigation(headings: list[dict[str, str]]) -> str:
    items = []
    for index, heading in enumerate(headings):
        heading_id = html.escape(heading["id"], quote=True)
        level = html.escape(heading["level"], quote=True)
        label = html.escape(heading["text"])
        current = ' aria-current="location"' if index == 0 else ""
        items.append(
            f'<li class="outline-menu__item" data-level="{level}">'
            f'<a class="outline-menu__option" data-outline-target="{heading_id}" '
            f'href="#{heading_id}"{current}>{label}</a></li>'
        )
    return "\n".join(items)


def citation_selector(reference: dict) -> str:
    parts = []
    for segment in reference["segments"]:
        verse_spec = segment["verseSpec"].replace("-", "–").replace(",", ", ")
        parts.append(f'{segment["chapter"]}:{verse_spec}')
    return "; ".join(parts)


def build_scripture_data(
    references: list[dict],
    config: dict,
    translations: dict[str, dict],
    books: dict[str, dict],
) -> dict:
    translation_order = config["available_translations"]
    labels = config.get("translation_labels", {})
    corpora = {
        translation_id: json.loads(
            (BIBLE_ROOT / f"versions/{translation_id}/verses.json").read_text(encoding="utf-8")
        )["books"]
        for translation_id in translation_order
    }
    payload = {
        "defaultTranslation": config["default_translation"],
        "translationOrder": translation_order,
        "translations": {},
        "references": {},
    }
    for translation_id in translation_order:
        metadata = translations[translation_id]
        payload["translations"][translation_id] = {
            "label": labels.get(translation_id, metadata["name"]),
            "language": metadata["language"],
        }

    for reference in references:
        book = books[reference["book"]]
        selector = citation_selector(reference)
        versions = {}
        for translation_id in translation_order:
            metadata = translations[translation_id]
            language = metadata["language"]
            texts: list[str] = []
            for segment in reference["segments"]:
                for verse in segment["verses"]:
                    try:
                        texts.append(corpora[translation_id][reference["book"]][str(segment["chapter"])][str(verse)])
                    except KeyError as error:
                        raise ValueError(
                            f'Missing verse in {translation_id}: {reference["book"]} '
                            f'{segment["chapter"]}:{verse}'
                        ) from error
            is_chinese = language.startswith("zh")
            if language == "zh-Hant":
                book_label = book["abbreviation_zh_hant"]
            elif language == "zh-Hans":
                book_label = book["abbreviation_zh_hans"]
            else:
                book_label = book["name_en"]
            versions[translation_id] = {
                "text": "".join(texts) if is_chinese else " ".join(texts),
                "citation": f"{book_label} {selector}",
            }
        payload["references"][reference["id"]] = {"versions": versions}
    return payload


def serialize_scripture_data(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")


def render_footnotes(source: str) -> tuple[str, set[str]]:
    parser = markdown_parser()
    templates: list[str] = []
    footnote_ids: set[str] = set()

    for match in FOOTNOTE_SECTION_RE.finditer(source):
        footnote_id = match.group(1).strip()
        body = match.group("body").strip()
        if footnote_id in footnote_ids:
            raise ValueError(f"Duplicate footnote heading: {footnote_id}")
        footnote_ids.add(footnote_id)
        rendered = parser.render(body).rstrip()
        safe_id = html.escape(footnote_id, quote=True)
        templates.append(
            f'<template id="footnote-template-{safe_id}" data-footnote-id="{safe_id}">\n'
            f'{rendered}\n'
            "</template>"
        )

    return "\n".join(templates), footnote_ids


def discover_chapters() -> list[dict[str, str | Path]]:
    chapters = []
    seen: set[str] = set()
    for source_path in sorted(READING_ROOT.rglob("*.md")):
        source = source_path.read_text(encoding="utf-8")
        body, metadata = strip_front_matter(source)
        chapter_id = metadata.get("chapter", "")
        if not re.fullmatch(r"\d{2}", chapter_id):
            raise ValueError(f"Missing or invalid chapter metadata: {source_path}")
        if chapter_id in seen:
            raise ValueError(f"Duplicate chapter metadata: {chapter_id}")
        title_match = TITLE_RE.search(body)
        if not title_match:
            raise ValueError(f"Missing chapter title: {source_path}")
        title = title_match.group(1).strip()
        title_parts = re.split(r"[：:]", title, maxsplit=1)
        chapter_label = title_parts[0]
        chapter_title = title_parts[1] if len(title_parts) == 2 else title
        chapters.append(
            {
                "id": chapter_id,
                "source_path": source_path,
                "footnote_path": FOOTNOTE_ROOT / f"Footnotes-{chapter_id}.md",
                "title": title,
                "label": chapter_label,
                "short_title": chapter_title,
            }
        )
        seen.add(chapter_id)
    chapters.sort(key=lambda chapter: str(chapter["id"]))
    if [chapter["id"] for chapter in chapters] != [f"{number:02d}" for number in range(1, 21)]:
        raise ValueError("Reading directory must contain chapters 01 through 20")
    return chapters


def render_chapter_navigation(chapters: list[dict[str, str | Path]], selected_id: str) -> str:
    options = []
    for chapter in chapters:
        chapter_id = str(chapter["id"])
        selected = "true" if chapter_id == selected_id else "false"
        current = ' aria-current="page"' if chapter_id == selected_id else ""
        label = html.escape(f'{chapter["label"]} · {chapter["short_title"]}')
        options.append(
            f'<a class="chapter-menu__option" role="option" aria-selected="{selected}"{current} '
            f'href="/chapters/{chapter_id}/">{label}</a>'
        )
    return "\n".join(options)


def build_chapter(
    chapter: dict[str, str | Path],
    chapters: list[dict[str, str | Path]],
    scripture_context: tuple[dict, dict[str, dict], dict[str, dict]],
) -> Path:
    chapter_id = str(chapter["id"])
    source_path = Path(chapter["source_path"])
    footnote_path = Path(chapter["footnote_path"])
    source = source_path.read_text(encoding="utf-8")
    body, metadata = strip_front_matter(source)
    title = str(chapter["title"])
    source_revision = hashlib.sha256(body.encode("utf-8")).hexdigest()
    scripture_config, translations, books = scripture_context
    article_html, referenced_footnotes, referenced_scriptures, outline_headings = render_markdown(
        body,
        chapter_id,
        books,
        scripture_config["available_translations"],
        scripture_config["default_translation"],
    )
    article_html = article_html.rstrip()
    footnote_templates, available_footnotes = render_footnotes(footnote_path.read_text(encoding="utf-8"))
    missing = [footnote_id for footnote_id in referenced_footnotes if footnote_id not in available_footnotes]
    if missing:
        raise ValueError(f"Missing footnote target(s): {', '.join(missing)}")
    scripture_data = build_scripture_data(referenced_scriptures, scripture_config, translations, books)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    page_title = f"{title}｜追寻敬虔"
    output = template.replace("{{PAGE_TITLE}}", html.escape(page_title, quote=True))
    output = output.replace("{{CHAPTER_ID}}", chapter_id)
    output = output.replace("{{CHAPTER_LABEL}}", html.escape(str(chapter["label"])))
    output = output.replace(
        "{{CHAPTER_MENU_LABEL}}",
        html.escape(f'{chapter["label"]} · {chapter["short_title"]}'),
    )
    output = output.replace("{{CHAPTER_NAVIGATION}}", render_chapter_navigation(chapters, chapter_id))
    output = output.replace("{{SECTION_NAVIGATION}}", render_section_navigation(outline_headings))
    output = output.replace("{{SOURCE_REVISION}}", source_revision)
    output = output.replace("{{ARTICLE_HTML}}", article_html)
    output = output.replace("{{FOOTNOTE_TEMPLATES}}", footnote_templates)
    output = output.replace("{{SCRIPTURE_DATA}}", serialize_scripture_data(scripture_data))

    output_path = DIST_ROOT / f"chapters/{chapter_id}/index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")

    return output_path.relative_to(REPO_ROOT)


def build() -> list[Path]:
    chapters = discover_chapters()
    scripture_context = load_scripture_context()
    outputs = [build_chapter(chapter, chapters, scripture_context) for chapter in chapters]

    (DIST_ROOT / "assets").mkdir(parents=True, exist_ok=True)

    for asset_name in ("app.css", "app.js"):
        source_asset = ASSET_ROOT / asset_name
        target_asset = DIST_ROOT / "assets" / asset_name
        target_asset.write_bytes(source_asset.read_bytes())

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    outputs = build()
    print(f"Built {len(outputs)} chapters in {DIST_ROOT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
