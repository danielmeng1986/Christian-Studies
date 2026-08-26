#!/usr/bin/env python3
"""Convert one 《追寻敬虔》 chapter from the legacy Word draft to Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def qn(name: str) -> str:
    return f"{{{W}}}{name}"


def wattr(node, name: str, default: str = "") -> str:
    return node.get(qn(name), default) if node is not None else default


CHAPTER_NUMERALS = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七",
    8: "八", 9: "九", 10: "十", 11: "十一", 12: "十二", 13: "十三",
    14: "十四", 15: "十五", 16: "十六", 17: "十七", 18: "十八",
    19: "十九", 20: "二十",
}


@dataclass
class NoteLabel:
    word_id: str
    display: str
    anchor: str
    heading: str
    custom: bool


class WordDocument:
    def __init__(self, path: Path):
        with zipfile.ZipFile(path) as archive:
            self.document = etree.fromstring(archive.read("word/document.xml"))
            self.styles_root = etree.fromstring(archive.read("word/styles.xml"))
            self.footnotes_root = (
                etree.fromstring(archive.read("word/footnotes.xml"))
                if "word/footnotes.xml" in archive.namelist() else None
            )
        self.paragraphs = self.document.xpath("//w:body/w:p", namespaces=NS)
        self.styles = self._load_styles()
        self.footnotes = self._load_footnotes()

    def _load_styles(self):
        styles = {}
        for style in self.styles_root.xpath("//w:style", namespaces=NS):
            style_id = wattr(style, "styleId")
            name = style.find("w:name", NS)
            based = style.find("w:basedOn", NS)
            styles[style_id] = {
                "name": wattr(name, "val", style_id),
                "based_on": wattr(based, "val"),
                "italic": style.find("w:rPr/w:i", NS) is not None,
                "bold": style.find("w:rPr/w:b", NS) is not None,
            }
        return styles

    def _load_footnotes(self):
        if self.footnotes_root is None:
            return {}
        result = {}
        for note in self.footnotes_root.xpath("//w:footnote", namespaces=NS):
            word_id = wattr(note, "id")
            if word_id and not word_id.startswith("-"):
                result[word_id] = note
        return result

    def style_name(self, paragraph) -> str:
        style = paragraph.find("w:pPr/w:pStyle", NS)
        style_id = wattr(style, "val")
        return self.styles.get(style_id, {}).get("name", style_id or "Normal")

    @staticmethod
    def plain_text(node) -> str:
        return "".join(node.xpath(".//w:t/text()", namespaces=NS))

    def run_format(self, run) -> tuple[bool, bool]:
        rpr = run.find("w:rPr", NS)
        style_id = wattr(rpr.find("w:rStyle", NS), "val") if rpr is not None else ""
        style = self.styles.get(style_id, {})
        italic = bool(rpr is not None and rpr.find("w:i", NS) is not None) or style.get("italic", False)
        bold = bool(rpr is not None and rpr.find("w:b", NS) is not None) or style.get("bold", False)
        return italic, bold

    @staticmethod
    def run_text(run) -> str:
        parts = []
        for node in run.iter():
            if node.tag == qn("t"):
                parts.append(node.text or "")
            elif node.tag == qn("tab"):
                parts.append("\t")
            elif node.tag in {qn("br"), qn("cr")}:
                parts.append("\n")
        return "".join(parts)


def convert_doc(source: Path, soffice: str | None) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    if source.suffix.lower() == ".docx":
        return source, None
    office = soffice or shutil.which("soffice") or shutil.which("libreoffice")
    if not office:
        raise SystemExit("Cannot convert .doc: make soffice available on PATH or pass --soffice.")
    temp = tempfile.TemporaryDirectory(prefix="qfg-word-")
    root = Path(temp.name)
    home = root / "home"
    profile = root / "profile"
    home.mkdir()
    profile.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    subprocess.run(
        [office, "--headless", f"-env:UserInstallation={profile.as_uri()}",
         "--convert-to", "docx", "--outdir", str(root), str(source)],
        check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    output = root / f"{source.stem}.docx"
    if not output.exists():
        raise SystemExit(f"Conversion succeeded without producing {output}")
    return output, temp


def chapter_range(doc: WordDocument, chapter: int) -> tuple[int, int]:
    target = f"第{CHAPTER_NUMERALS[chapter]}章"
    start = None
    for index, paragraph in enumerate(doc.paragraphs):
        if doc.style_name(paragraph).lower() == "heading 1" and doc.plain_text(paragraph).strip() == target:
            start = index
            break
    if start is None:
        raise SystemExit(f"Chapter marker not found: {target}")
    boundary = re.compile(r"^第.+(?:章|部份|部分)(?:[﹕:：].*)?$")
    end = len(doc.paragraphs)
    for index in range(start + 2, len(doc.paragraphs)):
        paragraph = doc.paragraphs[index]
        if doc.style_name(paragraph).lower() == "heading 1" and boundary.match(doc.plain_text(paragraph).strip()):
            end = index
            break
    return start, end


def note_labels(doc: WordDocument, paragraphs) -> tuple[dict[str, NoteLabel], list[NoteLabel]]:
    labels: dict[str, NoteLabel] = {}
    ordered: list[NoteLabel] = []
    number = translator = 0
    for paragraph in paragraphs:
        for ref in paragraph.xpath(".//w:footnoteReference", namespaces=NS):
            word_id = wattr(ref, "id")
            if word_id in labels:
                continue
            run = ref.getparent()
            custom = wattr(ref, "customMarkFollows") in {"1", "true", "on"}
            if custom:
                translator += 1
                note_text = doc.plain_text(doc.footnotes.get(word_id)).lstrip() if word_id in doc.footnotes else ""
                marker_match = re.match(r"(\*+|\++)", note_text)
                mark = marker_match.group(1) if marker_match else (doc.run_text(run).strip() or "*")
                label = NoteLabel(word_id, mark, f"译者注{translator}", f"译者注{translator}", True)
            else:
                number += 1
                text = str(number)
                label = NoteLabel(word_id, text, text, text, False)
            labels[word_id] = label
            ordered.append(label)
    return labels, ordered


def wrap_text(text: str, italic: bool, bold: bool) -> str:
    if not text:
        return ""
    if bold and italic:
        return f"***{text}***"
    if bold:
        return f"**{text}**"
    if italic:
        return f"*{text}*"
    return text


def paragraph_markdown(doc: WordDocument, paragraph, labels: dict[str, NoteLabel], footnote_href: str) -> str:
    segments: list[tuple[str, bool, bool]] = []
    for run in paragraph.xpath(".//w:r", namespaces=NS):
        refs = run.xpath(".//w:footnoteReference", namespaces=NS)
        if refs:
            label = labels[wattr(refs[0], "id")]
            segments.append((f"[{label.display}]({footnote_href}#{label.anchor})", False, False))
            continue
        rpr = run.find("w:rPr", NS)
        run_style = wattr(rpr.find("w:rStyle", NS), "val") if rpr is not None else ""
        if run_style in {"FootnoteCharacters", "FootnoteReference"}:
            continue
        text = doc.run_text(run)
        if not text:
            continue
        italic, bold = doc.run_format(run)
        if segments and segments[-1][1:] == (italic, bold):
            previous = segments[-1]
            segments[-1] = (previous[0] + text, italic, bold)
        else:
            segments.append((text, italic, bold))
    rendered = "".join(wrap_text(*segment) for segment in segments)
    rendered = re.sub(r"^\s+", "", rendered)
    rendered = rendered.replace("\t", " ")
    rendered = re.sub(r"[ ]{2,}", " ", rendered)
    return rendered.strip()


def source_text_without_notes(doc: WordDocument, paragraph) -> str:
    parts = []
    for run in paragraph.xpath(".//w:r", namespaces=NS):
        if run.xpath(".//w:footnoteReference", namespaces=NS):
            continue
        rpr = run.find("w:rPr", NS)
        run_style = wattr(rpr.find("w:rStyle", NS), "val") if rpr is not None else ""
        if run_style in {"FootnoteCharacters", "FootnoteReference"}:
            continue
        parts.append(doc.run_text(run))
    text = "".join(parts).replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()


def rendered_text_without_notes(text: str) -> str:
    text = re.sub(r"\[[^]]+\]\([^)]*\)", "", text)
    text = text.replace("***", "").replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def footnote_markdown(doc: WordDocument, note, label: NoteLabel) -> str:
    paragraphs = []
    for paragraph in note.xpath("./w:p", namespaces=NS):
        text = paragraph_markdown(doc, paragraph, {}, "") if not paragraph.xpath(".//w:footnoteReference", namespaces=NS) else doc.plain_text(paragraph)
        if text.strip():
            paragraphs.append(text.strip())
    body = "\n\n".join(paragraphs).strip()
    if label.custom:
        body = re.sub(r"^\s*" + re.escape(label.display) + r"\s*", "", body, count=1)
    return body


def build_markdown(doc: WordDocument, chapter: int, output: Path, footnotes: Path):
    start, end = chapter_range(doc, chapter)
    paragraphs = doc.paragraphs[start:end]
    labels, ordered_notes = note_labels(doc, paragraphs)
    href = Path(os.path.relpath(footnotes, output.parent)).as_posix()
    chapter_label = doc.plain_text(paragraphs[0]).strip()
    title = doc.plain_text(paragraphs[1]).strip()
    blocks = [
        "---\n"
        "book: 追寻敬虔\n"
        f"chapter: {chapter:02d}\n"
        "source_file: Original/QFG Draft 20170911 20211005.doc\n"
        f"source_location: \"{chapter_label}（源文件未提供稳定页码标记）\"\n"
        "---",
        f"# {chapter_label}：{title}",
        f"> 来源定位：原始文档 {chapter_label}（未提供稳定页码标记）。",
    ]
    style_counts: dict[str, int] = {}
    text_mismatches = []
    quote_buffer: list[str] = []

    def flush_quotes():
        nonlocal quote_buffer
        if quote_buffer:
            blocks.append("\n".join(quote_buffer))
            quote_buffer = []

    for offset, paragraph in enumerate(paragraphs[2:], start=2):
        style = doc.style_name(paragraph)
        style_key = style.lower()
        text = paragraph_markdown(doc, paragraph, labels, href)
        if not text:
            if quote_buffer:
                quote_buffer.append(">")
            continue
        style_counts[style] = style_counts.get(style, 0) + 1
        expected = source_text_without_notes(doc, paragraph)
        actual = rendered_text_without_notes(text)
        if expected != actual:
            text_mismatches.append({"word_paragraph": start + offset, "expected": expected, "actual": actual})
        if style == "內文縮排":
            quote_buffer.append(f"> {text}")
            continue
        flush_quotes()
        if style_key == "heading 1":
            blocks.append(f"# {text}")
        elif style_key == "heading 2":
            blocks.append(f"## {text}")
        elif style_key == "heading 3":
            blocks.append(f"### {text}")
        elif style_key == "heading 4":
            blocks.append(f"#### {text}")
        else:
            blocks.append(text)
    flush_quotes()
    chapter_md = "\n\n".join(blocks).rstrip() + "\n"

    note_blocks = [f"# Footnotes-{chapter:02d}"]
    footnote_text_mismatches = []
    for label in ordered_notes:
        note = doc.footnotes.get(label.word_id)
        if note is None:
            raise SystemExit(f"Missing footnote body for Word footnote id {label.word_id}")
        body = footnote_markdown(doc, note, label)
        expected_note = [
            source_text_without_notes(doc, paragraph)
            for paragraph in note.xpath("./w:p", namespaces=NS)
            if source_text_without_notes(doc, paragraph)
        ]
        actual_note = [rendered_text_without_notes(part) for part in body.split("\n\n") if part.strip()]
        if expected_note != actual_note:
            footnote_text_mismatches.append(
                {"word_footnote_id": label.word_id, "expected": expected_note, "actual": actual_note}
            )
        note_blocks.append(f"## {label.heading}\n\n{body}")
    footnote_md = "\n\n".join(note_blocks).rstrip() + "\n"
    audit = {
        "chapter": chapter,
        "word_paragraph_range": [start, end],
        "source_paragraphs": len(paragraphs),
        "style_counts_excluding_title_and_blanks": style_counts,
        "footnote_references": len(ordered_notes),
        "numbered_footnotes": sum(not label.custom for label in ordered_notes),
        "translator_footnotes": sum(label.custom for label in ordered_notes),
        "chapter_title": f"{chapter_label}：{title}",
        "paragraph_text_mismatches": text_mismatches,
        "footnote_text_mismatches": footnote_text_mismatches,
    }
    return chapter_md, footnote_md, audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--chapter", type=int, required=True, choices=range(1, 21))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--footnotes", type=Path, required=True)
    parser.add_argument("--soffice")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    docx, temp = convert_doc(args.source.resolve(), args.soffice)
    try:
        doc = WordDocument(docx)
        chapter_md, footnote_md, audit = build_markdown(
            doc, args.chapter, args.output.resolve(), args.footnotes.resolve()
        )
        if not args.audit_only:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.footnotes.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(chapter_md, encoding="utf-8")
            args.footnotes.write_text(footnote_md, encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == "__main__":
    main()
