# 4. Reference System

References should be readable in ordinary Markdown and stable enough to support later indexing. Version 1.0 keeps the shared system intentionally small:

```text
References/
  Footnotes.md
  Bibliography.md
  Scripture.md
```

## Four distinct reference types

**Footnotes** clarify, qualify, or source a specific local statement. Keep them with the reading or note where the statement appears, using ordinary Markdown footnotes when appropriate.

**Bibliography** records works cited or studied. `References/Bibliography.md` is the shared human-readable index; book-specific source details may also appear in `Metadata/book.yml`.

**Scripture references** use a consistent human-readable citation such as `Romans 8:1–4` or `John 3:16`. Translation-dependent quotations name their translation. `References/Scripture.md` records any repository-wide citation or translation conventions.

**External references** link to material outside the repository. Include a title, author or organization when known, URL, access date when relevant, and a brief reason for citation where context is not obvious.

## Citation practice

Use enough local context that a reader can trace a claim without relying on a future tool. Prefer links from notes and knowledge pages to the relevant book chapter, bibliography entry, Scripture page, or external source.

Future versions may introduce stable IDs, structured bibliography data, or generated indexes only after the simple Markdown conventions prove insufficient.
