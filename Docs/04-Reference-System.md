# 4. Reference System

References in Christian Studies should remain readable in ordinary Markdown, locally useful during study, and traceable across time. Version 1.0 uses simple documents rather than a specialized citation database.

## Scope and locations

The repository-level `References/` directory records shared indexes and conventions. Each studied book also has `Books/<Book-Slug>/References/` for material specific to that book:

```text
References/
  Footnotes.md
  Bibliography.md
  Scripture.md

Books/<Book-Slug>/References/
  Footnotes.md
  Bibliography.md
  Scripture.md
```

Book-level reference documents may be short or absent in substance when there is nothing to record, but the canonical locations remain stable. A book-level entry may link to a shared reference instead of duplicating it.

## Reference types

**Footnotes** clarify, qualify, or source a local statement. Place a standard Markdown footnote at the point of use whenever possible. Use a book or shared `Footnotes.md` file for imported notes, a compact index, or material that cannot reasonably remain beside the text.

**Bibliography entries** identify works cited or studied. Record enough information to identify the edition or resource: author or editor, title, publication details when known, and a stable link or identifier when relevant.

**Scripture citations** identify biblical passages in a consistent human-readable form, such as `John 3:16` or `Romans 8:1–4`. Name a translation whenever a quotation's wording depends on it. `Scripture.md` may record shared translation and citation conventions.

**External references** point outside this repository. Include a title, author or organization when known, URL, access date when relevant, and enough surrounding context to explain its use. Store them in a bibliography or another clearly labeled reference section.

## Citation practice

Use enough local context that a reader can trace a significant claim without relying on a tool or a private conversation. Prefer links from reading files, notes, and knowledge pages to the supporting chapter, bibliography entry, Scripture citation, or external source.

Reference files organize evidence; they do not replace local citations where a reader needs to understand what a statement depends on. Source provenance for normalized book chapters is governed by [03-Book-Format.md](03-Book-Format.md#36-provenance-and-traceability).

## Evolution

Future versions may add stable citation keys, structured bibliography data, generated indexes, or cross-book reference links. Such changes should remain understandable in Markdown and must not hide the evidence behind an opaque system.
