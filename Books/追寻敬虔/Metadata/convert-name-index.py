#!/usr/bin/env python3
"""Convert the legacy QFG translation index into Markdown and lookup JSON."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


BOOK_ROOT = Path(__file__).resolve().parents[1]
SOURCE = BOOK_ROOT / "QFG ?? 與譯名對照表  extension.doc"
MARKDOWN_OUTPUT = BOOK_ROOT / "References/追寻敬虔译名对照表.md"
JSON_OUTPUT = BOOK_ROOT / "References/追寻敬虔译名对照表.json"

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
PAGE_SUFFIX_RE = re.compile(r"(?:,?\s+|,\s*)\d+(?:\s*,\s*\d+)*\.?\s*$")
SECTION_RE = re.compile(r"[A-Z]")
FOOTER_START = "THOMAS GOODWIN (1600-1680) ON THE CHRISTIAN LIFE"


def extract_text() -> str:
    completed = subprocess.run(
        ["/usr/bin/textutil", "-convert", "txt", "-stdout", str(SOURCE)],
        check=True,
        stdout=subprocess.PIPE,
    )
    return (
        completed.stdout.decode("utf-8")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\uf0e0", "→")
    )


def display_line(line: str) -> str:
    indent = len(line) - len(line.lstrip("\t"))
    content = re.sub(r"\t+", " — ", line.strip())
    return f"{'  ' * indent}- {content}"


def build_markdown(lines: list[str]) -> str:
    output = [
        "---",
        "book: 追寻敬虔",
        f'source_file: "{SOURCE.name}"',
        "document_type: translation-index",
        "---",
        "",
        "# 追寻敬虔译名对照表",
        "",
        f"> 来源：`{SOURCE.name}`。",
        "> 本文件完整转录原 Word 索引；制表符改为破折号或嵌套项目，旧字体箭头恢复为 `→`，原有繁体译名、拼写、标点、页码与交叉引用均予保留。",
        "> 供程序查询的精简中英文映射见 [`追寻敬虔译名对照表.json`](追寻敬虔译名对照表.json)。",
        "",
        "## 原稿说明",
        "",
    ]
    in_footer = False
    in_appendix = False
    seen_section = False
    for raw_line in lines[1:]:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == FOOTER_START:
            in_footer = True
            output.extend(["", "## 原文件附带页脚文字", "", "```text", stripped])
            continue
        if in_footer:
            output.append(stripped)
            continue
        if SECTION_RE.fullmatch(stripped):
            seen_section = True
            output.extend(["", f"## {stripped}", ""])
            continue
        if stripped in {"===", "!!!"}:
            if not in_appendix:
                in_appendix = True
                output.extend(["", "## 附录", ""])
            continue
        if stripped == "常用譯名":
            output.extend(["", "### 常用譯名", ""])
            continue
        if seen_section or in_appendix:
            output.append(display_line(line))
        else:
            output.append(f"- {re.sub(r'\t+', ' — ', stripped)}")
    if in_footer:
        output.append("```")
    return "\n".join(output).rstrip() + "\n"


def clean_english(value: str) -> str:
    previous = None
    result = value.strip()
    while result != previous:
        previous = result
        result = PAGE_SUFFIX_RE.sub("", result).rstrip()
    return result.rstrip(" ,\t【")


def build_lookup(lines: list[str]) -> dict:
    entries = []
    section = ""
    in_index = False
    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if SECTION_RE.fullmatch(stripped):
            section = stripped
            in_index = True
            continue
        if stripped == FOOTER_START:
            break
        if stripped in {"===", "!!!"}:
            section = "appendix"
            continue
        if not in_index or stripped in {"", "常用譯名"}:
            continue
        match = CJK_RE.search(stripped)
        if match is None:
            continue
        english = clean_english(stripped[: match.start()])
        chinese = stripped[match.start() :].strip()
        if not english or not chinese:
            continue
        entries.append(
            {
                "english": english,
                "chinese": chinese,
                "section": section,
                "sourceLine": line_number,
                "sourceText": stripped,
            }
        )
    return {
        "schemaVersion": 1,
        "book": "追寻敬虔",
        "sourceFile": SOURCE.name,
        "description": "从原译名索引中抽取的明确中英文对应条目；原始 Word 和 Markdown 转录仍是内容依据。",
        "entryCount": len(entries),
        "entries": entries,
    }


def main() -> None:
    lines = extract_text().splitlines()
    MARKDOWN_OUTPUT.write_text(build_markdown(lines), encoding="utf-8")
    JSON_OUTPUT.write_text(
        json.dumps(build_lookup(lines), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {MARKDOWN_OUTPUT}")
    print(f"Wrote {JSON_OUTPUT}")


if __name__ == "__main__":
    main()
