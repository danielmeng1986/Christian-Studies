#!/usr/bin/env python3
"""Deterministic AI context assembly for the local reader."""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt


CONTEXT_SCHEMA_VERSION = 1
RETRIEVAL_VERSION = 1
SOURCE_REGISTRY_VERSION = 1

SCRIPT_ROOT = Path(__file__).resolve().parent
WEB_ROOT = SCRIPT_ROOT.parent
BOOK_ROOT = WEB_ROOT.parent
DEFAULT_BOOK_METADATA_PATH = BOOK_ROOT / "Metadata/book.yml"

KEY_RE = re.compile(r"\A[a-z][a-z0-9_]*\Z")
INTEGER_RE = re.compile(r"\A-?(?:0|[1-9]\d*)\Z")
FOOTNOTE_LINK_RE = re.compile(r"(?:^|/)Footnotes-\d{2}\.md#")

MARKDOWN_PARSER = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False, "typographer": False},
)


class ContextBuildError(ValueError):
    """Raised when declared context sources cannot be read deterministically."""


@dataclass(frozen=True)
class ContextBundle:
    envelope: dict[str, Any]
    manifest: dict[str, Any]
    preview: dict[str, Any]
    estimates: dict[str, Any]


@dataclass(frozen=True)
class ReadingBlock:
    block_id: str
    kind: str
    text: str
    heading_path: tuple[str, ...]


@dataclass(frozen=True)
class ContextRequest:
    book_id: str
    chapter_id: str
    chapter_title: str
    source_revision: str
    anchor: dict[str, Any]
    scriptures: list[dict[str, Any]]
    footnotes: list[dict[str, Any]]
    chapter_markdown: str
    prompt_version: int

    @classmethod
    def from_discussion(
        cls,
        document: dict[str, Any],
        chapter_markdown: str,
        *,
        prompt_version: int,
    ) -> ContextRequest:
        return cls(
            book_id=document["bookId"],
            chapter_id=document["chapterId"],
            chapter_title=document["context"]["chapterTitle"],
            source_revision=document["sourceRevision"],
            anchor=document["anchor"],
            scriptures=document["context"]["scriptures"],
            footnotes=document["context"]["footnotes"],
            chapter_markdown=chapter_markdown,
            prompt_version=prompt_version,
        )


