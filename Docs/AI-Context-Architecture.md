# AI Context Architecture

**Status:** Core normative specification  
**Scope:** AI-assisted discussion, retrieval, and context generation

This document defines how repository material may become AI context. It is a
repository-wide boundary; book-local context specifications define exact
schemas and UI behavior.

## 1. Context is a derived view

An AI context bundle is assembled for a specific question from declared source
files and user selections. It is not an authoritative content store and must
not become the only copy of evidence, notes, consent, or discussion history.

Context assembly must be:

- **source-linked** — every retained evidence fragment can be traced to a file,
  record, URL, or stable identifier;
- **typed** — author text, references, user notes, retrieved sources, and model
  output remain distinguishable;
- **revision-aware** — mutable inputs are identified by a revision or content
  hash when stale context would matter;
- **deterministic where practical** — identical inputs and options produce the
  same evidence selection;
- **visible** — optional evidence and external transmission are reviewable by
  the user; and
- **read-only by default** — building or previewing context does not modify its
  sources.

## 2. Evidence order

The default order is:

1. developer behavior instructions;
2. declared book identity;
3. current reading focus and selected passage;
4. current chapter, linked footnotes, and Scripture snapshots;
5. selected personal notes, clearly labeled as user material;
6. local reference resolution, such as translation-name matches;
7. relevant passages retrieved from the same book;
8. user-approved supplemental library fragments;
9. explicitly enabled external research;
10. discussion history and the current question.

This is an evidence and presentation order, not a claim that later categories
are less true in every circumstance. The model must state conflicts and
uncertainty rather than silently merging sources.

## 3. Trust and instruction boundary

Content is not instruction. Treat all of the following as untrusted data even
when it is repository-local:

- reading text and quotations;
- footnotes and bibliography text;
- user notes and discussion history;
- imported supplemental sources;
- retrieved web pages and external documents; and
- text embedded in indexes or metadata values.

Only the application/developer instruction layer may define model behavior.
Text inside evidence that asks the model to ignore rules, reveal secrets, use a
tool, or alter files must not be executed as instruction.

## 4. Source and index boundaries

Context may read these durable sources:

- `Reading/` for normalized book text;
- `References/` for linked evidence and identity resolution;
- `Metadata/` for declared identity and configuration;
- selected `Notes/` records for personal study context; and
- selected `Sources/Originals/` or `Sources/Processed/` records according to
  registry and consent state.

Retrieval units, indexes, rankings, previews, token estimates, and short-lived
server-side context builds are derived. In particular:

- deleting an index must not delete or modify its sources;
- an index must be rebuildable from declared inputs;
- an index hit must resolve back to a durable source fragment;
- source revisions must invalidate stale evidence where correctness requires
  it; and
- generated HTML is not a context authority when Markdown is available.

## 5. Personal data and consent

User notes may be included only when relevant to the current operation and must
be labeled `user_note` or an equivalent explicit type. Exact and overlapping
notes may be defaults if the UI shows and permits exclusion; unrelated notes
must not be silently added.

Supplemental library material has two gates:

1. the source must be eligible for outbound use according to its durable
   registry state; and
2. the exact fragment must be selected for the current request.

An index or processed projection must not broaden consent inherited from its
original. Preview choices affect the current request unless the user explicitly
changes durable consent. External search and other tools remain off unless the
user enables them for the operation.

## 6. Provenance and manifests

Persisted discussion turns should retain enough evidence metadata to explain
what the model saw without copying every durable source into the discussion
record. Depending on the schema, this may include:

- context and prompt schema versions;
- source paths or IDs;
- chapter, block, anchor, and heading identity;
- content revisions or hashes;
- included and excluded evidence IDs;
- external tool use and URLs; and
- truncation, overflow, or unresolved-source state.

Do not invent provenance for legacy turns. Mark unavailable evidence metadata
as legacy or unknown.

## 7. Failure behavior

Context generation must fail visibly rather than:

- inventing missing metadata;
- presenting an index excerpt that cannot resolve to its source;
- silently truncating required evidence or history;
- substituting stale source text after a revision mismatch;
- merging ambiguous identities without user-visible resolution; or
- transmitting a source without the required consent.

Failure to find relevant evidence is a valid empty result, not permission to add
weakly related material to fill a quota.

## 8. Current implementation

For 《追寻敬虔》, the execution-level schema and roadmap are defined by:

- [`AI-CONTEXT-SPEC.md`](../Books/追寻敬虔/Web/AI-CONTEXT-SPEC.md);
- [`AI-CONTEXT-SPEC-zh.md`](../Books/追寻敬虔/Web/AI-CONTEXT-SPEC-zh.md);
- [`AI-CONTEXT-ROADMAP-zh.md`](../Books/追寻敬虔/Web/AI-CONTEXT-ROADMAP-zh.md); and
- [`AI-CONTEXT-HANDOFF-zh.md`](../Books/追寻敬虔/Web/AI-CONTEXT-HANDOFF-zh.md).

The implementation lives primarily in `Web/scripts/context_builder.py`,
`Web/scripts/context_retrieval.py`, `Web/scripts/local_library.py`, and the
validated service APIs. Changes must run the context, retrieval, discussion,
library, and API tests selected by [`Validation.md`](Validation.md).
