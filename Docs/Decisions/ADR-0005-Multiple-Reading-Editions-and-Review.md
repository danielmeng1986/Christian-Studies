# ADR-0005: Multiple Reading Editions and Reviewed Publication

**Status:** Accepted
**Date:** 2026-09-05
**Deciders:** Project owner
**Related question:** Direct product decision for the *A Quest for Godliness* chapter 05 pilot

> Chinese review version:
> [`ADR-0005-Multiple-Reading-Editions-and-Review-zh.md`](ADR-0005-Multiple-Reading-Editions-and-Review-zh.md).

## Context

The current book model and reader assume that each chapter has one normalized
Markdown text under `Reading/`. *A Quest for Godliness* will test a second
reading edition: a modern Simplified Chinese ChatGPT-assisted revision based on
the received Chinese translation and checked against a permissioned English
chapter supplied for personal use.

The received Word-derived Chinese text must remain available and must not be
silently replaced. Draft AI prose must not appear as approved author text.
Annotations and discussions contain exact text, offsets, and source revisions,
so they cannot be transferred automatically between editions.

## Decision

### Edition identity and authority

Every reading edition has a stable `editionId`. For the pilot:

- `legacy-zh` identifies the received Traditional Chinese Word-derived edition
  and remains the default;
- `chatgpt-zh-cn` identifies the modern Simplified Chinese, ChatGPT-assisted
  revised edition.

An edition is a separately reviewed reading-text authority. The English source
is the highest authority for authorial meaning in the revised edition; the
received Chinese edition remains the authority for its own wording and the
initial paragraph correspondence. A disagreement discovered during revision
must be recorded for review rather than hidden.

### Target directory and manifest

The target portable layout is:

```text
Books/<Book-Slug>/
├── Reading/
│   ├── <existing-part>/<legacy-chapter>.md
│   └── chatgpt-zh-cn/<chapter>.md
└── Metadata/
    ├── editions.json
    ├── Reading-Units/<editionId>/<chapterId>.json
    └── Edition-Reviews/<targetEditionId>/<chapterId>.json
```

`Metadata/editions.json` is the authoritative edition catalog. It declares the
default edition and each edition's identity, display name, language, source
edition, provenance, publication state, and explicit chapter paths/statuses.
Readers and services must not infer authority by scanning duplicate chapter
numbers.

The received default edition retains its existing paths so relative references,
source revisions, notes, and discussions do not change merely to normalize a
directory layout. New alternate editions use `Reading/<editionId>/<chapter>.md`.
The explicit manifest, rather than physical symmetry, defines edition
membership. No second chapter with the same unqualified `chapterId` may enter
ordinary reader discovery before discovery and validation honor edition and
publication status.

### Reading-unit and correspondence metadata

`Metadata/Reading-Units/<editionId>/<chapterId>.json` is a reviewable identity
sidecar, not a prose copy. It contains:

- `schemaVersion`, `bookId`, `editionId`, and `chapterId`;
- the Markdown path and its content revision;
- an ordered list of semantic blocks with stable UUID, block kind, ordinal,
  and content hash.

`Metadata/Edition-Reviews/<targetEditionId>/<chapterId>.json` records the
revision workflow and cross-edition correspondence. It contains:

- source and target edition/chapter identities and revisions;
- the revision-policy and terminology-glossary versions;
- model identity, generation timestamp, and reference-source locators;
- one record per aligned block with a stable `pairId`, source block UUID,
  target block UUID, source/target content hashes, review status, and review
  timestamps; and
- chapter publication status and approval timestamp.

The review sidecar must not contain complete source, target, or English prose.
The Markdown files remain the only authoritative prose copies. A changed block
hash invalidates that block's prior approval.

Reviewer change requests are append-only comments on aligned blocks. Each is
either open or resolved. Open comments prevent block and chapter approval;
target-text revisions return the block to draft while preserving its comments.
The review interface keeps authoritative prose read-only so comments and prose
changes remain distinguishable.

The review interface may display a permissioned English source as a read-only,
collapsible reference. For browser compatibility, a same-origin runtime proxy
may fetch the fixed recorded source URL into memory. The English PDF or complete
extracted text must not be persisted in the repository, review sidecar, or
generated reader output.

### Alignment and publication

The pilot preserves headings, block quotations, footnote references, paragraph
order, and a one-to-one semantic-block correspondence. Sentences may be split
or combined inside one Markdown paragraph; Markdown paragraphs may not be
split, merged, added, removed, or reordered without an explicit reviewed
alignment change.

Block workflow is `draft` → `reviewed` → `approved`. Material target-text edits
after approval invalidate the block approval. Publication is chapter-atomic:
an edition chapter becomes available in the ordinary reader only when every
required block is approved and chapter validation succeeds. Draft and reviewed
content remains available only in the review interface.

### Runtime identity and URLs

All edition-sensitive runtime identities are composite:

```text
(bookId, editionId, chapterId)
```

Annotations, discussions, revisions, retrieval units, context manifests, and
API routes must carry `editionId`. Exact text offsets must never be reused
across editions. Cross-edition navigation uses reviewed block correspondence.

An ordinary reader URL may select an approved edition explicitly. Omitting the
edition selects the manifest's default edition. Requesting an unpublished or
unavailable edition falls back to the default edition with a visible notice;
the review interface may open draft or reviewed content directly.

## Consequences

- The received edition remains readable and is not overwritten by AI output.
- The reader can add further editions without treating language as identity.
- Review decisions are auditable without creating another prose authority.
- Current note and discussion schemas require a migration before multi-edition
  writes are enabled.
- Current flat paths and unqualified chapter routes remain compatible until the
  coordinated migration is implemented.

## Validation and migration gates

Before publishing the first alternate edition:

1. validate `editions.json`, reading-unit sidecars, and review sidecars;
2. register current chapter paths as `legacy-zh` without moving or rewriting them;
3. update build, service, retrieval, notes, discussions, and context manifests
   to use composite identity;
4. preserve existing user data and map it explicitly to `legacy-zh`;
5. verify one-to-one block alignment and footnote-reference parity;
6. ensure unapproved editions cannot enter ordinary reader output; and
7. test explicit-edition URLs, default fallback, cross-edition navigation, and
   approval invalidation after edits.
