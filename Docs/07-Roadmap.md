# 7. Roadmap

**Status:** Current strategic summary

The roadmap describes staged direction, not a commitment to build every possible feature or a schedule. The detailed bilingual plan is maintained in [`Product-Plan.md`](Product-Plan.md) and [`Product-Plan-zh.md`](Product-Plan-zh.md).

## Established foundation

《追寻敬虔》 has moved beyond the original foundation milestone. The repository now has:

- a preserved Word source and reviewed Markdown reading edition;
- deterministic generation of all chapters into a local interactive reader;
- footnote and Scripture interaction;
- Git-readable, revision-aware annotations and discussions;
- a working source-aware `ContextBuilder` with visible evidence selection;
- cross-chapter retrieval and a permission-aware supplemental library; and
- repository-level architecture, content, context, and validation contracts.

This working reader is the compatibility baseline for future refactoring.

## Current stage — Decide before restructuring

The current stage is product and target-architecture planning:

- preserve the project history and product insight in the root README;
- define a multi-book product plan and target architecture proposal;
- inventory current behavior and create compatibility fixtures;
- decide product, storage, Markdown, package, and database boundaries; and
- define migration and rollback before moving durable files.

The decision queue is [`Open-Questions.md`](Open-Questions.md), with a Chinese review version in [`Open-Questions-zh.md`](Open-Questions-zh.md).

## Planned sequence

1. **Extract domain contracts.** Define book-independent identities, schemas, interfaces, and policy checks around the working implementation.
2. **Build a reviewed ingestion pipeline.** Preserve originals, adapt supported formats, expose conversion diagnostics, and publish Markdown only after approval.
3. **Create the multi-book application shell.** Add a catalog, import/review workspace, shared reader, and book-independent validated APIs.
4. **Generalize the Context Service.** Separate discovery, ranking, selection, budgeting, preview, rendering, and evidence manifests.
5. **Add evaluated model routing.** Balance quality, cost, latency, privacy, and user preference without obscuring context.
6. **Add controlled MCP and skill capabilities.** Use explicit registration, least privilege, consent, and provenance.
7. **Develop reviewed structured knowledge.** Turn notes and discussions into evidence-linked proposals and cross-book knowledge through human acceptance.

## Advancement rules

- Advance by exit criteria and real-use evidence, not by date alone.
- Keep the current reader usable throughout migration.
- Do not combine directory, schema, UI, model, and product migrations into one change.
- Treat target-architecture documents as proposals until their prerequisite decisions are accepted and current normative documents are updated.
- Add a second representative book before claiming that an abstraction is truly book-independent.
