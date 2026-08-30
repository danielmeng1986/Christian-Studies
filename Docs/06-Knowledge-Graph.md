# 6. Knowledge Graph

The knowledge graph is the repository's network of ordinary Markdown links and citations. It is not a separate database in Version 1.0.

Reusable knowledge pages may describe:

- people and groups;
- concepts and theological terms;
- Scripture passages and themes;
- historical events; and
- timelines.

Pages belong in the directory that best describes their primary subject. A concept page might link to a person, several studied books, Scripture passages, and a historical event; it does not need to duplicate their content.

## Page conventions

Use a stable, descriptive filename and begin each page with a concise statement of scope. Include links to supporting book chapters or references for significant claims. Prefer a small page that can grow over a comprehensive page created too early.

Book-specific interpretation remains in `Books/<book>/Notes/` unless it has value beyond that book. When promoting an insight to a reusable page, preserve its provenance with a link back to the original note or reading chapter.

Future versions may add index pages, structured relationships, or semantic linking. Any such addition must continue to expose its evidence in human-readable Markdown.

## Accepted evolution direction

Accepted knowledge entities will use stable IDs, human-readable Markdown pages, aliases, and evidence links. AI-created structure remains a proposal until the reader accepts or edits it. Ambiguous entity merges require review; a matching label does not prove identical meaning.

Graph and search stores remain derived projections of accepted knowledge by default. A Graph database is a candidate implementation, not an accepted source of truth. Engine selection remains open in [`Open-Questions.md`](Open-Questions.md#oq-017-knowledge-graph-projection-engine) and [`Open-Questions-zh.md`](Open-Questions-zh.md#oq-017-知识图谱投影引擎).
