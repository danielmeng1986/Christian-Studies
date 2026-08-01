# 3. Book Format Specification

This document defines the canonical internal format for every studied book in Christian Studies, regardless of whether the supplied source was a Word document, PDF, EPUB, web page, or another format. The format serves reading and study; it does not attempt to reproduce the source file's internal structure.

## 3.1 Canonical book layout

Each book has one stable, human-readable slug under `Books/`:

```text
Books/
  <Book-Slug>/
    Original/
    Reading/
    Notes/
    Metadata/
    References/
```

Every canonical book contains one slug, one metadata file, one preserved-source area, one normalized-reading area, and one reference area. `Notes/` is part of the standard layout but may remain empty until book-specific notes are needed.

`Original/` preserves raw source files exactly as received. A source file is never modified in place or replaced by normalized Markdown.

`Reading/` contains the normalized Markdown files used for reading and discussion. It is the primary study representation of the book.

`Notes/` contains reflections, questions, summaries, and interpretations tied to this book or its chapters.

`Metadata/` contains structured book metadata and concise records of normalization or provenance decisions.

`References/` contains the book's reference documents, especially footnotes, bibliography-related material, Scripture conventions, and external-source context when needed.

The book slug must be stable once established. Use a concise, descriptive, filesystem-safe name; do not casually rename an active book directory because its path is a durable reference.

## 3.2 Metadata schema

The required metadata file is `Metadata/book.yml`. It is renderer-independent and describes the book rather than a particular import process.

```yaml
title: A Quest for Godliness
subtitle: The Puritan Vision of the Christian Life
author: J. I. Packer
translator: null
editor: null
publisher: Crossway
publication_year: 1990
language: en
source_format: doc
source_file: Original/A-Quest-for-Godliness.doc
isbn: null
status: active
reading_progress: 0
tags: [puritans, christian-life]
```

| Field | Requirement | Meaning |
| --- | --- | --- |
| `title` | Required | The book's main title. |
| `subtitle` | Optional | The subtitle, if known. |
| `author` | Required | The author or responsible creator. |
| `translator` | Optional | Translator name when applicable. |
| `editor` | Optional | Editor name when applicable. |
| `publisher` | Optional | Publisher of the studied edition. |
| `publication_year` | Optional | Publication year of the studied edition. |
| `language` | Required | Primary language, preferably a language code such as `en` or `zh`. |
| `source_format` | Required | Format of the primary preserved source, such as `doc`, `pdf`, `epub`, or `html`. |
| `source_file` | Required | Repository-relative path to the primary file in `Original/`. |
| `isbn` | Optional | ISBN of the studied edition. |
| `status` | Required | Current study state, such as `planned`, `active`, `paused`, or `completed`. |
| `reading_progress` | Required | Whole-number percentage from `0` to `100`. |
| `tags` | Required | Short topical labels. |

Use `null` for an unknown scalar value and `[]` for an intentionally empty list. Required fields must be present even when their value is unknown, except where a format cannot meaningfully supply the field; record the exception in a normalization note. Add new metadata fields only when they represent a stable need across multiple books.

## 3.3 Reading chapters

`Reading/` is divided into meaningful reading units, normally one chapter per Markdown file. A unit may be a preface, introduction, chapter, or comparable section when that better supports reading and discussion.

```text
Reading/
  00-Front-Matter.md
  01-Introduction.md
  02-Why-We-Need-the-Puritans.md
```

Filenames use a zero-padded numeric prefix and a descriptive slug. They must remain stable once reading begins; do not renumber existing chapters merely to accommodate a later discovery. Avoid generic names such as `Chapter1.md`.

Each reading file contains, as applicable:

1. YAML front matter for chapter-specific metadata;
2. the chapter title;
3. source-location information near the top;
4. normalized text; and
5. clearly labeled notes about uncertain transcription or editorial changes.

For example:

```markdown
---
book: A-Quest-for-Godliness
chapter: 02
source_file: Original/A-Quest-for-Godliness.doc
source_location: "pp. 23–41"
---

# Why We Need the Puritans

> Source location: pp. 23–41 of the primary source.

Normalized text begins here.
```

Front matter is recommended when it improves traceability; it is not a substitute for a readable source-location statement. A reading file may retain headings and other source boundaries where practical, while still being normalized for clear study.

## 3.4 Source fidelity and editorial policy

The original text must never be silently replaced with rewritten AI text. Normalization may improve technical readability—for example, resolving extraction artifacts or applying consistent Markdown—but it must not silently alter the source's meaning, authorship, or boundaries.

Apply these rules:

- Preserve original source files unchanged in `Original/`.
- Mark omissions, corrections, reconstructions, and substantive editorial interventions explicitly.
- Preserve chapter, section, and quotation boundaries as far as practical.
- Label uncertain transcription clearly rather than presenting a guess as certain text.
- Keep generated summaries, translations, questions, and interpretations distinguishable from source text.
- Prefer stable filenames, paths, and source references over convenient but transient organization.

Normalization should make a source easier to read, not erase the evidence needed to evaluate it.

## 3.5 References and footnotes

Each book has a `References/` area. Version 1.0 uses Markdown-friendly documents that may remain minimal when a book has no relevant material:

```text
References/
  Footnotes.md
  Bibliography.md
  Scripture.md
```

**Footnotes** are local annotations or source notes attached to a chapter or paragraph. Keep ordinary Markdown footnotes beside the relevant text when that is clearest; use `Footnotes.md` for a book-level index or imported note record when needed.

**Bibliography** records works cited or studied in connection with the book. `Bibliography.md` is the book-level human-readable list and may link to the repository-wide bibliography.

**Scripture** records biblical citations, quotation translations, or citation conventions relevant to the book. Cite passages in readable form, for example `Romans 8:1–4`; name the translation when wording depends on it.

**External references** are sources outside the repository. Record sufficient context to identify them: title, author or organization when known, URL, and access date when relevant. They may be listed in `Bibliography.md` or a clearly labeled section of another reference document.

This first-version system favors local readability and traceability over identifiers or database-style indexing. Shared repository conventions remain documented in [04-Reference-System.md](04-Reference-System.md).

## 3.6 Provenance and traceability

Every normalized chapter must remain traceable to its evidence. At minimum, it identifies the original source file and source page numbers or location markers when they are available. It also records material editorial decisions and enough citation context to support future discussion.

Use `Metadata/book.yml` for book-level source identity, reading-file front matter or opening text for chapter-level location, and a concise normalization note in `Metadata/` when a decision affects multiple chapters. Provenance should make it possible for a future reader to distinguish source content from normalization and interpretation without consulting a particular tool.

## 3.7 Relationship to reusable knowledge

The book directory holds material whose primary context is one book. When a note develops reusable theological, historical, biographical, or scriptural knowledge, it may be promoted to a broader repository area such as `People/`, `Concepts/`, `Scripture/`, or `Timeline/`.

Promotion does not remove the book-specific context: the reusable page should link back to the relevant chapter, note, or reference. This is an architectural direction, not a requirement to create broad knowledge pages for every observation.

## 3.8 Version 1.0 boundaries

Version 1.0 defines the stable shape of a studied book, not every import edge case. Later revisions may refine chapter-splitting heuristics, reference indexing, automated import tooling, handling of PDFs, web pages, and OCR sources, and cross-book knowledge linking.

Until practical use establishes a clearer need, preserve this small format and evolve it deliberately.
