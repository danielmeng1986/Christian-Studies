#!/usr/bin/env python3
"""Build normalized, lookup-friendly Bible JSON from eBible VPL files."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "versions"
DOWNLOAD_DATE = "2026-08-27"

TRANSLATIONS = {
    "cuv-t": {
        "name": "新標點和合本",
        "english_name": "Chinese Union Version (Traditional)",
        "language": "zh-Hant",
        "abbreviation": "CUV-T",
        "ebible_id": "cmn-cu89t",
        "source_url": "https://ebible.org/Scriptures/cmn-cu89t_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?all=1&id=cmn-cu89t",
        "license": "Public Domain",
    },
    "cuv-s": {
        "name": "新标点和合本",
        "english_name": "Chinese Union Version (Simplified)",
        "language": "zh-Hans",
        "abbreviation": "CUV-S",
        "ebible_id": "cmn-cu89s",
        "source_url": "https://ebible.org/Scriptures/cmn-cu89s_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?all=1&id=cmn-cu89s",
        "license": "Public Domain",
    },
    "kjv": {
        "name": "King James Version (1769)",
        "english_name": "King James Version (1769)",
        "language": "en",
        "abbreviation": "KJV",
        "ebible_id": "eng-kjv2006",
        "source_url": "https://ebible.org/Scriptures/eng-kjv2006_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?id=eng-kjv2006",
        "license": "Public Domain outside the United Kingdom; UK Crown letters-patent restrictions apply",
    },
    "asv": {
        "name": "American Standard Version (1901)",
        "english_name": "American Standard Version (1901)",
        "language": "en",
        "abbreviation": "ASV",
        "ebible_id": "eng-asv",
        "source_url": "https://ebible.org/Scriptures/eng-asv_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?id=eng-asv",
        "license": "Public Domain",
    },
    "web": {
        "name": "World English Bible, Protestant edition",
        "english_name": "World English Bible, Protestant edition",
        "language": "en",
        "abbreviation": "WEB",
        "ebible_id": "engwebp",
        "source_url": "https://ebible.org/Scriptures/engwebp_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?id=engwebp",
        "license": "Public Domain",
    },
    "bsb": {
        "name": "Berean Standard Bible",
        "english_name": "Berean Standard Bible",
        "language": "en",
        "abbreviation": "BSB",
        "ebible_id": "engbsb",
        "source_url": "https://ebible.org/Scriptures/engbsb_vpl.zip",
        "details_url": "https://ebible.org/bible/details.php?id=engbsb",
        "license": "Public Domain",
    },
}

# code, English name, traditional Chinese, simplified Chinese, common aliases
BOOKS = [
    ("GEN", "Genesis", "創世記", "创世记", ["Gen", "Ge", "創", "创"]),
    ("EXO", "Exodus", "出埃及記", "出埃及记", ["Exod", "Ex", "出"]),
    ("LEV", "Leviticus", "利未記", "利未记", ["Lev", "Le", "利"]),
    ("NUM", "Numbers", "民數記", "民数记", ["Num", "Nu", "民"]),
    ("DEU", "Deuteronomy", "申命記", "申命记", ["Deut", "Dt", "申"]),
    ("JOS", "Joshua", "約書亞記", "约书亚记", ["Josh", "Jos", "書", "书"]),
    ("JDG", "Judges", "士師記", "士师记", ["Judg", "Jdg", "士"]),
    ("RUT", "Ruth", "路得記", "路得记", ["Ruth", "Ru", "得"]),
    ("1SA", "1 Samuel", "撒母耳記上", "撒母耳记上", ["1Sam", "1 Sa", "撒上"]),
    ("2SA", "2 Samuel", "撒母耳記下", "撒母耳记下", ["2Sam", "2 Sa", "撒下"]),
    ("1KI", "1 Kings", "列王紀上", "列王纪上", ["1Kgs", "1 Ki", "王上"]),
    ("2KI", "2 Kings", "列王紀下", "列王纪下", ["2Kgs", "2 Ki", "王下"]),
    ("1CH", "1 Chronicles", "歷代志上", "历代志上", ["1Chr", "1 Ch", "代上"]),
    ("2CH", "2 Chronicles", "歷代志下", "历代志下", ["2Chr", "2 Ch", "代下"]),
    ("EZR", "Ezra", "以斯拉記", "以斯拉记", ["Ezra", "Ezr", "拉"]),
    ("NEH", "Nehemiah", "尼希米記", "尼希米记", ["Neh", "Ne", "尼"]),
    ("EST", "Esther", "以斯帖記", "以斯帖记", ["Esth", "Est", "斯"]),
    ("JOB", "Job", "約伯記", "约伯记", ["Job", "伯"]),
    ("PSA", "Psalms", "詩篇", "诗篇", ["Psalm", "Ps", "Psa", "詩", "诗"]),
    ("PRO", "Proverbs", "箴言", "箴言", ["Prov", "Pr", "箴"]),
    ("ECC", "Ecclesiastes", "傳道書", "传道书", ["Eccl", "Ecc", "傳", "传"]),
    ("SNG", "Song of Solomon", "雅歌", "雅歌", ["Song", "Song of Songs", "Sng", "歌"]),
    ("ISA", "Isaiah", "以賽亞書", "以赛亚书", ["Isa", "Is", "賽", "赛"]),
    ("JER", "Jeremiah", "耶利米書", "耶利米书", ["Jer", "Je", "耶"]),
    ("LAM", "Lamentations", "耶利米哀歌", "耶利米哀歌", ["Lam", "La", "哀"]),
    ("EZK", "Ezekiel", "以西結書", "以西结书", ["Ezek", "Ezk", "結", "结"]),
    ("DAN", "Daniel", "但以理書", "但以理书", ["Dan", "Da", "但"]),
    ("HOS", "Hosea", "何西阿書", "何西阿书", ["Hos", "Ho", "何"]),
    ("JOL", "Joel", "約珥書", "约珥书", ["Joel", "Jl", "珥"]),
    ("AMO", "Amos", "阿摩司書", "阿摩司书", ["Amos", "Am", "摩"]),
    ("OBA", "Obadiah", "俄巴底亞書", "俄巴底亚书", ["Obad", "Ob", "俄"]),
    ("JON", "Jonah", "約拿書", "约拿书", ["Jonah", "Jon", "拿"]),
    ("MIC", "Micah", "彌迦書", "弥迦书", ["Mic", "Mi", "彌", "弥"]),
    ("NAM", "Nahum", "那鴻書", "那鸿书", ["Nah", "Na", "鴻", "鸿"]),
    ("HAB", "Habakkuk", "哈巴谷書", "哈巴谷书", ["Hab", "哈"]),
    ("ZEP", "Zephaniah", "西番雅書", "西番雅书", ["Zeph", "Zep", "番"]),
    ("HAG", "Haggai", "哈該書", "哈该书", ["Hag", "該", "该"]),
    ("ZEC", "Zechariah", "撒迦利亞書", "撒迦利亚书", ["Zech", "Zec", "亞", "亚"]),
    ("MAL", "Malachi", "瑪拉基書", "玛拉基书", ["Mal", "瑪", "玛"]),
    ("MAT", "Matthew", "馬太福音", "马太福音", ["Matt", "Mt", "太"]),
    ("MRK", "Mark", "馬可福音", "马可福音", ["Mark", "Mk", "可"]),
    ("LUK", "Luke", "路加福音", "路加福音", ["Luke", "Lk", "路"]),
    ("JHN", "John", "約翰福音", "约翰福音", ["John", "Jn", "約", "约"]),
    ("ACT", "Acts", "使徒行傳", "使徒行传", ["Acts", "Ac", "徒"]),
    ("ROM", "Romans", "羅馬書", "罗马书", ["Rom", "Ro", "羅", "罗"]),
    ("1CO", "1 Corinthians", "哥林多前書", "哥林多前书", ["1Cor", "1 Co", "林前"]),
    ("2CO", "2 Corinthians", "哥林多後書", "哥林多后书", ["2Cor", "2 Co", "林後", "林后"]),
    ("GAL", "Galatians", "加拉太書", "加拉太书", ["Gal", "Ga", "加"]),
    ("EPH", "Ephesians", "以弗所書", "以弗所书", ["Eph", "弗"]),
    ("PHP", "Philippians", "腓立比書", "腓立比书", ["Phil", "Php", "腓"]),
    ("COL", "Colossians", "歌羅西書", "歌罗西书", ["Col", "西"]),
    ("1TH", "1 Thessalonians", "帖撒羅尼迦前書", "帖撒罗尼迦前书", ["1Thess", "1 Th", "帖前"]),
    ("2TH", "2 Thessalonians", "帖撒羅尼迦後書", "帖撒罗尼迦后书", ["2Thess", "2 Th", "帖後", "帖后"]),
    ("1TI", "1 Timothy", "提摩太前書", "提摩太前书", ["1Tim", "1 Ti", "提前"]),
    ("2TI", "2 Timothy", "提摩太後書", "提摩太后书", ["2Tim", "2 Ti", "提後", "提后"]),
    ("TIT", "Titus", "提多書", "提多书", ["Titus", "Tit", "多"]),
    ("PHM", "Philemon", "腓利門書", "腓利门书", ["Phlm", "Phm", "門", "门"]),
    ("HEB", "Hebrews", "希伯來書", "希伯来书", ["Heb", "來", "来"]),
    ("JAM", "James", "雅各書", "雅各书", ["Jas", "Jam", "雅"]),
    ("1PE", "1 Peter", "彼得前書", "彼得前书", ["1Pet", "1 Pe", "彼前"]),
    ("2PE", "2 Peter", "彼得後書", "彼得后书", ["2Pet", "2 Pe", "彼後", "彼后"]),
    ("1JO", "1 John", "約翰一書", "约翰一书", ["1John", "1 Jn", "約一", "约一"]),
    ("2JO", "2 John", "約翰二書", "约翰二书", ["2John", "2 Jn", "約二", "约二"]),
    ("3JO", "3 John", "約翰三書", "约翰三书", ["3John", "3 Jn", "約三", "约三"]),
    ("JUD", "Jude", "猶大書", "犹大书", ["Jude", "Jud", "猶", "犹"]),
    ("REV", "Revelation", "啟示錄", "启示录", ["Rev", "Re", "啟", "启"]),
]

ZH_ABBREVIATIONS = {
    "GEN": ("創", "创"), "EXO": ("出", "出"), "LEV": ("利", "利"),
    "NUM": ("民", "民"), "DEU": ("申", "申"), "JOS": ("書", "书"),
    "JDG": ("士", "士"), "RUT": ("得", "得"), "1SA": ("撒上", "撒上"),
    "2SA": ("撒下", "撒下"), "1KI": ("王上", "王上"), "2KI": ("王下", "王下"),
    "1CH": ("代上", "代上"), "2CH": ("代下", "代下"), "EZR": ("拉", "拉"),
    "NEH": ("尼", "尼"), "EST": ("斯", "斯"), "JOB": ("伯", "伯"),
    "PSA": ("詩", "诗"), "PRO": ("箴", "箴"), "ECC": ("傳", "传"),
    "SNG": ("歌", "歌"), "ISA": ("賽", "赛"), "JER": ("耶", "耶"),
    "LAM": ("哀", "哀"), "EZK": ("結", "结"), "DAN": ("但", "但"),
    "HOS": ("何", "何"), "JOL": ("珥", "珥"), "AMO": ("摩", "摩"),
    "OBA": ("俄", "俄"), "JON": ("拿", "拿"), "MIC": ("彌", "弥"),
    "NAM": ("鴻", "鸿"), "HAB": ("哈", "哈"), "ZEP": ("番", "番"),
    "HAG": ("該", "该"), "ZEC": ("亞", "亚"), "MAL": ("瑪", "玛"),
    "MAT": ("太", "太"), "MRK": ("可", "可"), "LUK": ("路", "路"),
    "JHN": ("約", "约"), "ACT": ("徒", "徒"), "ROM": ("羅", "罗"),
    "1CO": ("林前", "林前"), "2CO": ("林後", "林后"), "GAL": ("加", "加"),
    "EPH": ("弗", "弗"), "PHP": ("腓", "腓"), "COL": ("西", "西"),
    "1TH": ("帖前", "帖前"), "2TH": ("帖後", "帖后"), "1TI": ("提前", "提前"),
    "2TI": ("提後", "提后"), "TIT": ("多", "多"), "PHM": ("門", "门"),
    "HEB": ("來", "来"), "JAM": ("雅", "雅"), "1PE": ("彼前", "彼前"),
    "2PE": ("彼後", "彼后"), "1JO": ("約壹", "约壹"), "2JO": ("約貳", "约贰"),
    "3JO": ("約參", "约叁"), "JUD": ("猶", "犹"), "REV": ("啟", "启"),
}

LINE = re.compile(r"^([1-3A-Z]+) (\d+):(\d+) (.*)$")

# eBible's VPL export uses a small set of legacy BibleWorks codes. Normalize
# them to the current three-character USFM codes used by this repository.
SOURCE_CODE_MAP = {
    "SOL": "SNG",
    "EZE": "EZK",
    "JOE": "JOL",
    "NAH": "NAM",
    "MAR": "MRK",
    "JOH": "JHN",
    "PHI": "PHP",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value, *, compact: bool = False) -> None:
    options = {"ensure_ascii": False}
    if compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    path.write_text(json.dumps(value, **options) + "\n", encoding="utf-8")


def build_books() -> list[dict]:
    result = []
    seen_aliases: dict[str, str] = {}
    for order, (code, english, traditional, simplified, aliases) in enumerate(BOOKS, 1):
        abbreviation_hant, abbreviation_hans = ZH_ABBREVIATIONS[code]
        source_codes = [source for source, canonical in SOURCE_CODE_MAP.items() if canonical == code]
        source_codes.append(code)
        all_aliases = list(dict.fromkeys([
            code,
            *source_codes,
            english,
            traditional,
            simplified,
            abbreviation_hant,
            abbreviation_hans,
            *aliases,
        ]))
        for alias in all_aliases:
            key = re.sub(r"[ .]", "", alias).casefold()
            previous = seen_aliases.get(key)
            if previous and previous != code:
                raise SystemExit(f"Ambiguous book alias {alias!r}: {previous} and {code}")
            seen_aliases[key] = code
        result.append({
            "order": order,
            "code": code,
            "name_en": english,
            "name_zh_hant": traditional,
            "name_zh_hans": simplified,
            "abbreviation_zh_hant": abbreviation_hant,
            "abbreviation_zh_hans": abbreviation_hans,
            "source_codes": source_codes,
            "aliases": all_aliases,
        })
    return result


def build_citation_aliases(books: list[dict]) -> dict:
    aliases = {}
    for book in books:
        for alias in book["aliases"]:
            normalized = re.sub(r"[\s.]", "", alias).casefold()
            aliases[normalized] = book["code"]
    return {
        "schema_version": 1,
        "normalization": "Remove whitespace and periods, then apply Unicode case folding.",
        "preferred_display": {
            "zh-Hant": "abbreviation_zh_hant",
            "zh-Hans": "abbreviation_zh_hans",
        },
        "aliases": dict(sorted(aliases.items())),
    }


def write_book_mapping(books: list[dict]) -> None:
    lines = [
        "# Bible Book Code Mapping",
        "",
        "Canonical codes follow current three-character USFM usage. `Source code` records the legacy code found in the downloaded eBible VPL files when it differs. Both traditional and simplified abbreviations are accepted for lookup, independent of the selected translation.",
        "",
        "| # | Code | Source code | 繁體簡稱 | 简体简称 | 繁體全名 | 简体全名 | English |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for book in books:
        source_codes = ", ".join(book["source_codes"])
        lines.append(
            f"| {book['order']} | `{book['code']}` | `{source_codes}` | "
            f"{book['abbreviation_zh_hant']} | {book['abbreviation_zh_hans']} | "
            f"{book['name_zh_hant']} | {book['name_zh_hans']} | {book['name_en']} |"
        )
    (ROOT / "book-mapping.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_translation(version_id: str, metadata: dict, expected_codes: list[str]) -> dict:
    source = VERSIONS / version_id / "source.vpl.txt"
    books: dict[str, dict[str, dict[str, str]]] = {}
    verse_count = 0
    for line_number, raw_line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(), 1):
        match = LINE.match(raw_line)
        if not match:
            raise SystemExit(f"{source}:{line_number}: invalid VPL line")
        source_code, chapter, verse, text = match.groups()
        code = SOURCE_CODE_MAP.get(source_code, source_code)
        if code not in expected_codes:
            raise SystemExit(f"{source}:{line_number}: unexpected book code {code}")
        chapter_map = books.setdefault(code, {}).setdefault(chapter, {})
        if verse in chapter_map:
            raise SystemExit(f"{source}:{line_number}: duplicate {code} {chapter}:{verse}")
        chapter_map[verse] = text
        verse_count += 1
    if list(books) != expected_codes:
        raise SystemExit(f"{source}: expected the canonical 66-book order")

    normalized = VERSIONS / version_id / "verses.json"
    document = {
        "schema_version": 1,
        "translation": version_id,
        "abbreviation": metadata["abbreviation"],
        "language": metadata["language"],
        "books": books,
    }
    write_json(normalized, document, compact=True)
    return {
        "id": version_id,
        **metadata,
        "downloaded_on": DOWNLOAD_DATE,
        "format": "VPL (one verse per line), normalized to nested JSON",
        "book_count": len(books),
        "verse_record_count": verse_count,
        "source_file": f"versions/{version_id}/source.vpl.txt",
        "normalized_file": f"versions/{version_id}/verses.json",
        "source_sha256": sha256(source),
        "normalized_sha256": sha256(normalized),
    }


def main() -> None:
    books = build_books()
    expected_codes = [book["code"] for book in books]
    write_json(ROOT / "books.json", {"schema_version": 2, "books": books})
    write_json(ROOT / "citation-aliases.json", build_citation_aliases(books))
    write_book_mapping(books)
    translations = [
        build_translation(version_id, metadata, expected_codes)
        for version_id, metadata in TRANSLATIONS.items()
    ]
    write_json(ROOT / "manifest.json", {
        "schema_version": 1,
        "downloaded_on": DOWNLOAD_DATE,
        "canonical_collection": "Protestant 66-book canon",
        "translations": translations,
    })


if __name__ == "__main__":
    main()
