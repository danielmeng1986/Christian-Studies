#!/usr/bin/env python3
"""Look up Chinese or English Scripture references in the local corpus."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = re.compile(
    r"^\s*(.+?)\s*(\d+)\s*[:：.．]\s*(\d+)"
    r"(?:\s*[-–—]\s*(\d+))?\s*$"
)


def normalize_alias(value: str) -> str:
    return re.sub(r"[\s.]", "", value).casefold()


def parse_reference(value: str, aliases: dict[str, str]) -> tuple[str, int, int, int]:
    match = REFERENCE.match(value)
    if not match:
        raise ValueError(f"无法解析经文引用：{value}")
    book_text, chapter_text, start_text, end_text = match.groups()
    code = aliases.get(normalize_alias(book_text))
    if code is None:
        raise ValueError(f"未知圣经书卷：{book_text}")
    chapter = int(chapter_text)
    start = int(start_text)
    end = int(end_text or start_text)
    if end < start:
        raise ValueError(f"经节范围倒置：{value}")
    return code, chapter, start, end


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--translation",
        action="append",
        default=[],
        help="Translation ID; repeat to compare versions. Default: cuv-s",
    )
    parser.add_argument("references", nargs="+")
    args = parser.parse_args()

    alias_document = json.loads((ROOT / "citation-aliases.json").read_text(encoding="utf-8"))
    aliases = alias_document["aliases"]
    translations = args.translation or ["cuv-s"]
    corpora = {}
    for translation in translations:
        path = ROOT / "versions" / translation / "verses.json"
        if not path.exists():
            raise SystemExit(f"未知译本：{translation}")
        corpora[translation] = json.loads(path.read_text(encoding="utf-8"))

    for reference in args.references:
        try:
            code, chapter, start, end = parse_reference(reference, aliases)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        for translation, corpus in corpora.items():
            chapter_map = corpus["books"].get(code, {}).get(str(chapter), {})
            verses = []
            for verse in range(start, end + 1):
                text = chapter_map.get(str(verse))
                if text is None:
                    raise SystemExit(f"{translation} 中没有 {code} {chapter}:{verse} 的独立记录")
                verses.append(f"{verse} {text}")
            print(f"[{translation}] {reference} ({code} {chapter}:{start}{f'-{end}' if end != start else ''})")
            print(" ".join(verses))


if __name__ == "__main__":
    main()
