# ADR-0003: Stable Block Identity with Precise Range Selectors

**Status:** Accepted
**Date:** 2026-08-30
**Deciders:** Project owner
**Related question:** OQ-008

> Chinese review version:
> [`ADR-0003-Stable-Block-Anchoring-zh.md`](ADR-0003-Stable-Block-Anchoring-zh.md).

## Context

The current reader derives block IDs from rendered block order, then stores
offsets, exact text, prefix/suffix context, and a source revision. This supports
precise selection but neighboring insertions can renumber later blocks.

Sentence-level UUIDs could give finer identity, but sentence segmentation is
language- and punctuation-sensitive, would increase identity volume, and would
force the note model to treat sentence boundaries as editorial truth. Paragraph
or semantic-block identity solves the main insertion problem without removing
precise selection.

## Decision

The durable anchor container is a **reviewed semantic block**, normally a
paragraph, heading, list item, or quotation paragraph. Each block receives a
stable opaque UUID that is preserved across builds and ordinary edits.

An annotation or discussion anchor contains:

- stable reading-unit ID;
- stable block UUID, or an ordered list of block UUIDs when cross-block anchors
  are supported;
- exact selected text;
- offsets within the canonical block text when the selection is a subrange;
- prefix and suffix context;
- source revision or content hash; and
- anchor schema version.

Notes are not required to cover the entire paragraph. The stable block UUID
provides durable location, while quote/range selectors preserve the reader's
precise selection. The first generalized schema may continue to allow only one
block per annotation; cross-block support requires an explicit schema extension
and tests.

Persistent sentence UUIDs are not required in the first platform model.
Sentence segmentation may be a derived reading or AI feature. It can become a
durable identity layer later only through a new decision supported by actual
use.

The UUID's physical representation in authoritative Markdown—inline attribute,
sidecar identity map, or another reviewable mechanism—will be selected in the
versioned Reading Document Model specification. That choice must preserve
Markdown authority and avoid a separately maintained prose copy.

## Recovery behavior

1. Resolve the reading unit and stable block UUID.
2. Verify offsets against exact text and the source revision.
3. Recover a unique exact/contextual match inside the same block when the block
   was edited.
4. Search other blocks only as an explicit migration or relocation operation.
5. If no unique match exists, retain the user data as unresolved and never draw
   a misleading highlight.

Inserting or moving neighboring blocks must not change an existing block UUID.
Splitting, merging, duplicating, or substantively replacing a block requires an
explicit identity rule and may require anchor migration.

## Consequences

- An insertion before a paragraph no longer invalidates that paragraph's
  durable identity.
- Precise text selection remains available without assigning a UUID to every
  sentence.
- Import and editing workflows must preserve block UUIDs intentionally.
- UUID generation alone does not eliminate revision checks or quote context.
- The Reading Document Model must define canonical block text and identity
  preservation before current order-based IDs are migrated.

## Rejected alternatives

- Rendering-order block IDs as the long-term durable identity.
- DOM paths as persistent anchors.
- Requiring all notes to attach only to a whole paragraph.
- Requiring a persistent UUID for every sentence in the first platform release.

## Migration and validation

- Add stable UUIDs without rewriting user notes in place.
- Build a mapping from current deterministic block IDs to stable UUIDs against a
  pinned source revision.
- Preserve current quote, offsets, context, and source hashes during migration.
- Test insertions, deletions, block moves, splits, merges, duplicate text, and
  ambiguous recovery.
- Keep a recoverable migration record and never discard unresolved anchors.
