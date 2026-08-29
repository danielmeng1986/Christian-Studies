#!/usr/bin/env python3
"""Local, rebuildable source library for the QFG reader."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


CATALOG_SCHEMA_VERSION = 1
PROCESSED_SCHEMA_VERSION = 1
INDEX_SCHEMA_VERSION = 1
SUPPORTED_FORMATS = {"markdown", "text", "json", "pdf"}
SOURCE_TYPES = {"book", "article", "paper", "sermon", "reference", "web_snapshot"}
AUTHORITY_CLASSES = {"primary", "scholarly", "confessional_secondary", "general_secondary"}
SENSITIVITY_CLASSES = {"standard", "private"}
CATALOG_FIELDS = {
    "sourceId", "title", "author", "language", "sourceType", "theologicalTradition",
    "authorityClass", "originalPath", "processedPath", "url", "licenseNote", "sha256",
    "processedSha256", "format", "sensitivity", "enabled", "externalSharingApprovedAt",
    "createdAt",
}
TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


class LocalLibraryError(ValueError):
    """Raised when a source or local-library document is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _clean_text(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def _paragraph_chunks(text: str, locator_prefix: str, headings: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[dict[str, Any]] = []
    for index, paragraph in enumerate(paragraphs, 1):
        for part_index, start in enumerate(range(0, len(paragraph), 2000), 1):
            suffix = f".{part_index}" if len(paragraph) > 2000 else ""
            chunks.append({
                "chunkId": "",
                "locator": f"{locator_prefix}:{index}{suffix}",
                "headingPath": list(headings),
                "text": paragraph[start:start + 2000],
            })
    return chunks


def _convert_markdown(content: bytes) -> list[dict[str, Any]]:
    try:
        text = _clean_text(content.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise LocalLibraryError("Markdown source must be UTF-8") from error
    headings: list[str] = []
    chunks: list[dict[str, Any]] = []
    buffer: list[str] = []
    section = 0

    def flush() -> None:
        nonlocal section
        if not buffer:
            return
        section += 1
        chunks.extend(_paragraph_chunks("\n".join(buffer), f"section:{section}", tuple(headings)))
        buffer.clear()

    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush()
            level = len(match.group(1))
            headings[level - 1:] = [match.group(2).strip()]
        else:
            buffer.append(line)
    flush()
    return chunks


def _convert_text(content: bytes) -> list[dict[str, Any]]:
    try:
        return _paragraph_chunks(_clean_text(content.decode("utf-8")), "paragraph")
    except UnicodeDecodeError as error:
        raise LocalLibraryError("Text source must be UTF-8") from error


def _json_leaves(value: Any, pointer: str = "") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        result: list[tuple[str, str]] = []
        for key in sorted(value):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            result.extend(_json_leaves(value[key], f"{pointer}/{escaped}"))
        return result
    if isinstance(value, list):
        result = []
        for index, item in enumerate(value):
            result.extend(_json_leaves(item, f"{pointer}/{index}"))
        return result
    return [(pointer or "/", json.dumps(value, ensure_ascii=False))]


def _convert_json(content: bytes) -> list[dict[str, Any]]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LocalLibraryError("JSON source must be valid UTF-8 JSON") from error
    return [
        {"chunkId": "", "locator": f"json:{pointer}", "headingPath": [], "text": text}
        for pointer, text in _json_leaves(value)
    ]


def _convert_pdf(content: bytes) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise LocalLibraryError("PDF import requires the pinned pypdf dependency") from error
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise LocalLibraryError("Encrypted PDF files are not supported")
        chunks: list[dict[str, Any]] = []
        for page_number, page in enumerate(reader.pages, 1):
            text = _clean_text(page.extract_text() or "")
            if text:
                chunks.extend(_paragraph_chunks(text, f"page:{page_number}"))
    except LocalLibraryError:
        raise
    except Exception as error:
        raise LocalLibraryError("PDF could not be parsed") from error
    if not chunks:
        raise LocalLibraryError("PDF contains no extractable text; OCR is not enabled")
    return chunks


def detect_format(filename: str) -> str:
    suffix = Path(filename).suffix.casefold()
    formats = {".md": "markdown", ".markdown": "markdown", ".txt": "text", ".json": "json", ".pdf": "pdf"}
    if suffix not in formats:
        raise LocalLibraryError("Supported source formats are Markdown, TXT, JSON, and PDF")
    return formats[suffix]


def convert_source(filename: str, content: bytes) -> tuple[str, list[dict[str, Any]]]:
    source_format = detect_format(filename)
    converters = {"markdown": _convert_markdown, "text": _convert_text, "json": _convert_json, "pdf": _convert_pdf}
    chunks = converters[source_format](content)
    if not chunks:
        raise LocalLibraryError("Source contains no indexable text")
    return source_format, chunks


def _required_string(metadata: dict[str, Any], field: str) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value.strip():
        raise LocalLibraryError(f"{field} must be a non-empty string")
    return value.strip()


def normalize_metadata(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise LocalLibraryError("metadata must be an object")
    allowed = {"title", "author", "language", "sourceType", "theologicalTradition", "authorityClass", "url", "licenseNote", "sensitivity"}
    if not set(metadata) <= allowed:
        raise LocalLibraryError("metadata has unexpected fields")
    result = {
        "title": _required_string(metadata, "title"),
        "author": metadata.get("author"),
        "language": _required_string(metadata, "language"),
        "sourceType": _required_string(metadata, "sourceType"),
        "theologicalTradition": metadata.get("theologicalTradition"),
        "authorityClass": _required_string(metadata, "authorityClass"),
        "url": metadata.get("url"),
        "licenseNote": metadata.get("licenseNote"),
        "sensitivity": metadata.get("sensitivity", "standard"),
    }
    for field in ("author", "theologicalTradition", "url", "licenseNote"):
        if result[field] is not None and (not isinstance(result[field], str) or not result[field].strip()):
            raise LocalLibraryError(f"{field} must be null or a non-empty string")
        if isinstance(result[field], str):
            result[field] = result[field].strip()
    if result["sourceType"] not in SOURCE_TYPES:
        raise LocalLibraryError("sourceType is invalid")
    if result["authorityClass"] not in AUTHORITY_CLASSES:
        raise LocalLibraryError("authorityClass is invalid")
    if result["sensitivity"] not in SENSITIVITY_CLASSES:
        raise LocalLibraryError("sensitivity is invalid")
    return result


class LocalLibrary:
    """Manage originals, processed chunks, catalog metadata, and a derived index."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.originals_root = self.root / "Originals"
        self.processed_root = self.root / "Processed"
        self.indexes_root = self.root / "Indexes"
        self.catalog_path = self.root / "catalog.json"
        self.index_path = self.indexes_root / "local-library.json"

    def ensure(self) -> None:
        for path in (self.originals_root, self.processed_root, self.indexes_root):
            path.mkdir(parents=True, exist_ok=True)
        if not self.catalog_path.exists():
            _atomic_write(self.catalog_path, _json_bytes({"schemaVersion": CATALOG_SCHEMA_VERSION, "sources": []}))
        if not self.index_path.exists():
            _atomic_write(self.index_path, _json_bytes({"schemaVersion": INDEX_SCHEMA_VERSION, "chunks": []}))

    def load_catalog(self) -> dict[str, Any]:
        self.ensure()
        try:
            document = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LocalLibraryError("catalog.json could not be read") from error
        if not isinstance(document, dict) or set(document) != {"schemaVersion", "sources"}:
            raise LocalLibraryError("catalog.json has invalid fields")
        if document["schemaVersion"] != CATALOG_SCHEMA_VERSION or not isinstance(document["sources"], list):
            raise LocalLibraryError("catalog.json has an unsupported schema")
        seen: set[str] = set()
        for source in document["sources"]:
            if not isinstance(source, dict) or set(source) != CATALOG_FIELDS:
                raise LocalLibraryError("catalog source has invalid fields")
            source_id = source.get("sourceId")
            if not isinstance(source_id, str) or source_id in seen:
                raise LocalLibraryError("catalog sourceId is invalid or duplicated")
            seen.add(source_id)
        return document

    def preview_import(self, filename: str, content: bytes, metadata: Any) -> dict[str, Any]:
        if not isinstance(filename, str) or not Path(filename).name or Path(filename).name != filename:
            raise LocalLibraryError("filename must be a plain file name")
        if not content or len(content) > 20_000_000:
            raise LocalLibraryError("source must contain 1 to 20 MB of data")
        normalized = normalize_metadata(metadata)
        source_format, chunks = convert_source(filename, content)
        for index, chunk in enumerate(chunks, 1):
            chunk["chunkId"] = f"pending:{index:04d}"
        return {
            "filename": filename,
            "format": source_format,
            "sha256": sha256_bytes(content),
            "sizeBytes": len(content),
            "metadata": normalized,
            "chunkCount": len(chunks),
            "sampleChunks": chunks[:3],
            "content": content,
            "chunks": chunks,
        }

    def confirm_import(self, preview: dict[str, Any]) -> dict[str, Any]:
        self.ensure()
        source_id = str(uuid4())
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", preview["filename"]).strip(".-") or "source"
        original_name = f"{source_id}--{safe_name}"
        original_path = self.originals_root / original_name
        processed_path = self.processed_root / f"{source_id}.json"
        chunks = []
        for index, chunk in enumerate(preview["chunks"], 1):
            chunks.append({**chunk, "chunkId": f"{source_id}:{index:04d}"})
        processed = {
            "schemaVersion": PROCESSED_SCHEMA_VERSION,
            "sourceId": source_id,
            "originalSha256": preview["sha256"],
            "format": preview["format"],
            "chunks": chunks,
        }
        processed_content = _json_bytes(processed)
        metadata = preview["metadata"]
        source = {
            "sourceId": source_id,
            **metadata,
            "originalPath": f"Originals/{original_name}",
            "processedPath": f"Processed/{source_id}.json",
            "sha256": preview["sha256"],
            "processedSha256": sha256_bytes(processed_content),
            "format": preview["format"],
            "enabled": metadata["sensitivity"] != "private",
            "externalSharingApprovedAt": None,
            "createdAt": utc_now(),
        }
        catalog = self.load_catalog()
        if any(item["sha256"] == source["sha256"] for item in catalog["sources"]):
            raise LocalLibraryError("This exact original is already present in the catalog")
        previous_catalog_content = _json_bytes(catalog)
        _atomic_write(original_path, preview["content"])
        try:
            _atomic_write(processed_path, processed_content)
            catalog["sources"].append(source)
            catalog["sources"].sort(key=lambda item: (item["title"].casefold(), item["sourceId"]))
            _atomic_write(self.catalog_path, _json_bytes(catalog))
            self.rebuild_index()
        except Exception:
            _atomic_write(self.catalog_path, previous_catalog_content)
            original_path.unlink(missing_ok=True)
            processed_path.unlink(missing_ok=True)
            self.rebuild_index()
            raise
        return source

    def rebuild_index(self) -> dict[str, Any]:
        catalog = self.load_catalog()
        chunks: list[dict[str, Any]] = []
        for source in catalog["sources"]:
            original = self.root / source["originalPath"]
            processed_path = self.root / source["processedPath"]
            try:
                original_content = original.read_bytes()
                processed_content = processed_path.read_bytes()
                processed = json.loads(processed_content)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise LocalLibraryError(f"source {source['sourceId']} cannot be rebuilt") from error
            if sha256_bytes(original_content) != source["sha256"]:
                raise LocalLibraryError(f"original hash changed for {source['sourceId']}")
            if sha256_bytes(processed_content) != source["processedSha256"]:
                raise LocalLibraryError(f"processed hash changed for {source['sourceId']}")
            if not isinstance(processed, dict) or processed.get("sourceId") != source["sourceId"]:
                raise LocalLibraryError(f"processed sourceId mismatch for {source['sourceId']}")
            for chunk in processed.get("chunks", []):
                chunks.append({
                    **chunk,
                    "sourceId": source["sourceId"],
                    "sourceTitle": source["title"],
                    "author": source["author"],
                    "authorityClass": source["authorityClass"],
                    "enabled": source["enabled"],
                    "externalSharingApproved": source["externalSharingApprovedAt"] is not None,
                    "sourceSha256": source["sha256"],
                    "processedSha256": source["processedSha256"],
                })
        chunks.sort(key=lambda item: item["chunkId"])
        index = {"schemaVersion": INDEX_SCHEMA_VERSION, "chunks": chunks}
        _atomic_write(self.index_path, _json_bytes(index))
        return {"sourceCount": len(catalog["sources"]), "chunkCount": len(chunks)}

    def list_sources(self) -> dict[str, Any]:
        catalog = self.load_catalog()
        try:
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
            indexed = {chunk["sourceId"] for chunk in index.get("chunks", [])}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            indexed = set()
        return {"schemaVersion": catalog["schemaVersion"], "sources": [{**item, "indexed": item["sourceId"] in indexed} for item in catalog["sources"]]}

    def update_source(self, source_id: str, changes: Any) -> dict[str, Any]:
        if not isinstance(changes, dict) or not set(changes) <= {"enabled", "approveExternalSharing"} or not changes:
            raise LocalLibraryError("source update has invalid fields")
        if "enabled" in changes and not isinstance(changes["enabled"], bool):
            raise LocalLibraryError("enabled must be boolean")
        if "approveExternalSharing" in changes and changes["approveExternalSharing"] is not True:
            raise LocalLibraryError("approveExternalSharing must be true")
        catalog = self.load_catalog()
        previous_catalog_content = _json_bytes(catalog)
        source = next((item for item in catalog["sources"] if item["sourceId"] == source_id), None)
        if source is None:
            raise LocalLibraryError("source was not found")
        if "enabled" in changes:
            source["enabled"] = changes["enabled"]
        if changes.get("approveExternalSharing"):
            source["externalSharingApprovedAt"] = utc_now()
        _atomic_write(self.catalog_path, _json_bytes(catalog))
        try:
            self.rebuild_index()
        except Exception:
            _atomic_write(self.catalog_path, previous_catalog_content)
            self.rebuild_index()
            raise
        return source

    def remove_derived_index(self, source_id: str) -> int:
        self.load_catalog()
        try:
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LocalLibraryError("local index could not be read") from error
        before = len(index.get("chunks", []))
        index["chunks"] = [item for item in index.get("chunks", []) if item.get("sourceId") != source_id]
        removed = before - len(index["chunks"])
        _atomic_write(self.index_path, _json_bytes(index))
        return removed

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if limit < 1 or limit > 5:
            raise LocalLibraryError("local library result limit must be 1 to 5")
        try:
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LocalLibraryError("local index could not be read") from error
        terms = _search_terms(query)
        if not terms:
            return []
        results: list[tuple[int, str, dict[str, Any]]] = []
        for chunk in index.get("chunks", []):
            if not chunk.get("enabled"):
                continue
            haystack = unicodedata.normalize("NFKC", " ".join([chunk.get("sourceTitle", ""), *chunk.get("headingPath", []), chunk.get("text", "")])).casefold()
            score = sum(min(haystack.count(term), 4) * (3 if len(term) > 1 else 1) for term in terms)
            if score:
                results.append((score, chunk["chunkId"], {**chunk, "score": score}))
        results.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in results[:limit]]

    def search_local_library(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Read-only retrieval boundary consumed by ContextBuilder."""
        return self.search(query, limit)


def _search_terms(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    words = [word for word in TOKEN_RE.findall(normalized) if len(word) > 1]
    cjk_runs = re.findall(r"[\u3400-\u9fff]+", normalized)
    bigrams = [run[index:index + 2] for run in cjk_runs for index in range(max(0, len(run) - 1))]
    return sorted(set(words + bigrams))
