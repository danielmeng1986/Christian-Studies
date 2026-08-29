#!/usr/bin/env python3
"""Deterministic AI context assembly for the local reader."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt


CONTEXT_SCHEMA_VERSION = 1
RETRIEVAL_VERSION = 3
SOURCE_REGISTRY_VERSION = 1

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
WEB_ROOT = SCRIPT_ROOT.parent
BOOK_ROOT = WEB_ROOT.parent
DEFAULT_BOOK_METADATA_PATH = BOOK_ROOT / "Metadata/book.yml"
DEFAULT_TRANSLATION_INDEX_PATH = BOOK_ROOT / "References/追寻敬虔译名对照表.json"
DEFAULT_READING_ROOT = BOOK_ROOT / "Reading"
DEFAULT_FOOTNOTE_ROOT = BOOK_ROOT / "References"

KEY_RE = re.compile(r"\A[a-z][a-z0-9_]*\Z")
INTEGER_RE = re.compile(r"\A-?(?:0|[1-9]\d*)\Z")
FOOTNOTE_LINK_RE = re.compile(r"(?:^|/)Footnotes-\d{2}\.md#")
CHAPTER_META_RE = re.compile(r"^chapter:\s*(?P<chapter>\d{2})\s*$", re.MULTILINE)

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
    question: str = ""
    note_document: dict[str, Any] | None = None
    excluded_note_ids: frozenset[str] = frozenset()
    included_translation_source_lines: frozenset[int] = frozenset()
    excluded_translation_source_lines: frozenset[int] = frozenset()
    excluded_book_passage_ids: frozenset[str] = frozenset()
    book_passage_limit: int = 5
    included_local_chunk_ids: frozenset[str] = frozenset()

    @classmethod
    def from_discussion(
        cls,
        document: dict[str, Any],
        chapter_markdown: str,
        *,
        prompt_version: int,
        note_document: dict[str, Any] | None = None,
        excluded_note_ids: frozenset[str] = frozenset(),
        included_translation_source_lines: frozenset[int] = frozenset(),
        excluded_translation_source_lines: frozenset[int] = frozenset(),
        excluded_book_passage_ids: frozenset[str] = frozenset(),
        book_passage_limit: int = 5,
        included_local_chunk_ids: frozenset[str] = frozenset(),
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
            question=next(
                (
                    message["content"]
                    for message in reversed(document["messages"])
                    if message["role"] == "user" and message["status"] == "completed"
                ),
                "",
            ),
            note_document=note_document,
            excluded_note_ids=excluded_note_ids,
            included_translation_source_lines=included_translation_source_lines,
            excluded_translation_source_lines=excluded_translation_source_lines,
            excluded_book_passage_ids=excluded_book_passage_ids,
            book_passage_limit=book_passage_limit,
            included_local_chunk_ids=included_local_chunk_ids,
        )


def resolve_note_evidence(
    note_document: dict[str, Any] | None,
    chapter_id: str,
    selection: dict[str, Any],
    excluded_note_ids: frozenset[str] = frozenset(),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Classify validated chapter notes without reading or mutating their source."""

    if note_document is None:
        return [], []
    if note_document.get("bookId") != "qfg" or note_document.get("chapterId") != chapter_id:
        raise ContextBuildError("note document does not match the current chapter")
    notes = note_document.get("notes")
    if not isinstance(notes, list):
        raise ContextBuildError("note document notes must be an array")

    included: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for note in notes:
        anchor = note.get("anchor", {})
        if anchor.get("blockId") != selection["blockId"]:
            continue
        same_range = (
            anchor.get("startOffset") == selection["startOffset"]
            and anchor.get("endOffset") == selection["endOffset"]
            and anchor.get("exact") == selection["exact"]
        )
        overlaps = (
            isinstance(anchor.get("startOffset"), int)
            and isinstance(anchor.get("endOffset"), int)
            and anchor["startOffset"] < selection["endOffset"]
            and anchor["endOffset"] > selection["startOffset"]
        )
        relation = "exact" if same_range else "overlap" if overlaps else "sameBlock"
        evidence = {
            "evidenceType": "user_note",
            "relation": relation,
            "noteId": note.get("id"),
            "body": note.get("body"),
            "sourceRevision": note.get("sourceRevision"),
            "updatedAt": note.get("updatedAt"),
        }
        if relation in {"exact", "overlap"} and evidence["noteId"] not in excluded_note_ids:
            included.append(evidence)
        else:
            evidence["includedByDefault"] = relation in {"exact", "overlap"}
            evidence["excluded"] = evidence["noteId"] in excluded_note_ids
            candidates.append(evidence)
    return included, candidates


