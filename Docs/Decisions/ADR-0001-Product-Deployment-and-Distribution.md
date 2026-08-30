# ADR-0001: Product Boundary, Deployment Direction, and Distribution Stages

**Status:** Accepted
**Date:** 2026-08-30
**Deciders:** Project owner
**Related questions:** OQ-001, OQ-002, OQ-003

> Chinese review version:
> [`ADR-0001-Product-Deployment-and-Distribution-zh.md`](ADR-0001-Product-Deployment-and-Distribution-zh.md).

## Context

Christian Studies currently runs as a browser application plus a loopback local
service. This was the fastest way to discover and validate reading, annotation,
and AI-context requirements. The longer-term product may be introduced to a
reading group and, if useful to others, distributed more widely.

The architecture needs a primary boundary now without prematurely building
accounts, cloud synchronization, collaboration, or tenancy.

## Decision

### Product boundary

The first platform is a **local-first, single-reader personal environment**.
The trusted boundary is the user's machine. Identities and APIs should avoid
blocking a future multi-user design, but the platform will not implement cloud
accounts, synchronization, tenancy, or collaborative reading without a new
accepted product decision.

Interest from the project owner's reading group will inform whether a later
collaborative or broader-reader edition is worth pursuing.

### Runtime direction

Development continues with the current **browser plus loopback local service**
because it supports rapid implementation, testing, and iteration of core
requirements.

The intended first distributable product is a **desktop application built on a
web application substrate**. It should provide one application entry point for
local onboarding, book management, reading, notes, discussions, and AI-provider
configuration. Packaging technology and supported operating systems will be
selected in a later implementation specification.

“User registration” in the personal release means creating a local profile or
completing local onboarding. It does not create a remote account. API keys are
configured locally and must use the platform's approved secret-storage boundary.

### Distribution stages

1. **Personal stage:** the project owner uses the application locally. Durable
   content, annotations, and discussions may be Git-managed; temporary,
   generated, and derived data are excluded.
2. **Internal stage:** reading-group friends may deploy the application for
   themselves. Shared books and study resources may remain Git-managed, but
   each reader's annotations and discussions stay local and are not uploaded to
   the shared repository.
3. **External stage:** the distributed application contains no bundled books.
   It may contain Scripture resources whose distribution rights permit that
   use. Readers import their own Markdown, Word, EPUB, PDF, or other supported
   material through the approved ingestion pipeline.

Support for a format in the external product still depends on the accepted
ingestion specification and fixtures; this ADR does not expand first-release
format support beyond OQ-007.

## Consequences

- Local-first behavior, offline reading, and portable data remain design
  constraints.
- The current web implementation is a valid evolutionary base rather than a
  discarded prototype.
- Application APIs use stable identities and scoped resources, but avoid
  speculative multi-user infrastructure.
- A distributable desktop shell is a target, not an immediate refactor
  requirement.
- Git inclusion rules depend on the distribution stage and data ownership.
- Personal data must never enter a shared internal or external repository by
  default.
- Public or collaborative product work requires a new decision covering
  accounts, synchronization, conflicts, moderation, and sharing permissions.

## Rejected alternatives

- Building a hosted multi-user product as the first platform release.
- Treating the current browser development experience as the final packaging
  decision.
- Implementing accounts or cloud synchronization solely to preserve a possible
  future use case.

## Migration and validation

- Preserve current 《追寻敬虔》 behavior during application-shell extraction.
- Define stage-specific default ignore and export policies before the internal
  or external stage ships.
- Test that internal/external packages exclude personal notes, discussions,
  secrets, and unauthorized book content.
- Treat packaging and local secret storage as explicit acceptance areas for the
  desktop release.
