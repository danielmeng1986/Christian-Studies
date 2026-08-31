# Christian Studies

> An AI-assisted reading environment built on transparent, controllable
> context.

[中文说明](README-zh.md)

Christian Studies began as a Git-managed place for thoughts and notes produced
while reading Christian books. Its first book, J. I. Packer's *A Quest for
Godliness* (《追寻敬虔》), arrived as a legacy Word manuscript. That source was
difficult to navigate and annotate during sustained reading, so it was
normalized into Markdown. Markdown improved reading and version control; a
deterministic HTML reader then added interactions that plain Markdown could not
provide.

The project now supports selecting text to write notes, opening footnotes and
Scripture passages in place, and discussing a passage with AI. Its most
important result is not a particular model integration. It is the ability to
control the evidence sent to the model through a source-aware `ContextBuilder`.
In real use, carefully selected local context has produced answers that are more
accurate, focused, and useful even without web access.

The project is therefore evolving from a single-book reader into an
**AI-assisted reading environment**. Christian Studies is its first real Domain
Profile; language learning is the leading candidate second use case.

## Current capabilities

The working 《追寻敬虔》 reader currently provides:

- deterministic generation of all 20 chapters from reviewed Markdown;
- chapter navigation and responsive reading layouts;
- interactive footnotes and Scripture passages;
- Git-tracked, revision-aware annotations;
- persistent AI discussion threads;
- visible, source-linked context previews;
- cross-chapter retrieval and name resolution;
- an opt-in supplemental local library with rebuildable indexes; and
- local serving that keeps API credentials out of the browser and repository.

The implementation and run instructions are in the
[`Books/追寻敬虔/Web` README](Books/追寻敬虔/Web/README.md).

## Product direction

The intended platform will eventually support a complete book-study lifecycle:

```text
Import source
    ↓
Preserve and normalize to reviewed Markdown
    ↓
Validate and build an interactive reading edition
    ↓
Read, annotate, and discuss with source-aware AI
    ↓
Develop reviewed, structured knowledge across books
```

The future Reading Core may own import, conversion, validation, indexing,
context assembly, typed Source Providers, model orchestration, and controlled
tool or skill access. Domain Profiles keep Christian Studies and future
language-learning behavior distinct. These boundaries are extracted only after
a second representative real use case validates them.

The accepted first-product boundary is local-first and single-reader.
Development and discovery continue through the browser plus loopback service;
the first dedicated-device target is a self-contained iPhone application, with
desktop as a possible later client. Local-first means the active device owns
core reading capability and authoritative personal data, not that a Mac server
must always run. Export/import precedes synchronization, and cloud remains
optional infrastructure rather than the owner of personal knowledge.

This direction is a planning target, not yet the current architecture. Major
refactoring proceeds only through accepted decisions, compatibility fixtures,
versioned contracts, and migration plans.

## Core principles

- Preserve original sources and provenance.
- Keep reviewed Markdown authoritative for normalized reading content unless a
  future decision explicitly changes that rule.
- Treat generated HTML and indexes as disposable outputs.
- Treat notes and discussions as user data.
- Make AI context visible, typed, source-linked, and revision-aware.
- Improve answer quality through evidence selection before escalating model
  cost or complexity.
- Keep model providers, MCP tools, and skills behind explicit capability and
  consent boundaries.
- Refactor incrementally while the current reader remains usable.
- Keep device-local user data portable and provider credentials inside approved
  secret storage.
- Generalize only after a second real use case demonstrates the shared contract.

## Documentation

- [`AGENTS.md`](AGENTS.md) — mandatory working entry point for agents.
- [`Docs/README.md`](Docs/README.md) — authoritative documentation map.
- [`Docs/Product-Plan.md`](Docs/Product-Plan.md) — product phases and refactoring
  plan ([中文](Docs/Product-Plan-zh.md)).
- [`Docs/Platform-Architecture-Proposal.md`](Docs/Platform-Architecture-Proposal.md)
  — proposed target architecture
  ([中文](Docs/Platform-Architecture-Proposal-zh.md)).
- [`Docs/Open-Questions.md`](Docs/Open-Questions.md) — decisions required before
  major refactoring ([中文](Docs/Open-Questions-zh.md)).
- [`Docs/Decisions/README.md`](Docs/Decisions/README.md) — accepted architecture
  decision records.

Current normative architecture remains under `Docs/`. The target proposal does
not authorize implementation changes by itself.

## Project status

The single-book environment is working and has been used for real reading. The
current stage is to keep reading 《追寻敬虔》, record issues, and batch them when a
coherent theme emerges. A representative English or German second book must be
used before shared contracts or platform extraction are claimed. Native mobile,
portable-data, dictionary/grammar Source Provider, language-knowledge, and
managed-content details remain gated decisions rather than an active rewrite.