def _search_normalize(value: str, *, strip_punctuation: bool = False) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.translate(str.maketrans({"·": ".", "‧": ".", "・": ".", "．": "."}))
    if strip_punctuation:
        normalized = "".join(character if character.isalnum() else " " for character in normalized)
    return " ".join(normalized.split())


def _canonical_english_name(value: str) -> str:
    family, separator, given = value.partition(",")
    return f"{given.strip()} {family.strip()}" if separator and given.strip() else value.strip()


def load_translation_index(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ContextBuildError(f"translation index could not be read: {path}") from error
    entries = value.get("entries") if isinstance(value, dict) else None
    if not isinstance(entries, list):
        raise ContextBuildError("translation index entries must be an array")
    return entries


def resolve_translation_entities(
    entries: list[dict[str, Any]], focus: dict[str, Any], question: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve deterministic exact/alias matches; retain ambiguity as candidates."""

    primary_texts = [focus["selection"]["exact"], question, *focus["headingPath"]]
    neighboring_texts = [
        block["text"] for block in (focus.get("previousBlock"), focus.get("nextBlock")) if block
    ]

    def matches(texts: list[str]) -> list[tuple[dict[str, Any], str, str]]:
        found: list[tuple[dict[str, Any], str, str]] = []
        normalized_text = "\n".join(_search_normalize(text) for text in texts if text)
        loose_text = _search_normalize("\n".join(texts), strip_punctuation=True)
        for entry in entries:
            english = entry.get("english")
            chinese = entry.get("chinese")
            if not isinstance(english, str) or not isinstance(chinese, str):
                continue
            canonical = _canonical_english_name(english)
            variants = ((chinese, "exact"), (english, "exact"), (canonical, "alias"))
            for surface, match_type in variants:
                needle = _search_normalize(surface)
                if needle and needle in normalized_text:
                    found.append((entry, surface, match_type))
                    break
            else:
                for surface in (chinese, english, canonical):
                    needle = _search_normalize(surface, strip_punctuation=True)
                    if needle and len(needle) >= 4 and needle in loose_text:
                        found.append((entry, surface, "candidate"))
                        break
        return found

    found = matches(primary_texts)
    if not found:
        found = matches(neighboring_texts)

    grouped: dict[str, list[tuple[dict[str, Any], str, str]]] = {}
    for item in found:
        grouped.setdefault(_search_normalize(item[1], strip_punctuation=True), []).append(item)

    entities: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    seen_lines: set[int] = set()
    for items in grouped.values():
        ambiguous = len({item[0].get("sourceLine") for item in items}) > 1
        for entry, surface, match_type in items:
            source_line = entry.get("sourceLine")
            if source_line in seen_lines:
                continue
            seen_lines.add(source_line)
            effective_type = "candidate" if ambiguous else match_type
            result = {
                "evidenceType": "translation_index_match",
                "surface": surface,
                "canonicalSearchName": _canonical_english_name(entry["english"]),
                "indexForm": entry["english"],
                "english": entry["english"],
                "chinese": entry["chinese"],
                "matchType": effective_type,
                "sourceLine": source_line,
            }
            (candidates if effective_type == "candidate" else entities).append(result)
    return entities, candidates


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


def discover_retrieval_paths(
    reading_root: Path = DEFAULT_READING_ROOT,
    footnote_root: Path = DEFAULT_FOOTNOTE_ROOT,
) -> tuple[dict[str, Path], dict[str, Path]]:
    """Discover declared book sources without importing HTTP or discussion code."""

    chapter_paths: dict[str, Path] = {}
    try:
        candidates = sorted(reading_root.rglob("*.md"))
    except OSError as error:
        raise ContextBuildError(f"reading sources could not be listed: {reading_root}") from error
    for path in candidates:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise ContextBuildError(f"chapter source could not be read: {path}") from error
        match = CHAPTER_META_RE.search(source)
        if match is None:
            continue
        chapter_id = match.group("chapter")
        if chapter_id in chapter_paths:
            raise ContextBuildError(f"duplicate chapter source: {chapter_id}")
        chapter_paths[chapter_id] = path
    footnote_paths = {
        chapter_id: footnote_root / f"Footnotes-{chapter_id}.md"
        for chapter_id in chapter_paths
    }
    return chapter_paths, footnote_paths


class ContextBuilder:
    """Build a versioned evidence envelope without network access or filesystem writes."""

    def __init__(
        self,
        metadata_path: Path = DEFAULT_BOOK_METADATA_PATH,
        translation_index_path: Path = DEFAULT_TRANSLATION_INDEX_PATH,
        *,
        chapter_paths: dict[str, Path] | None = None,
        footnote_paths: dict[str, Path] | None = None,
        local_library: Any | None = None,
    ) -> None:
        self.metadata_path = metadata_path
        self.translation_index_path = translation_index_path
        if chapter_paths is None:
            chapter_paths, discovered_footnotes = discover_retrieval_paths()
            if footnote_paths is None:
                footnote_paths = discovered_footnotes
        self.chapter_paths = dict(chapter_paths)
        self.footnote_paths = dict(footnote_paths or {})
        self.local_library = local_library

    def build(self, request: ContextRequest) -> ContextBundle:
        if request.book_passage_limit not in {5, 10}:
            raise ContextBuildError("book passage limit must be 5 or 10")
        book = load_book_metadata(self.metadata_path)
        if request.book_id != book["bookId"]:
            raise ContextBuildError("discussion bookId does not match book metadata")

        chapter_revision = hashlib.sha256(request.chapter_markdown.encode("utf-8")).hexdigest()
        scriptures = request.scriptures
        footnotes = request.footnotes
        anchor = request.anchor
        focus = resolve_reading_focus(request.chapter_markdown, request.chapter_id, anchor)
        notes, note_candidates = resolve_note_evidence(
            request.note_document, request.chapter_id, focus["selection"], request.excluded_note_ids
        )
        default_entities, entity_candidates = resolve_translation_entities(
            load_translation_index(self.translation_index_path), focus, request.question
        )
        entities = [
            item
            for item in default_entities
            if item["sourceLine"] not in request.excluded_translation_source_lines
        ]
        entities.extend(
            item
            for item in entity_candidates
            if item["sourceLine"] in request.included_translation_source_lines
        )

        try:
            from context_retrieval import build_retrieval_units, retrieve_book_passages

            retrieval_units = build_retrieval_units(
                self.chapter_paths,
                self.footnote_paths,
                build_block_map,
            )
            passage_candidates = retrieve_book_passages(
                retrieval_units,
                current_chapter_id=request.chapter_id,
                selected_block_id=focus["selection"]["blockId"],
                question=request.question,
                selection=focus["selection"]["exact"],
                entities=entities,
                scripture_ids=(item.get("id", "") for item in scriptures),
                limit=request.book_passage_limit + 1,
            )
        except (OSError, ValueError) as error:
            raise ContextBuildError(str(error)) from error
        has_more_book_passages = len(passage_candidates) > request.book_passage_limit
        book_passages = [
            passage
            for passage in passage_candidates[: request.book_passage_limit]
            if passage["passageId"] not in request.excluded_book_passage_ids
        ]

        local_candidates: list[dict[str, Any]] = []
        local_chunks: list[dict[str, Any]] = []
        if self.local_library is not None:
            query = "\n".join([request.question, focus["selection"]["exact"], *focus["headingPath"]])
            try:
                local_candidates = self.local_library.search_local_library(query, limit=5)
            except ValueError as error:
                raise ContextBuildError(str(error)) from error
            candidate_by_id = {item["chunkId"]: item for item in local_candidates}
            if request.included_local_chunk_ids - set(candidate_by_id):
                raise ContextBuildError("selected local-library chunks are no longer available")
            if any(
                not candidate_by_id[chunk_id].get("externalSharingApproved")
                for chunk_id in request.included_local_chunk_ids
            ):
                raise ContextBuildError(
                    "selected local-library source has not been approved for external sharing"
                )
            local_chunks = [
                candidate_by_id[chunk_id]
                for chunk_id in sorted(request.included_local_chunk_ids)
            ]

        manifest = {
            "contextSchemaVersion": CONTEXT_SCHEMA_VERSION,
            "promptVersion": request.prompt_version,
            "retrievalVersion": RETRIEVAL_VERSION,
            "sourceRegistryVersion": SOURCE_REGISTRY_VERSION,
            "chapterRevision": chapter_revision,
            "sourceHashes": {
                "bookMetadata": hashlib.sha256(
                    self.metadata_path.read_bytes()
                ).hexdigest(),
                "translationIndex": hashlib.sha256(
                    self.translation_index_path.read_bytes()
                ).hexdigest(),
                "scriptures": hashlib.sha256(
                    json.dumps(scriptures, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "footnotes": hashlib.sha256(
                    json.dumps(footnotes, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest(),
            },
            "included": {
                "scriptureIds": [item["id"] for item in scriptures],
                "footnoteIds": [item["id"] for item in footnotes],
                "noteIds": [item["noteId"] for item in notes],
                "noteRevisions": [
                    {
                        "noteId": item["noteId"],
                        "sourceRevision": item["sourceRevision"],
                        "updatedAt": item["updatedAt"],
                    }
                    for item in notes
                ],
                "translationSourceLines": [item["sourceLine"] for item in entities],
                "bookPassages": [
                    {
                        "passageId": item["passageId"],
                        "chapterId": item["chapterId"],
                        "blockId": item["blockId"],
                        "sourceRevision": item["sourceRevision"],
                        "footnoteRevision": item["footnoteRevision"],
                        "relatedFootnoteIds": item["relatedFootnoteIds"],
                    }
                    for item in book_passages
                ],
                "localSourceChunks": [
                    {
                        "chunkId": item["chunkId"],
                        "sourceId": item["sourceId"],
                        "locator": item["locator"],
                        "sourceSha256": item["sourceSha256"],
                        "processedSha256": item["processedSha256"],
                    }
                    for item in local_chunks
                ],
                "webSources": [],
            },
            "capabilities": {
                "localLibrary": self.local_library is not None,
                "crossChapterSearch": True,
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
            "personalStudy": {"notes": notes},
            "referenceResolution": {"entities": entities, "terms": []},
            "retrieval": {
                "bookPassages": book_passages,
                "localSourceChunks": local_chunks,
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
            "notes": notes,
            "noteCandidates": note_candidates,
            "translationEntities": entities,
            "translationCandidates": [
                {**item, "included": item["sourceLine"] in request.included_translation_source_lines}
                for item in entity_candidates
            ],
            "bookPassages": book_passages,
            "bookPassageLimit": request.book_passage_limit,
            "hasMoreBookPassages": has_more_book_passages,
            "localSourceCandidates": [
                {**item, "included": item["chunkId"] in request.included_local_chunk_ids}
                for item in local_candidates
            ],
            "webSearchEnabled": False,
        }
        evidence_characters = len(request.chapter_markdown) + len(anchor["exact"])
        evidence_characters += sum(len(item["text"]) for item in scriptures)
        evidence_characters += sum(len(item["text"]) for item in footnotes)
        evidence_characters += sum(len(item["body"]) for item in notes)
        evidence_characters += sum(len(item["excerpt"]) for item in book_passages)
        evidence_characters += sum(len(item["text"]) for item in local_chunks)
        evidence_characters += sum(
            len(footnote["text"])
            for item in book_passages
            for footnote in item["relatedFootnotes"]
        )
        estimates = {
            "method": "characters",
            "evidenceCharacters": evidence_characters,
            "tokenEstimate": None,
        }
        return ContextBundle(envelope=envelope, manifest=manifest, preview=preview, estimates=estimates)
