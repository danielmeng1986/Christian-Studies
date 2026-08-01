# 3. Book Format

Each studied book has one directory under `Books/`, named with a stable, human-readable slug.

```text
Books/
  A-Quest-for-Godliness/
    Original/
    Reading/
    Notes/
    Metadata/
```

## Required areas

`Original/` preserves supplied files exactly as received: scans, EPUBs, Word files, PDFs, and related source material. These files are never replaced by generated Markdown.

`Reading/` contains normalized Markdown intended for reading and discussion. It may be derived from an original source, but is a separate representation.

`Notes/` contains notes tied directly to the book, its chapters, or its arguments. Book notes should link outward when they contribute to reusable knowledge.

`Metadata/` contains book-level metadata and, when useful, a concise record of normalization decisions or source provenance.

## Metadata

Store the primary metadata in `Metadata/book.yml`. It is renderer-independent and uses YAML:

```yaml
title: A Quest for Godliness
subtitle: The Puritan Vision of the Christian Life
author: J. I. Packer
translator: null
publisher: Crossway
publication_year: 1990
language: en
source_format: doc
isbn: null
status: active
reading_progress: 0
tags: [puritans, christian-life]
```

Use `null` for an unknown single-value field and `[]` for an intentionally empty list. `reading_progress` is a simple percentage from `0` to `100`; detailed progress belongs in the journal or book notes.

Additional fields may be added when they recur across multiple books. Do not make a renderer's private configuration part of this core metadata.

## Reading chapters

Split reading material by meaningful reading units, normally one chapter per Markdown file. The division serves reading and discussion; it need not reproduce pages, sections, or file boundaries of the source.

```text
Reading/
  00-Front-Matter.md
  01-Introduction.md
  02-Why-We-Need-the-Puritans.md
```

Filenames begin with a zero-padded sequence and use a descriptive title. The sequence is stable once reading begins; avoid renumbering existing files merely to make room for a later discovery. Do not use generic names such as `Chapter1.md`.

Each normalized reading file should identify its book, chapter, and source location near the beginning. Any editorial omissions, corrections, or uncertain transcriptions should be noted plainly. Original wording must never be silently presented as AI or editorial rewriting.
