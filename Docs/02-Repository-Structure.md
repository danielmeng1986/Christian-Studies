# 2. Repository Structure

The top-level layout separates source books, reusable knowledge, working notes, and repository specifications.

```text
Books/        Individual book study projects
Notes/        Reusable topical notes and essays
People/       Biographical and person-centered knowledge pages
Concepts/     Theological, historical, and methodological concepts
Scripture/    Scripture-focused study pages and canonical indexes
References/   Shared reference indexes and bibliographic records
Journal/      Dated reading reflections and study-log entries
Docs/         This Design Book and repository conventions
```

## Directory responsibilities

`Books/` contains the materials and notes specific to a particular book. It is the only top-level directory that stores book source files.

`Notes/` contains reusable synthesis that is not better represented as a person, concept, Scripture, or reference page.

`People/`, `Concepts/`, and `Scripture/` hold durable knowledge pages. A page may link to many books and must cite its evidence.

`References/` provides shared indexes for citations, bibliography, and Scripture-reference conventions. It does not replace citations in a study note.

`Journal/` records dated observations and reading progress. Journal entries are chronological and may later inform durable knowledge pages.

`Docs/` records the repository's current architecture. Unnumbered core documents define system boundaries; numbered Design Book documents preserve the reading order of domain conventions and rationale. `Docs/README.md` is the authoritative task-to-document index.

Avoid adding a top-level directory until a recurring need makes its purpose obvious.
