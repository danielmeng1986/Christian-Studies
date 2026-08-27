# Bible Text Corpus

This directory contains repository-level Bible texts for exact Scripture lookup, quotation, comparison, and generated reading interfaces.

## Included translations

| ID | Translation | Language | License |
|---|---|---|---|
| `cuv-t` | 新標點和合本 | Traditional Chinese | Public Domain |
| `cuv-s` | 新标点和合本 | Simplified Chinese | Public Domain |
| `kjv` | King James Version (1769) | English | Public Domain outside the United Kingdom; see the regional note below |
| `asv` | American Standard Version (1901) | English | Public Domain |
| `web` | World English Bible, Protestant edition | English | Public Domain |
| `bsb` | Berean Standard Bible | English | Public Domain |

The Chinese texts are the New Punctuation Chinese Union Version, not the copyrighted Revised Chinese Union Version (RCUV). The WEB source is the 66-book Protestant edition; the general eBible WEB package also contains deuterocanonical books and is intentionally not used here.

The KJV is public domain in most jurisdictions. In the United Kingdom, Crown letters-patent restrictions govern authorized printing. Preserve the notice and source details in `manifest.json` when redistributing it.

## Layout

Each directory under `versions/` contains:

- `source.vpl.txt`: the downloaded eBible verse-per-line text, preserved without normalization;
- `verses.json`: a generated UTF-8 lookup document organized as `books -> code -> chapter -> verse`.

Shared files:

- `manifest.json`: provenance, licensing, source URLs, record counts, and SHA-256 checksums;
- `books.json`: canonical book order, multilingual names, preferred simplified/traditional Chinese abbreviations, source codes, and common aliases;
- `book-mapping.md`: the same 66-book code and Chinese-abbreviation mapping in a human-reviewable table;
- `citation-aliases.json`: a compact alias-to-canonical-code map for citation parsers;
- `scripts/build.py`: deterministic normalization and validation.

Verse record counts differ between translations because their versification sometimes joins or separates verses differently. A record must therefore be addressed by its actual `BOOK.CHAPTER.VERSE` key and must never be aligned merely by array position.

## Rebuild and verify

Run from the repository root:

```bash
python3 References/Bible-Texts/scripts/build.py
```

The build rejects malformed lines, duplicate verse keys, unknown books, and noncanonical book order. The raw source files are authoritative; generated JSON must reproduce their text exactly.

To verify citation parsing or retrieve verses, use the local lookup helper. It defaults to CUV-S and accepts traditional or simplified abbreviations, `:`, `：`, `.`, or `．` as the chapter/verse separator:

```bash
python3 References/Bible-Texts/scripts/lookup.py '路4:23' '來11.39'
python3 References/Bible-Texts/scripts/lookup.py -t cuv-s -t kjv '约3:16-18'
```

## Source and attribution

All six VPL packages were downloaded from [eBible.org](https://ebible.org/) on 2026-08-27. Exact package URLs, detail pages, identifiers, licenses, and checksums are recorded in `manifest.json`.

Do not add copyrighted full-text translations such as NIV, ESV, NRSVue, NASB, NKJV, CSB, or NLT here without a license that expressly permits repository storage, redistribution, and the intended software or AI use.
