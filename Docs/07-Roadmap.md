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

## Current stage — Use, observe, and batch

The current Reader is a real product baseline, not a demo waiting to be
replaced. The immediate work is to continue reading 《追寻敬虔》, record problems,
and wait until they form coherent batches. No implementation phase starts merely
to complete this roadmap.

The accepted target direction is now a local-first, mobile-first personal AI
reading environment. Christian Studies is its first Domain Profile; language
learning is the leading candidate second profile. The current browser plus
loopback service remains the development and compatibility runtime, while the
first dedicated-device target is a self-contained iPhone application. This
direction does not authorize an immediate native rewrite.

Accepted records are indexed in
[`Decisions/README.md`](Decisions/README.md); remaining questions are in
[`Open-Questions.md`](Open-Questions.md) and
[`Open-Questions-zh.md`](Open-Questions-zh.md).

## Platform-extraction gate

Platform extraction begins only after a second representative real use case,
preferably an English or German non-theological book, has been genuinely used.
That use must show which Reading Core, anchor, annotation, discussion, Context,
search, and Source Provider contracts are shared and which belong in Domain
Profiles.

Before structural work begins:

- inventory the current Reader behavior and create compatibility fixtures;
- select and use the second representative book;
- define only the smallest contracts supported by both workflows;
- document migration and rollback for authoritative and user-owned data; and
- keep the current Reader usable as the compatibility baseline.

## Candidate sequence after the gate

1. **Extract evidence-tested contracts.** Define shared identities, schemas, interfaces, and policy checks around the working implementation while keeping Christian Studies and Language Learning Domain Profiles distinct.
2. **Build a reviewed ingestion pipeline.** Preserve originals, adapt supported formats, expose conversion diagnostics, and publish Markdown only after approval.
3. **Create the multi-book application boundary.** Add a catalog, import/review workspace, shared Reader contracts, and book-independent validated APIs without selecting a native framework prematurely.
4. **Prove portable user data.** Separate managed content from mutable user data and implement versioned export/import with stable identities, conflict handling, recovery, and secret exclusion.
5. **Generalize the Context Service and Source Providers.** Separate discovery, ranking, selection, budgeting, preview, rendering, evidence manifests, and typed provider evidence.
6. **Build the scoped mobile client.** Implement the accepted offline, device-local iPhone slice only after OQ-018, OQ-019, and OQ-022 are resolved and compatibility behavior is fixed.
7. **Add evaluated model routing.** Balance quality, cost, latency, privacy, and user preference without obscuring context.
8. **Add controlled MCP and skill capabilities.** Use explicit registration, least privilege, consent, and provenance.
9. **Develop reviewed structured knowledge.** Turn notes and discussions into evidence-linked proposals and cross-book or cross-domain knowledge through human acceptance.

## Advancement rules

- Advance by exit criteria and real-use evidence, not by date alone.
- Keep the current reader usable throughout migration.
- Do not combine directory, schema, UI, model, and product migrations into one change.
- Treat target-architecture documents as proposals until their prerequisite decisions are accepted and current normative documents are updated.
- Add a second representative book before claiming that an abstraction is truly book-independent.
- Treat mobile-first as a product priority, not permission to compress a desktop
  UI or discard current behavior.
- Keep reading, local search, trusted-source lookup, notes, and saved history
  useful offline; isolate provider credentials in approved secret storage.
- Implement explicit export/import before LAN or cloud synchronization; never
  use whole-database replacement as the long-term sync protocol.
- Batch real problems into coherent themes instead of running a continuous
  fix/tweak/refactor loop.
