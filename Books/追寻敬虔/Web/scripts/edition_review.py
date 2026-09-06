#!/usr/bin/env python3
"""Edition comparison and review data for the local reader."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from markdown_it import MarkdownIt


BOOK_ID = "qfg"
VALID_STATUSES = ("draft", "reviewed", "approved")
VALID_COMMENT_STATUSES = ("open", "resolved")
MAX_COMMENT_LENGTH = 4000


class ReviewError(ValueError):
    """Raised when edition-review data is invalid or stale."""


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def strip_front_matter(source: str) -> tuple[str, dict[str, str]]:
    if not source.startswith("---\n"):
        return source, {}
    end = source.find("\n---\n", 4)
    if end < 0:
        raise ReviewError("Markdown front matter is not closed")
    metadata: dict[str, str] = {}
    for line in source[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"')
    return source[end + 5 :], metadata


def semantic_blocks(markdown: str, *, edition_id: str, chapter_id: str) -> list[dict[str, Any]]:
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    blocks: list[dict[str, Any]] = []
    for index, token in enumerate(tokens):
        if token.type not in {"heading_open", "paragraph_open"}:
            continue
        inline = tokens[index + 1] if index + 1 < len(tokens) else None
        if inline is None or inline.type != "inline" or token.map is None:
            raise ReviewError("Semantic block has no readable source range")
        ordinal = len(blocks) + 1
        kind = token.tag if token.type == "heading_open" else "blockquote" if token.level > 0 else "paragraph"
        block_uuid = str(uuid5(NAMESPACE_URL, f"{BOOK_ID}:{edition_id}:{chapter_id}:{ordinal}:{kind}"))
        blocks.append(
            {
                "blockId": block_uuid,
                "kind": kind,
                "ordinal": ordinal,
                "text": inline.content.strip(),
                "contentHash": sha256_text(inline.content.strip()),
            }
        )
    return blocks


def load_markdown(path: Path, *, edition_id: str, chapter_id: str) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    body, metadata = strip_front_matter(source)
    if metadata.get("chapter") != chapter_id:
        raise ReviewError(f"Chapter metadata does not match {chapter_id}")
    return {
        "path": path,
        "metadata": metadata,
        "body": body,
        "revision": sha256_text(body),
        "blocks": semantic_blocks(body, edition_id=edition_id, chapter_id=chapter_id),
    }


def build_review_document(
    source: dict[str, Any], target: dict[str, Any], existing: dict[str, Any] | None = None
) -> dict[str, Any]:
    source_blocks = source["blocks"]
    target_blocks = target["blocks"]
    if len(source_blocks) != len(target_blocks):
        raise ReviewError("Source and target semantic-block counts differ")
    old_pairs = {item.get("pairId"): item for item in (existing or {}).get("pairs", [])}
    pairs = []
    for source_block, target_block in zip(source_blocks, target_blocks, strict=True):
        if source_block["kind"] != target_block["kind"]:
            raise ReviewError(f"Block kind differs at ordinal {source_block['ordinal']}")
        pair_id = str(uuid5(NAMESPACE_URL, f"{BOOK_ID}:legacy-zh:chatgpt-zh-cn:05:{source_block['ordinal']}"))
        old = old_pairs.get(pair_id, {})
        unchanged = (
            old.get("sourceContentHash") == source_block["contentHash"]
            and old.get("targetContentHash") == target_block["contentHash"]
        )
        status = old.get("status", "draft") if unchanged else "draft"
        pairs.append(
            {
                "pairId": pair_id,
                "sourceBlockId": source_block["blockId"],
                "targetBlockId": target_block["blockId"],
                "sourceContentHash": source_block["contentHash"],
                "targetContentHash": target_block["contentHash"],
                "status": status,
                "reviewedAt": old.get("reviewedAt") if unchanged else None,
                "approvedAt": old.get("approvedAt") if unchanged else None,
                "comments": old.get("comments", []),
            }
        )
    all_approved = bool(pairs) and all(pair["status"] == "approved" for pair in pairs)
    old_chapter_status = (existing or {}).get("chapterStatus", "draft")
    chapter_status = "approved" if all_approved and old_chapter_status == "approved" else "reviewed" if any(
        pair["status"] != "draft" for pair in pairs
    ) else "draft"
    return {
        "schemaVersion": 2,
        "bookId": BOOK_ID,
        "sourceEditionId": "legacy-zh",
        "targetEditionId": "chatgpt-zh-cn",
        "chapterId": "05",
        "sourceRevision": source["revision"],
        "targetRevision": target["revision"],
        "revisionPolicyVersion": "qfg-modern-zh-cn-v1",
        "glossaryId": "qfg-05-v1",
        "generationModel": target["metadata"].get("generation_model", "unknown"),
        "generatedAt": target["metadata"].get("generated_at"),
        "referenceSources": [
            {
                "url": target["metadata"].get("english_reference"),
                "locator": target["metadata"].get("source_location"),
            }
        ],
        "chapterStatus": chapter_status,
        "approvedAt": (existing or {}).get("approvedAt") if chapter_status == "approved" else None,
        "pairs": pairs,
    }


def review_payload(source: dict[str, Any], target: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    pairs = []
    for pair, source_block, target_block in zip(document["pairs"], source["blocks"], target["blocks"], strict=True):
        pairs.append({**pair, "kind": source_block["kind"], "ordinal": source_block["ordinal"], "sourceText": source_block["text"], "targetText": target_block["text"]})
    counts = {status: sum(pair["status"] == status for pair in pairs) for status in VALID_STATUSES}
    counts["openComments"] = sum(
        comment.get("status") == "open" for pair in pairs for comment in pair.get("comments", [])
    )
    return {
        "bookId": BOOK_ID,
        "chapterId": "05",
        "sourceEdition": {"editionId": "legacy-zh", "label": "Word 转写版"},
        "targetEdition": {"editionId": "chatgpt-zh-cn", "label": "现代简体润译版（ChatGPT）"},
        "chapterStatus": document["chapterStatus"],
        "counts": counts,
        "canApproveChapter": counts["approved"] == len(pairs) and counts["openComments"] == 0,
        "pairs": pairs,
    }


def apply_review_update(document: dict[str, Any], payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"pairId", "status"}:
        raise ReviewError("Review update must contain pairId and status")
    if payload["status"] not in VALID_STATUSES:
        raise ReviewError("Unknown review status")
    pair = next((item for item in document["pairs"] if item["pairId"] == payload["pairId"]), None)
    if pair is None:
        raise ReviewError("Unknown aligned block")
    if payload["status"] == "approved" and any(
        comment.get("status") == "open" for comment in pair.get("comments", [])
    ):
        raise ReviewError("Resolve every comment before approving this block")
    now = now_timestamp()
    pair["status"] = payload["status"]
    pair["reviewedAt"] = now if payload["status"] in {"reviewed", "approved"} else None
    pair["approvedAt"] = now if payload["status"] == "approved" else None
    document["chapterStatus"] = "reviewed" if any(item["status"] != "draft" for item in document["pairs"]) else "draft"
    document["approvedAt"] = None
    return document


def add_review_comment(document: dict[str, Any], payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"pairId", "text"}:
        raise ReviewError("Comment request must contain pairId and text")
    text = payload["text"].strip() if isinstance(payload["text"], str) else ""
    if not text:
        raise ReviewError("Comment text cannot be empty")
    if len(text) > MAX_COMMENT_LENGTH:
        raise ReviewError(f"Comment text cannot exceed {MAX_COMMENT_LENGTH} characters")
    pair = next((item for item in document["pairs"] if item["pairId"] == payload["pairId"]), None)
    if pair is None:
        raise ReviewError("Unknown aligned block")
    now = now_timestamp()
    pair.setdefault("comments", []).append(
        {
            "commentId": str(uuid4()),
            "text": text,
            "status": "open",
            "createdAt": now,
            "resolvedAt": None,
        }
    )
    if pair["status"] == "approved":
        pair["status"] = "reviewed"
        pair["approvedAt"] = None
    document["chapterStatus"] = "reviewed" if any(item["status"] != "draft" for item in document["pairs"]) else "draft"
    document["approvedAt"] = None
    return document


def set_comment_status(document: dict[str, Any], payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"pairId", "commentId", "status"}:
        raise ReviewError("Comment-status request must contain pairId, commentId, and status")
    if payload["status"] not in VALID_COMMENT_STATUSES:
        raise ReviewError("Unknown comment status")
    pair = next((item for item in document["pairs"] if item["pairId"] == payload["pairId"]), None)
    if pair is None:
        raise ReviewError("Unknown aligned block")
    comment = next(
        (item for item in pair.get("comments", []) if item.get("commentId") == payload["commentId"]), None
    )
    if comment is None:
        raise ReviewError("Unknown review comment")
    comment["status"] = payload["status"]
    comment["resolvedAt"] = now_timestamp() if payload["status"] == "resolved" else None
    document["chapterStatus"] = "reviewed" if any(item["status"] != "draft" for item in document["pairs"]) else "draft"
    document["approvedAt"] = None
    return document


def approve_chapter(document: dict[str, Any]) -> dict[str, Any]:
    if not document["pairs"] or any(pair["status"] != "approved" for pair in document["pairs"]):
        raise ReviewError("Every block must be approved before approving the chapter")
    document["chapterStatus"] = "approved"
    if any(comment.get("status") == "open" for pair in document["pairs"] for comment in pair.get("comments", [])):
        raise ReviewError("Every review comment must be resolved before approving the chapter")
    document["approvedAt"] = now_timestamp()
    return document


def serialize(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
