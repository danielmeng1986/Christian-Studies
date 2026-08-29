#!/usr/bin/env python3
"""Deterministic, source-locatable retrieval across the book."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import unquote

from markdown_it import MarkdownIt


DEFAULT_PASSAGE_LIMIT = 5
EXPANDED_PASSAGE_LIMIT = 10
MAX_PASSAGES_PER_CHAPTER = 2

FRONT_MATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n(?P<body>.*)\Z", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
FOOTNOTE_LINK_RE = re.compile(r"(?:^|/)Footnotes-(?P<chapter>\d{2})\.md#(?P<id>[^)\s]+)")
SCRIPTURE_LINK_RE = re.compile(r"scripture:(?P<id>[A-Z0-9.]+(?:,[0-9-]+)?)", re.IGNORECASE)
FOOTNOTE_HEADING_RE = re.compile(r"^##\s+(?P<id>.+?)\s*$", re.MULTILINE)
QUOTED_TERM_RE = re.compile(r"《([^》]{2,80})》|「([^」]{2,80})」|『([^』]{2,80})』|[\"“]([^\"”]{3,80})[\"”]")
LATIN_WORD_RE = re.compile(r"[a-z0-9]+(?:['’-][a-z0-9]+)?")
CJK_RUN_RE = re.compile(r"[\u3400-\u9fff]{2,}")

MARKDOWN_PARSER = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False, "typographer": False},
)

QUESTION_NOISE = (
    "请问", "請問", "如何", "怎麼", "怎么", "怎样", "怎樣", "为什么", "為什麼",
    "为何", "為何", "什么", "什麼", "哪些", "哪一", "是否", "能否", "可以", "关于",
    "關於", "这里", "這裡", "这段", "這段", "本段", "作者", "巴刻", "认为", "認為",
    "理解", "说明", "說明", "解释", "解釋", "论述", "論述", "提到", "展开", "展開",
    "关系", "關係", "意义", "意義", "观点", "觀點", "内容", "內容", "问题", "問題",
)

WEAK_CJK_TERMS = {
    "我們", "我们", "他們", "他们", "這個", "这个", "一個", "一个", "不是", "就是",
    "可以", "沒有", "没有", "以及", "因為", "因为", "所以", "但是", "而且", "如果",
    "對於", "对于", "其中", "自己", "這些", "这些", "那個", "那个", "本書", "本书",
    "一種", "一种", "成為", "成为", "所謂", "所谓", "之中", "之間", "之间", "有關",
    "有关", "方面", "時候", "时候", "如此", "實際", "实际", "乃是", "也是", "這樣",
    "这样", "地說", "来说", "來說", "所說", "所说", "使得", "為了", "为了", "並且",
}


class RetrievalSourceError(ValueError):
    """Raised when a declared book retrieval source cannot be rebuilt."""


@dataclass(frozen=True)
class RetrievalUnit:
    passage_id: str
    chapter_id: str
    chapter_title: str
    heading_path: tuple[str, ...]
    block_id: str
    text: str
    search_text: str
    source_revision: str
    footnote_revision: str | None
    footnotes: tuple[tuple[str, str], ...]
    scripture_ids: tuple[str, ...]
    order: int


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.translate(str.maketrans({"·": ".", "‧": ".", "・": ".", "．": "."}))
    return " ".join(normalized.split())


def _compact(value: str) -> str:
    return "".join(character for character in _normalize(value) if character.isalnum())


def _body_and_title(source: str, path: Path) -> tuple[str, str]:
    match = FRONT_MATTER_RE.fullmatch(source)
    body = match.group("body") if match else source
    title_match = TITLE_RE.search(body)
    if not title_match:
        raise RetrievalSourceError(f"chapter source is missing its title: {path}")
    return body, title_match.group("title").strip()


def _parse_footnotes(source: str) -> dict[str, str]:
    matches = list(FOOTNOTE_HEADING_RE.finditer(source))
    results: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        raw = source[match.end() : end].strip()
        if not raw:
            continue
        tokens = MARKDOWN_PARSER.parse(raw)
        parts = [token.content for token in tokens if token.type in {"inline", "fence", "code_block"}]
        text = "\n".join(part.strip() for part in parts if part.strip())
        if text:
            results[match.group("id").strip()] = text
    return results


def build_retrieval_units(
    chapter_paths: dict[str, Path],
    footnote_paths: dict[str, Path],
    block_builder: Callable[[str, str], list[Any]],
) -> list[RetrievalUnit]:
    """Rebuild paragraph-level search units from declared chapter and footnote files."""

    units: list[RetrievalUnit] = []
    for chapter_id, chapter_path in sorted(chapter_paths.items()):
        try:
            chapter_source = chapter_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RetrievalSourceError(f"chapter source could not be read: {chapter_path}") from error
        body, chapter_title = _body_and_title(chapter_source, chapter_path)
        source_revision = hashlib.sha256(body.encode("utf-8")).hexdigest()

        footnotes: dict[str, str] = {}
        footnote_revision: str | None = None
        footnote_path = footnote_paths.get(chapter_id)
        if footnote_path is not None and footnote_path.is_file():
            try:
                footnote_source = footnote_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as error:
                raise RetrievalSourceError(f"footnote source could not be read: {footnote_path}") from error
            footnotes = _parse_footnotes(footnote_source)
            footnote_revision = hashlib.sha256(footnote_source.encode("utf-8")).hexdigest()

        tokens = MARKDOWN_PARSER.parse(body)
        paragraph_sources = [
            "\n".join(body.splitlines()[token.map[0] : token.map[1]]) if token.map else ""
            for token in tokens
            if token.type in {"heading_open", "paragraph_open"}
        ]
        blocks = block_builder(body, chapter_id)
        if len(blocks) != len(paragraph_sources):
            raise RetrievalSourceError(f"block projection changed while indexing chapter {chapter_id}")

        for order, (block, block_source) in enumerate(zip(blocks, paragraph_sources)):
            if block.kind != "paragraph" or not block.text.strip():
                continue
            related_ids = tuple(
                dict.fromkeys(
                    unquote(match.group("id"))
                    for match in FOOTNOTE_LINK_RE.finditer(block_source)
                    if match.group("chapter") == chapter_id
                )
            )
            related_footnotes = tuple(
                (footnote_id, footnotes[footnote_id])
                for footnote_id in related_ids
                if footnote_id in footnotes
            )
            scripture_ids = tuple(
                dict.fromkeys(match.group("id").upper() for match in SCRIPTURE_LINK_RE.finditer(block_source))
            )
            searchable = "\n".join(
                [chapter_title, *block.heading_path, block.text, *(text for _, text in related_footnotes)]
            )
            units.append(
                RetrievalUnit(
                    passage_id=f"qfg:{chapter_id}:{block.block_id}",
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    heading_path=block.heading_path,
                    block_id=block.block_id,
                    text=block.text,
                    search_text=_normalize(searchable),
                    source_revision=source_revision,
                    footnote_revision=footnote_revision,
                    footnotes=related_footnotes,
                    scripture_ids=scripture_ids,
                    order=order,
                )
            )
    return units


def _entity_terms(entities: Iterable[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for entity in entities:
        for field in ("surface", "chinese", "english", "indexForm", "canonicalSearchName"):
            value = entity.get(field)
            if isinstance(value, str) and len(_compact(value)) >= 2:
                values.append(value)
    return list(dict.fromkeys(values))


def _quoted_terms(texts: Iterable[str]) -> list[str]:
    terms: list[str] = []
    for text in texts:
        for match in QUOTED_TERM_RE.finditer(text):
            value = next(group for group in match.groups() if group is not None).strip()
            if len(_compact(value)) >= 2:
                terms.append(value)
    return list(dict.fromkeys(terms))


def _keyword_terms(texts: Iterable[str], protected_terms: Iterable[str]) -> list[str]:
    protected = {_compact(term) for term in protected_terms}
    candidates: list[str] = []
    for original in texts:
        text = _normalize(original)
        for noise in QUESTION_NOISE:
            text = text.replace(_normalize(noise), " ")
        candidates.extend(word for word in LATIN_WORD_RE.findall(text) if len(word) >= 4)
        for run in CJK_RUN_RE.findall(text):
            if 2 <= len(run) <= 8:
                candidates.append(run)
            for size in (4, 3, 2):
                if len(run) < size:
                    continue
                candidates.extend(run[index : index + size] for index in range(len(run) - size + 1))
    result: list[str] = []
    for term, _ in Counter(candidates).most_common():
        compact = _compact(term)
        if compact in protected or term in WEAK_CJK_TERMS or len(compact) < 2:
            continue
        if any(character.isdigit() for character in compact) and len(compact) < 4:
            continue
        result.append(term)
        if len(result) == 24:
            break
    return result


def _topic_terms(question: str) -> list[str]:
    text = _normalize(question)
    for noise in QUESTION_NOISE:
        text = text.replace(_normalize(noise), " ")
    terms = [run for run in CJK_RUN_RE.findall(text) if run not in WEAK_CJK_TERMS]
    return list(dict.fromkeys(terms))


def retrieve_book_passages(
    units: list[RetrievalUnit],
    *,
    current_chapter_id: str,
    selected_block_id: str,
    question: str,
    selection: str,
    entities: list[dict[str, Any]],
    scripture_ids: Iterable[str],
    excluded_passage_ids: frozenset[str] = frozenset(),
    limit: int = DEFAULT_PASSAGE_LIMIT,
) -> list[dict[str, Any]]:
    """Rank deterministic signals and return only strong, source-locatable passages."""

    entity_terms = _entity_terms(entities)
    quoted_terms = _quoted_terms((question, selection))
    keywords = _keyword_terms((question, selection), [*entity_terms, *quoted_terms])
    topic_terms = _topic_terms(question)
    normalized_scriptures = {_normalize(value) for value in scripture_ids if value}
    scored: list[tuple[float, RetrievalUnit, list[str], list[str], list[str]]] = []

    for unit in units:
        if unit.chapter_id == current_chapter_id or unit.block_id == selected_block_id:
            continue
        compact_haystack = _compact(unit.search_text)
        entity_hits = [term for term in entity_terms if _compact(term) in compact_haystack]
        quoted_hits = [term for term in quoted_terms if _compact(term) in compact_haystack]
        keyword_hits = [term for term in keywords if _compact(term) in compact_haystack]
        topic_hits = [term for term in topic_terms if _compact(term) in compact_haystack]
        scripture_hits = [
            scripture_id
            for scripture_id in unit.scripture_ids
            if _normalize(scripture_id) in normalized_scriptures
        ]

        reasons: list[str] = []
        score = 0.0
        if entity_hits:
            reasons.append("exact_entity")
            score += 100 + min(20, 5 * len({_compact(term) for term in entity_hits}))
        if quoted_hits:
            reasons.append("exact_work_or_phrase")
            score += 75 + min(10, 3 * len(quoted_hits))
        if scripture_hits:
            reasons.append("same_scripture")
            score += 70 + min(10, 3 * len(scripture_hits))

        distinctive_hits = [term for term in keyword_hits if len(_compact(term)) >= 4]
        if distinctive_hits:
            reasons.append("distinctive_phrase")
            score += min(45, 14 * len(distinctive_hits))
        broader_hits = [term for term in keyword_hits if term not in distinctive_hits]
        if broader_hits:
            reasons.append("question_keywords")
            score += min(24, 4 * len(broader_hits))
        if topic_hits:
            reasons.append("topic_term")
            score += min(40, 12 * len(topic_hits))

        # A lexical candidate must have a primary deterministic signal, one long phrase,
        # or several independent keyword matches. This is the no-quota-filling threshold.
        topic_signal = bool(
            any(len(_compact(term)) >= 4 for term in topic_hits)
            or (len(topic_terms) == 1 and topic_hits)
            or len(topic_hits) >= 2
        )
        strong = bool(entity_hits or quoted_hits or scripture_hits or distinctive_hits or topic_signal)
        if not strong:
            continue
        heading_text = _compact(" ".join(unit.heading_path))
        if any(_compact(term) in heading_text for term in [*quoted_hits, *distinctive_hits, *topic_hits]):
            score += 8
        footnote_hits = [
            footnote_id
            for footnote_id, footnote_text in unit.footnotes
            if any(_compact(term) in _compact(footnote_text) for term in [*entity_hits, *quoted_hits, *keyword_hits])
        ]
        if footnote_hits:
            score += 2
        matched_terms = list(
            dict.fromkeys([*entity_hits, *quoted_hits, *scripture_hits, *topic_hits, *keyword_hits])
        )
        scored.append((score, unit, matched_terms, reasons, footnote_hits))

    scored.sort(key=lambda item: (-item[0], item[1].chapter_id, item[1].order, item[1].block_id))
    chapter_counts: Counter[str] = Counter()
    results: list[dict[str, Any]] = []
    for score, unit, matched_terms, reasons, footnote_hits in scored:
        if chapter_counts[unit.chapter_id] >= MAX_PASSAGES_PER_CHAPTER:
            continue
        passage = {
                "evidenceType": "book_passage",
                "passageId": unit.passage_id,
                "chapterId": unit.chapter_id,
                "chapterTitle": unit.chapter_title,
                "headingPath": list(unit.heading_path),
                "blockId": unit.block_id,
                "excerpt": unit.text,
                "matchedTerms": matched_terms,
                "matchReasons": reasons,
                "score": round(score, 3),
                "sourceRevision": unit.source_revision,
                "footnoteRevision": unit.footnote_revision,
                "relatedFootnoteIds": [footnote_id for footnote_id, _ in unit.footnotes],
                "relatedFootnotes": [
                    {"id": footnote_id, "text": text}
                    for footnote_id, text in unit.footnotes
                    if footnote_id in footnote_hits
                ],
                "matchedFootnoteIds": footnote_hits,
                "scriptureIds": list(unit.scripture_ids),
                "href": f"/chapters/{unit.chapter_id}/#{unit.block_id}",
            }
        chapter_counts[unit.chapter_id] += 1
        if unit.passage_id not in excluded_passage_ids:
            results.append(passage)
        if sum(chapter_counts.values()) >= limit:
            break
    return results