def _parse_scalar(raw_value: str, field: str) -> Any:
    value = raw_value.strip()
    if not value:
        raise ContextBuildError(f"book metadata field {field} cannot be empty")
    if value in {"null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if INTEGER_RE.fullmatch(value):
        return int(value)
    if value.startswith("["):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            # YAML permits unquoted plain strings in flow-style lists.
            if not value.endswith("]"):
                raise ContextBuildError(f"book metadata field {field} has an invalid list") from error
            parsed = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        if not isinstance(parsed, list) or any(not isinstance(item, str) or not item for item in parsed):
            raise ContextBuildError(f"book metadata field {field} must be a list of strings")
        return parsed
    if value[0:1] in {'"', "'"}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ContextBuildError(f"book metadata field {field} has invalid quoting") from error
        if not isinstance(parsed, str):
            raise ContextBuildError(f"book metadata field {field} must be a string")
        return parsed
    if value.startswith(("{", "|", ">", "&", "*", "!")):
        raise ContextBuildError(f"book metadata field {field} uses unsupported YAML syntax")
    return value


def load_book_metadata(path: Path) -> dict[str, Any]:
    """Read the repository's intentionally flat YAML metadata without guessing fields."""

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContextBuildError(f"book metadata could not be read: {path}") from error

    raw: dict[str, Any] = {}
    for line_number, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line != line.lstrip():
            raise ContextBuildError(f"book metadata line {line_number} must not be nested")
        key, separator, value = line.partition(":")
        key = key.strip()
        if not separator or not KEY_RE.fullmatch(key):
            raise ContextBuildError(f"book metadata line {line_number} is invalid")
        if key in raw:
            raise ContextBuildError(f"book metadata field {key} is duplicated")
        raw[key] = _parse_scalar(value, key)

    field_map = {
        "book_id": "bookId",
        "display_title": "displayTitle",
        "title": "title",
        "subtitle": "subtitle",
        "author": "author",
        "publisher": "publisher",
        "publication_year": "publicationYear",
        "language": "language",
        "tags": "tags",
    }
    required = set(field_map)
    missing = sorted(required - set(raw))
    if missing:
        raise ContextBuildError(f"book metadata is missing: {', '.join(missing)}")

    result = {target: raw[source] for source, target in field_map.items()}
    for field in ("bookId", "displayTitle", "title", "subtitle", "author", "publisher", "language"):
        if not isinstance(result[field], str) or not result[field].strip():
            raise ContextBuildError(f"book metadata field {field} must be a non-empty string")
    if not isinstance(result["publicationYear"], int) or isinstance(result["publicationYear"], bool):
        raise ContextBuildError("book metadata field publicationYear must be an integer")
    if not isinstance(result["tags"], list) or any(not isinstance(tag, str) or not tag for tag in result["tags"]):
        raise ContextBuildError("book metadata field tags must be a list of strings")
    return result


def _inline_text(children: list[Any]) -> str:
    parts: list[str] = []
    skipped_links = 0
    for token in children:
        if token.type == "link_open":
            href = token.attrGet("href") or ""
            if skipped_links or FOOTNOTE_LINK_RE.search(href):
                skipped_links += 1
            continue
        if token.type == "link_close":
            if skipped_links:
                skipped_links -= 1
            continue
        if skipped_links:
            continue
        if token.type in {"text", "code_inline"}:
            parts.append(token.content)
        elif token.type in {"softbreak", "hardbreak"}:
            parts.append("\n")
        # Images have no DOM text node; their alt text must not affect anchors.
    return "".join(parts)


def build_block_map(chapter_markdown: str, chapter_id: str) -> list[ReadingBlock]:
    """Reproduce build.py block IDs and the browser's canonical selectable text."""

    tokens = MARKDOWN_PARSER.parse(chapter_markdown)
    blocks: list[ReadingBlock] = []
    heading_stack: list[str] = []
    block_index = 0

    for index, token in enumerate(tokens):
        if token.type not in {"heading_open", "paragraph_open"}:
            continue
        block_index += 1
        tag = token.tag if token.tag in {"h1", "h2"} else "p"
        inline = tokens[index + 1] if index + 1 < len(tokens) and tokens[index + 1].type == "inline" else None
        text = _inline_text(inline.children or []) if inline is not None else ""

        if token.type == "heading_open":
            level = int(token.tag[1:]) if token.tag.startswith("h") and token.tag[1:].isdigit() else 2
            if level <= 1:
                heading_stack = [text]
            else:
                # The current reader emits h1/h2, but this remains deterministic for future deeper headings.
                heading_stack = heading_stack[: max(1, level - 1)]
                heading_stack.append(text)
            heading_path = tuple(heading_stack)
            kind = "heading"
        else:
            heading_path = tuple(heading_stack)
            kind = "paragraph"

        blocks.append(
            ReadingBlock(
                block_id=f"{chapter_id}-{tag}-{block_index:04d}",
                kind=kind,
                text=text,
                heading_path=heading_path,
            )
        )
    return blocks


def _utf16_slice(text: str, start_offset: int, end_offset: int) -> str:
    encoded = text.encode("utf-16-le")
    if start_offset < 0 or end_offset < start_offset or end_offset * 2 > len(encoded):
        raise ContextBuildError("selection offsets are outside the selected block")
    try:
        return encoded[start_offset * 2 : end_offset * 2].decode("utf-16-le")
    except UnicodeDecodeError as error:
        raise ContextBuildError("selection offsets split a Unicode character") from error


def resolve_reading_focus(chapter_markdown: str, chapter_id: str, anchor: dict[str, Any]) -> dict[str, Any]:
    blocks = build_block_map(chapter_markdown, chapter_id)
    selected_index = next((index for index, block in enumerate(blocks) if block.block_id == anchor["blockId"]), None)
    if selected_index is None:
        raise ContextBuildError("selection block does not exist in the current chapter")

    selected = blocks[selected_index]
    actual = _utf16_slice(selected.text, anchor["startOffset"], anchor["endOffset"])
    if actual != anchor["exact"]:
        raise ContextBuildError("selection text does not match the current chapter block")

    prefix_length = len(anchor.get("prefix", "").encode("utf-16-le")) // 2
    suffix_length = len(anchor.get("suffix", "").encode("utf-16-le")) // 2
    actual_prefix = _utf16_slice(
        selected.text,
        max(0, anchor["startOffset"] - prefix_length),
        anchor["startOffset"],
    )
    actual_suffix = _utf16_slice(
        selected.text,
        anchor["endOffset"],
        min(len(selected.text.encode("utf-16-le")) // 2, anchor["endOffset"] + suffix_length),
    )
    if actual_prefix != anchor.get("prefix", "") or actual_suffix != anchor.get("suffix", ""):
        raise ContextBuildError("selection context does not match the current chapter block")

    paragraph_indexes = [index for index, block in enumerate(blocks) if block.kind == "paragraph" and block.text]
    previous_index = next((index for index in reversed(paragraph_indexes) if index < selected_index), None)
    next_index = next((index for index in paragraph_indexes if index > selected_index), None)

    def block_value(index: int | None) -> dict[str, str] | None:
        if index is None:
            return None
        block = blocks[index]
        return {"blockId": block.block_id, "text": block.text}

    return {
        "headingPath": list(selected.heading_path),
        "previousBlock": block_value(previous_index),
        "selectedBlock": {
            "blockId": selected.block_id,
            "kind": selected.kind,
            "text": selected.text,
        },
        "selection": {
            "blockId": anchor["blockId"],
            "exact": anchor["exact"],
            "startOffset": anchor["startOffset"],
            "endOffset": anchor["endOffset"],
        },
        "nextBlock": block_value(next_index),
    }


class ContextBuilder:
    """Build a versioned evidence envelope without network access or filesystem writes."""

    def __init__(self, metadata_path: Path = DEFAULT_BOOK_METADATA_PATH) -> None:
        self.metadata_path = metadata_path

    def build(self, request: ContextRequest) -> ContextBundle:
        book = load_book_metadata(self.metadata_path)
        if request.book_id != book["bookId"]:
            raise ContextBuildError("discussion bookId does not match book metadata")

        chapter_revision = hashlib.sha256(request.chapter_markdown.encode("utf-8")).hexdigest()
        scriptures = request.scriptures
        footnotes = request.footnotes
        anchor = request.anchor
        focus = resolve_reading_focus(request.chapter_markdown, request.chapter_id, anchor)

        manifest = {
            "contextSchemaVersion": CONTEXT_SCHEMA_VERSION,
            "promptVersion": request.prompt_version,
            "retrievalVersion": RETRIEVAL_VERSION,
            "sourceRegistryVersion": SOURCE_REGISTRY_VERSION,
            "chapterRevision": chapter_revision,
            "included": {
                "scriptureIds": [item["id"] for item in scriptures],
                "footnoteIds": [item["id"] for item in footnotes],
                "noteIds": [],
                "translationSourceLines": [],
                "bookPassages": [],
                "localSourceChunks": [],
                "webSources": [],
            },
            "capabilities": {
                "localLibrary": False,
                "crossChapterSearch": False,
                "webSearch": False,
                "researchDepth": "local",
            },
        }

        envelope = {
            "contextSchemaVersion": CONTEXT_SCHEMA_VERSION,
            "book": book,
            "chapter": {
                "chapterId": request.chapter_id,
                "chapterTitle": request.chapter_title,
                "sourceRevision": request.source_revision,
                "currentSourceRevision": chapter_revision,
                "sourceChanged": chapter_revision != request.source_revision,
            },
            "focus": focus,
            "primarySources": {
                "chapterMarkdown": request.chapter_markdown,
                "scriptures": scriptures,
                "footnotes": footnotes,
            },
            "personalStudy": {"notes": []},
            "referenceResolution": {"entities": [], "terms": []},
            "retrieval": {
                "bookPassages": [],
                "localSourceChunks": [],
                "bibliographyMatches": [],
            },
            "externalResearch": {"enabled": False, "mode": "off", "sources": []},
            "capabilities": manifest["capabilities"],
            "manifest": manifest,
        }
        preview = {
            "chapterTitle": request.chapter_title,
            "headingPath": focus["headingPath"],
            "selection": anchor["exact"],
            "scriptureCount": len(scriptures),
            "footnoteCount": len(footnotes),
            "webSearchEnabled": False,
        }
        evidence_characters = len(request.chapter_markdown) + len(anchor["exact"])
        evidence_characters += sum(len(item["text"]) for item in scriptures)
        evidence_characters += sum(len(item["text"]) for item in footnotes)
        estimates = {
            "method": "characters",
            "evidenceCharacters": evidence_characters,
            "tokenEstimate": None,
        }
        return ContextBundle(envelope=envelope, manifest=manifest, preview=preview, estimates=estimates)
