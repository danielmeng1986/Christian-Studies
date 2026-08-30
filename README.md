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
**AI-assisted reading environment**.

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

The backend is expected to own import, conversion, validation, indexing,
context assembly, model orchestration, and controlled tool or skill access. The
frontend is expected to become a multi-book workspace for importing, managing,
reading, annotating, discussing, and developing structured notes.

This direction is a planning target, not yet the current architecture. Major
refactoring begins only after the product boundaries and open architectural
questions have explicit decisions.

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

Current normative architecture remains under `Docs/`. The target proposal does
not authorize implementation changes by itself.

## Project status

The single-book environment is working and has been used for real reading. The
next stage is product and architecture planning: preserve what has already
proved valuable, extract book-independent contracts, decide the unresolved
boundaries, and only then begin the multi-book refactor.
