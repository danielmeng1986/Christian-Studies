#!/usr/bin/env python3
"""Deterministic AI context assembly for the local reader."""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONTEXT_SCHEMA_VERSION = 1
RETRIEVAL_VERSION = 1
SOURCE_REGISTRY_VERSION = 1

SCRIPT_ROOT = Path(__file__).resolve().parent
WEB_ROOT = SCRIPT_ROOT.parent
BOOK_ROOT = WEB_ROOT.parent
DEFAULT_BOOK_METADATA_PATH = BOOK_ROOT / "Metadata/book.yml"

KEY_RE = re.compile(r"\A[a-z][a-z0-9_]*\Z")
INTEGER_RE = re.compile(r"\A-?(?:0|[1-9]\d*)\Z")


class ContextBuildError(ValueError):
    """Raised when declared context sources cannot be read deterministically."""


@dataclass(frozen=True)
class ContextBundle:
    envelope: dict[str, Any]
    manifest: dict[str, Any]
    preview: dict[str, Any]
    estimates: dict[str, Any]


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
            "focus": {
                "selection": {
                    "blockId": anchor["blockId"],
                    "exact": anchor["exact"],
                    "startOffset": anchor["startOffset"],
                    "endOffset": anchor["endOffset"],
                }
            },
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
