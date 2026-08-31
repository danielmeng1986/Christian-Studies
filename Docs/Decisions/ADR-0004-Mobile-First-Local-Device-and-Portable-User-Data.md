# ADR-0004: Mobile-First Local Device and Portable User Data

**Status:** Accepted
**Date:** 2026-08-31
**Deciders:** Project owner
**Related questions:** OQ-001, OQ-002, OQ-003, OQ-018, OQ-019
**Amends:** ADR-0001 runtime direction and first-distributable target

> Chinese review version:
> [`ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md`](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md).

## Context

Real use of the current reader has shown that the durable product opportunity is
larger than a desktop theology application. Christian Studies is the first
domain profile for a personal AI-assisted reading environment that may later
serve language learning and other serious reading. The device used most often
for that work is expected to be an iPhone.

ADR-0001 correctly established a local-first, single-reader product and kept
the browser plus loopback service as the current development runtime. Its
desktop-first distributable target no longer reflects the product priority.

## Decision

### Product and runtime direction

The long-term product direction is a **local-first, mobile-first personal AI
reading environment**. Christian Studies remains its first real domain and the
current 《追寻敬虔》 Reader remains the compatibility baseline.

The first dedicated device target is a fully local iPhone application that can
read and manage its core data without a Mac backend. Reading, local search,
local Bible and dictionary lookup, notes, highlights, saved discussions, and
accepted knowledge should remain useful offline. Network access is required
only for explicitly networked capabilities such as an OpenAI API call.

The current browser plus loopback service remains the development and discovery
runtime. This decision does not authorize an immediate native rewrite or
platform extraction. A representative second real use case must first show
which contracts are genuinely reusable.

### First-stage boundaries

The first personal mobile stage does not require:

- App Store distribution or public users;
- a remote account or Google login;
- a cloud backend or hosted source of truth;
- a running Mac server; or
- mandatory iCloud synchronization.

It uses one local profile. Future Apple, Google, or other sign-in systems may be
identity providers, but must not replace an internal stable profile identity.

### Secret boundary

The user supplies their own provider credential. On iOS it is stored only in
Keychain; other platforms must use an equivalent approved secret store. Content
files, ordinary configuration, SQLite fields, context manifests, discussions,
exports, logs, and command arguments must never contain the credential.
Non-secret configuration may record provider identity and whether a credential
is configured.

### Managed content and user data

The first personal build may bundle legally permitted books, Bible resources,
dictionaries, grammar references, and other trusted materials as managed
content. Reading progress, highlights, notes, discussions, saved language
items, accepted knowledge, and preferences are mutable user-owned data. An
application update must not replace or erase that user data.

The device-local copy is authoritative for first-stage user data. Runtime
storage may use local SQLite, but long-term portability must not depend on
copying an opaque database file. The first migration capability is an explicit,
versioned export/import package with a manifest and human-readable records where
practical. Export/import precedes automatic synchronization.

Durable user entities should use stable identities. Revision, device, and
deletion metadata needed by a future change-based synchronization protocol must
be specified before that protocol is implemented; this decision does not force
an immediate rewrite of current user-data schemas.

A portable discussion is more than a message list. Its durable record must keep
a stable discussion identity, book and anchor/selection identity, timestamps,
model metadata, messages, selected-context references, and an evidence manifest
where available. Optional titles or summaries may aid recall, but must not
replace the recorded evidence provenance. Legacy records must not be assigned
invented context metadata.

### Cloud role

If cloud infrastructure is introduced later, it may provide transport,
replication, or backup. It must not become the only authoritative copy of
personal knowledge. Automatic sync, LAN transfer, conflict resolution, and
multi-device identity require separate accepted specifications before
implementation.

## Consequences

- Mobile interaction and narrow-screen behavior become core product concerns,
  but current responsive behavior remains the only implemented baseline.
- Desktop packaging is no longer the first dedicated-device release gate. It
  remains a possible later client using the same portable contracts.
- Portable user data and secure local credentials are acceptance areas for the
  first mobile implementation.
- Export/import is intentionally simpler than sync and must be validated before
  any automatic replication work.
- Bundling a source depends on its rights and visibility metadata; this ADR does
  not grant redistribution rights.
- Platform and native-app implementation remain gated by real-use evidence,
  compatibility fixtures, and the open contracts referenced below.

## Rejected alternatives

- Requiring the Mac loopback service for normal iPhone reading.
- Making a remote account or cloud database the first-stage user-data authority.
- Starting with automatic synchronization or whole-SQLite replacement.
- Treating mobile-first as merely a narrower desktop layout.
- Beginning a general platform rewrite before a second representative use case.

## Follow-up decisions and validation

- OQ-018 defines the native mobile interaction and application boundary before
  implementation begins.
- OQ-019 defines the portable export/import package, merge behavior, recovery,
  and compatibility policy.
- Dictionary and language-learning contracts remain separate open questions;
  they are not silently added to the Christian Studies domain model.
- Compatibility tests must preserve the current Reader's reading, notes,
  discussions, context, and evidence-manifest behavior.
- Mobile acceptance tests must cover offline use, update-safe user data,
  Keychain isolation, export/import round trips, and failure recovery.
