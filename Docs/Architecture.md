# Repository Architecture

**Status:** Core normative specification  
**Scope:** Entire repository

This document defines the repository's structural truth and system boundaries.
`AGENTS.md` ensures that work enters this documentation set; this document says
what the major parts of the repository own.

## 1. Architectural layers

Christian Studies has five distinct layers:

1. **Governance** — `AGENTS.md` and `Docs/` define working rules and architecture.
2. **Study content** — preserved originals, normalized reading Markdown,
   references, metadata, and reusable knowledge are durable repository content.
3. **User data** — notes, annotations, and discussions record reader-created
   state and must not be overwritten by builds.
4. **Implementation** — application source, runtime services, generators, and
   tests implement repository behavior.
5. **Derived and generated data** — indexes, processed projections, and built
   reader assets are reproducible outputs, never independent sources of truth.

The layers may depend downward on declared inputs, but generated data must not
become the only location of information that cannot be reconstructed.

## 2. Top-level structure

```text
Christian-Studies/
├── AGENTS.md
├── Docs/
├── Books/
├── Notes/
├── People/
├── Concepts/
├── Scripture/
├── References/
└── Journal/
```

Not every durable-knowledge directory needs to exist before it contains useful
material. Adding a new top-level directory requires a recurring responsibility
that does not fit an existing one and an update to this document and
[`02-Repository-Structure.md`](02-Repository-Structure.md).

## 3. Canonical book boundary

A book is an independently understandable study unit under `Books/<Book-Slug>/`:

```text
Books/<Book-Slug>/
├── Original/       # preserved primary book files
├── Reading/        # authoritative normalized reading Markdown
├── References/     # curated book-specific evidence and reference records
├── Metadata/       # curated identity, configuration, and provenance
├── Notes/          # user-authored study state
├── Sources/        # optional supplemental local-library materials
└── Web/            # optional reader implementation and generated site
```

`Original/` and `Sources/` have different responsibilities. `Original/` holds
the primary edition from which `Reading/` was normalized. `Sources/` is an
optional local library of later supplemental material and may contain preserved
imports, processed projections, a registry, and rebuildable indexes. They must
not be collapsed into an ambiguous `Source/` directory without a documented
migration that updates metadata, code, tests, and links together.

`Sources/` and `Web/` are optional capabilities, not requirements for every
book. The five durable study areas—`Original/`, `Reading/`, `References/`,
`Metadata/`, and `Notes/`—remain the base format.

## 4. Authority is domain-specific

There is no single file that is authoritative for every question:

- `Original/` is authoritative evidence for the wording and structure of the
  received primary source.
- `Reading/**/*.md` is authoritative for the normalized text shown by the
  reader and used in discussion.
- `Metadata/` is authoritative for declared book identity and configuration.
- `References/` is authoritative for curated footnotes, bibliography records,
  Scripture configuration links, and name mappings in its declared scope.
- `Notes/` is authoritative for the user's saved study state, not for claims
  about the book.
- `Web/src/` and `Web/scripts/` are authoritative for reader behavior.
- `Web/dist/` and index files are not authoritative; they are outputs.

When authorities disagree, preserve the disagreement and investigate its
provenance. For example, an extraction error is corrected in `Reading/` with a
traceable normalization record; the original file is not rewritten.

## 5. Dependency direction

```text
Original ──normalize──> Reading ───────────┐
Metadata ──────────────────────────────────┤
References ────────────────────────────────┼──> Reader build ──> Web/dist
Web/src + Web/scripts ─────────────────────┘

Reading + References + Metadata + selected Notes + selected Sources
                           └──> context assembly / retrieval

Sources/Originals ──convert──> Sources/Processed ──index──> Sources/Indexes
```

Builds may read user data when required for runtime validation, but they must
not replace, normalize, or delete it as a side effect. Context assembly is a
read-only projection except for explicitly saved user discussions or library
operations requested through their owning workflow.

## 6. Change rules

- Change an authoritative input when the content itself is wrong.
- Change a generator or implementation when an output is wrong but its input is
  correct.
- Regenerate an output after changing its input; never repair the output by
  hand.
- Update a governing document in the same change when a responsibility,
  canonical path, schema ownership, or dependency direction changes.
- A rename of a canonical directory is a migration, not a cosmetic cleanup. It
  must update all metadata paths, code constants, tests, documentation, and
  stored references atomically.

## 7. Specification boundaries

The core documents divide responsibility as follows:

- [`Content-Model.md`](Content-Model.md) defines data classes, ownership,
  provenance, and editability.
- [`Reader-Architecture.md`](Reader-Architecture.md) defines the generated local
  reader and runtime write boundaries.
- [`AI-Context-Architecture.md`](AI-Context-Architecture.md) defines context,
  retrieval, trust, consent, and derived indexes.
- [`Validation.md`](Validation.md) defines how rules are checked and which checks
  currently exist.

The numbered Design Book documents refine reading, reference, workflow, and
knowledge conventions. Book-local specifications may refine an implementation
but may not redefine repository-level ownership.

## 8. Known legacy placement

`Books/追寻敬虔/` predates parts of this contract and currently retains a small
number of source-related Word files at the book root as well as implementation
planning documents under `Metadata/`. Their presence records repository history;
it does not establish additional canonical locations.

Do not move, rename, or reclassify these files during unrelated work. A cleanup
must first identify each file's ownership and references, choose its canonical
destination, update all dependent metadata and tooling, and verify the migration
as a dedicated change.
