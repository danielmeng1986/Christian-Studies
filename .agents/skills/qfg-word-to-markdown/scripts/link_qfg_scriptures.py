#!/usr/bin/env python3
"""Add deterministic scripture: links to 《追寻敬虔》 Markdown chapters."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
BIBLE_ROOT = REPO_ROOT / "References/Bible-Texts"
CONFIG_PATH = REPO_ROOT / "Books/追寻敬虔/Metadata/scripture-config.json"


def normalize_alias(value: str) -> str:
    return re.sub(r"[\s.]", "", value).casefold()


def load_context() -> tuple[dict[str, str], list[str], dict[str, dict]]:
    alias_document = json.loads((BIBLE_ROOT / "citation-aliases.json").read_text(encoding="utf-8"))
    aliases = alias_document["aliases"]
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    translations = config["available_translations"]
    corpora = {
        translation: json.loads((BIBLE_ROOT / f"versions/{translation}/verses.json").read_text(encoding="utf-8"))[
            "books"
        ]
        for translation in translations
    }
    return aliases, translations, corpora


def citation_pattern(aliases: dict[str, str]) -> re.Pattern[str]:
    chinese_aliases = sorted(
        (alias for alias in aliases if re.search(r"[\u3400-\u9fff]", alias)),
        key=len,
        reverse=True,
    )
    books = "|".join(re.escape(alias) for alias in chinese_aliases)
    verse_part = r"\d+(?:\s*[-–—]\s*\d+)?"
    verse_list = verse_part + r"(?:\s*[,，、]\s*" + verse_part + r")*"
    continuations = r"(?:\s*[;；]\s*(?:\d+\s*[:：.．]\s*)?" + verse_list + r")*"
    return re.compile(
        r"(?<![\u3400-\u9fffA-Za-z0-9])"
        rf"(?P<book>{books})\s*(?P<chapter>\d+)\s*[:：.．]\s*"
        rf"(?P<verses>{verse_list}{continuations})"
    )


def normalize_verse_list(value: str) -> tuple[str, list[int]]:
    parts = re.split(r"\s*[,，、]\s*", value.strip())
    normalized: list[str] = []
    verses: list[int] = []
    seen: set[int] = set()
    for part in parts:
        match = re.fullmatch(r"(\d+)(?:\s*[-–—]\s*(\d+))?", part)
        if not match:
            raise ValueError(f"Invalid verse selector: {value}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < start:
            raise ValueError(f"Invalid verse range: {value}")
        selected = list(range(start, end + 1))
        if any(verse in seen for verse in selected):
            raise ValueError(f"Overlapping verse selector: {value}")
        seen.update(selected)
        verses.extend(selected)
        normalized.append(str(start) if start == end else f"{start}-{end}")
    return ",".join(normalized), verses


def canonical_reference(match: re.Match[str], aliases: dict[str, str]) -> tuple[str, list[tuple[int, list[int]]]]:
    code = aliases[normalize_alias(match.group("book"))]
    chapter = int(match.group("chapter"))
    raw_segments = re.split(r"\s*[;；]\s*", match.group("verses"))
    normalized_first, verses = normalize_verse_list(raw_segments[0])
    canonical = f"{code}.{chapter}.{normalized_first}"
    selections = [(chapter, verses)]
    for raw_segment in raw_segments[1:]:
        continuation = re.fullmatch(r"(\d+)\s*[:：.．]\s*(.+)", raw_segment)
        if continuation:
            continuation_chapter = int(continuation.group(1))
            verse_source = continuation.group(2)
        else:
            continuation_chapter = chapter
            verse_source = raw_segment
        normalized, continuation_verses = normalize_verse_list(verse_source)
        if continuation_chapter == chapter:
            raise ValueError(f"Same-chapter semicolon must be written with commas: {match.group(0)}")
        canonical += f";{continuation_chapter}.{normalized}"
        selections.append((continuation_chapter, continuation_verses))
    return canonical, selections


def validate_reference(
    canonical: str,
    book: str,
    selections: list[tuple[int, list[int]]],
    translations: list[str],
    corpora: dict[str, dict],
) -> None:
    for translation in translations:
        for chapter, verses in selections:
            chapter_map = corpora[translation].get(book, {}).get(str(chapter), {})
            for verse in verses:
                if str(verse) not in chapter_map:
                    raise ValueError(f"Missing verse in {translation}: {canonical} ({book} {chapter}:{verse})")


def link_text(
    text: str,
    pattern: re.Pattern[str],
    aliases: dict[str, str],
    translations: list[str],
    corpora: dict[str, dict],
) -> tuple[str, list[str]]:
    links: list[str] = []

    def replace(match: re.Match[str]) -> str:
        canonical, selections = canonical_reference(match, aliases)
        book = canonical.split(".", 1)[0]
        validate_reference(canonical, book, selections, translations, corpora)
        links.append(canonical)
        if match.start() > 0 and text[match.start() - 1] == "[" and text[match.end() :].startswith("](scripture:"):
            target = text[match.end() + len("](scripture:") :].split(")", 1)[0]
            if target != canonical:
                raise ValueError(f"Scripture link target mismatch: {match.group(0)} -> {target}, expected {canonical}")
            return match.group(0)
        return f"[{match.group(0)}](scripture:{canonical})"

    return pattern.sub(replace, text), links


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate links without changing files")
    args = parser.parse_args()
    aliases, translations, corpora = load_context()
    pattern = citation_pattern(aliases)
    total = 0
    unique: set[str] = set()
    for path in args.paths:
        source = path.read_text(encoding="utf-8")
        rendered, links = link_text(source, pattern, aliases, translations, corpora)
        total += len(links)
        unique.update(links)
        if not args.check and rendered != source:
            path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"{path}: {len(links)} Scripture reference(s)")
    print(f"Total: {total} link occurrence(s), {len(unique)} unique canonical reference(s)")


if __name__ == "__main__":
    main()
