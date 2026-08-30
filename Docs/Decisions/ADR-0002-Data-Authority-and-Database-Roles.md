# ADR-0002: Data Authority, Git Policy, and Database Roles

**Status:** Accepted
**Date:** 2026-08-30
**Deciders:** Project owner
**Related questions:** OQ-003, OQ-006, OQ-014

> Chinese review version:
> [`ADR-0002-Data-Authority-and-Database-Roles-zh.md`](ADR-0002-Data-Authority-and-Database-Roles-zh.md).

## Context

The current personal project uses portable Markdown and JSON files, with Git
history for durable study content and user data. The target platform also needs
a book catalog, platform-managed metadata, retrieval, jobs, and later possibly a
different durable store for annotations and discussions.

The statement “the database is the Source of Truth” is too broad unless
authority is assigned per entity. A database can contain both authoritative
records and fully rebuildable projections at the same time.

## Decision

### Authority is declared per entity

Every schema or table must declare one of these roles:

- **authoritative:** the record is the durable Source of Truth and requires
  backup, migration, export, and conflict rules;
- **derived:** the record is rebuilt from declared authoritative inputs; or
- **operational:** the record coordinates local work, such as a job or cache,
  and has an explicit recovery policy.

The storage engine itself is never globally authoritative merely because a
record is stored in it.

### Current personal stage

- Preserved originals, reviewed Markdown, references, current book metadata,
  annotations, and discussions remain file authorities.
- These durable files may be managed in Git for the project owner's personal
  installation.
- Temporary files, generated HTML, caches, processed projections, and retrieval
  indexes remain excluded or rebuildable.

This ADR does not immediately migrate current `Metadata/book.yml`, annotations,
or discussions.

### Target SQLite roles

The platform may introduce a new local SQLite database now for:

- the authoritative platform Book Catalog;
- authoritative platform-managed book metadata after an explicit, tested
  migration from current file metadata;
- operational import/build/migration job state; and
- derived full-text, retrieval, and catalog projections.

Search and retrieval entries remain **derived**, even when stored in the same
SQLite database as authoritative catalog or metadata records. Their truth is the
reviewed content and declared reference inputs, and they must be rebuildable.

When book metadata moves to SQLite authority, the platform must provide a
documented export or portable package representation. Until that migration is
implemented and validated, current file metadata remains authoritative.

### User-data persistence

Annotations and discussions remain schema-versioned JSON file authorities in
the personal stage. The internal or external product may later move them to a
database that preserves their JSON document semantics, revisions, export, and
portability. The specific engine and migration contract remain open under
OQ-016.

“Native JSON support” is an evaluation criterion for that future decision, not
an accepted database selection in this ADR.

### Knowledge graph persistence

Accepted knowledge uses stable IDs, human-readable Markdown, aliases, and
evidence links under OQ-014. Graph and search stores are derived projections by
default. A graph database is a valid candidate for the projection layer, but
engine selection and measured justification remain open under OQ-017.

## Consequences

- SQLite may contain a mix of authoritative, derived, and operational tables;
  each schema must label its role.
- Backup and migration requirements apply to authoritative tables, while
  rebuild tests apply to derived tables.
- A failed or deleted retrieval index cannot destroy book content.
- The current file-based reader remains valid during platform extraction.
- A future user-data database must include lossless export and tested migration;
  convenience of JSON storage alone is insufficient.
- A future graph database cannot silently replace human-readable accepted
  knowledge without a new decision.

## Rejected alternatives

- Declaring every record in one database authoritative.
- Moving current notes and discussions immediately, before the internal or
  external persistence requirements are known.
- Treating a retrieval or graph index as the only copy of book text or accepted
  knowledge.

## Migration and validation

- Publish schemas and role labels before creating platform tables.
- Test authoritative database backup, export, schema migration, and recovery.
- Test deterministic rebuilding of search, retrieval, and graph projections.
- Run a dual-read comparison before changing metadata authority from files to
  SQLite; avoid indefinite dual-write authority.
- Keep current user-data files untouched until OQ-016 is accepted and a
  backward-compatible migration exists.
