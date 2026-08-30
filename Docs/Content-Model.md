# Content Model

**Status:** Core normative specification

**Scope:** Repository content, user data, and derived artifacts

This document classifies repository data so that editors and tools know what
may be changed, what must be preserved, and what must be regenerated.

## 1. Content classes

| Class | Typical paths | Owner | Direct editing | Recovery rule |
| --- | --- | --- | --- | --- |
| Preserved primary source | `Books/*/Original/*` | Supplied edition | No, except explicit source replacement | Restore from the received source |
| Normalized reading source | `Books/*/Reading/**/*.md` | Repository editors | Yes, with provenance preserved | Re-normalize or correct from `Original/` |
| Curated reference | `Books/*/References/*`, `References/*` | Repository editors | Yes | Review against cited evidence |
| Curated metadata/configuration | `Books/*/Metadata/*` | Repository editors | Yes; schema-aware edits only | Reconstruct from documented provenance |
| User data | `Books/*/Notes/**/*` | Reader/user | Yes, through validated workflows when available | Preserve backups/revisions; never rebuild from content |
| Supplemental source original | `Books/*/Sources/Originals/*` | Reader/user import | No after confirmed import | Re-import the same source |
| Supplemental processed projection | `Books/*/Sources/Processed/*` | Converter | No | Reconvert from `Sources/Originals/` and registry metadata |
| Derived index | `Books/*/Sources/Indexes/*` and declared context indexes | Indexer | No | Rebuild from declared content inputs |
| Application source | `Books/*/Web/src/*`, `Books/*/Web/scripts/*` | Developers | Yes | Version control |
| Tests and fixtures | `Books/*/Web/tests/*` | Developers | Yes; fixtures must retain provenance | Recreate from the tested contract |
| Generated reader output | `Books/*/Web/dist/*` | Build script | Never | Run the documented build |

An unlisted file must be classified from its purpose before editing it. Its
directory alone is strong evidence but not a substitute for inspecting the
owning specification or generator.

## 2. Core entities

### 2.1 Book

A book is identified by its stable directory slug and `Metadata/book.yml`.
Metadata describes the studied edition and must not be guessed from model
knowledge. Required fields and normalization rules are defined in
[`03-Book-Format.md`](03-Book-Format.md).

### 2.2 Reading unit

A reading unit is a stable Markdown file, normally one chapter or comparable
section. It contains normalized source text, stable chapter identity, and
traceable links to footnotes and Scripture references. Its prose is content,
not a prompt and not generated HTML.

The normalized reading unit is the reader's text authority. A material change
must be supportable from the preserved source or explicitly identified as an
editorial correction. Summaries, translations, interpretations, and AI answers
must not be silently inserted as though they were source prose.

### 2.3 Reference record

Reference records include footnotes, bibliography entries, Scripture links and
configuration, and name or translation mappings. They identify or contextualize
evidence; they do not automatically prove every claim made in a note or AI
answer. Stable local citations should remain human-readable.

### 2.4 Note

A note is user data derived from reading but owned by the reader. Annotations
may include anchors into a particular source revision; discussions may include
messages, evidence manifests, and schema versions. Tools must preserve unknown
fields when a compatible schema permits them and reject unsafe or stale writes
rather than silently overwriting a newer revision.

Notes may be used as optional personal context. They must always be labeled as
user-authored material and kept distinct from author text and references.

### 2.5 Supplemental library item

A local-library item is distinct from the primary book. Its logical record may
span:

- an unchanged import under `Sources/Originals/`;
- registry data in `Sources/catalog.json`;
- a reproducible text projection under `Sources/Processed/`; and
- a disposable search structure under `Sources/Indexes/`.

Privacy and outbound-approval fields in the registry are user decisions, not
derivable metadata. Converters and indexers must preserve that distinction.

### 2.6 Derived context and build output

A derived context bundle selects and labels data for one operation. A derived
index accelerates retrieval. A generated reader file renders other sources.
None may become the sole durable copy of book text, user notes, consent state,
or provenance.

## 3. Provenance requirements

Durable normalized or derived material must expose enough information to answer:

1. What input produced this?
2. Which version or revision of the input was used?
3. Which tool or schema produced it?
4. Can the output be rebuilt without hidden state?
5. Is any part human-authored, user-authored, or AI-generated?

The exact representation may be Markdown front matter, a registry entry, a
manifest, or a documented deterministic path. Provenance should be readable
without relying on a private chat history.

## 4. Editability rules

### Edit the source when

- normalized Markdown contains a verified transcription or formatting error;
- curated metadata or a reference record is incorrect;
- application behavior or presentation must change; or
- the user explicitly changes their own note or consent state.

### Edit the generator when

- HTML, an index, a projection, or a context bundle is incorrect while its
  declared inputs are correct; or
- generation is nondeterministic, incomplete, or loses provenance.

### Never repair by hand

- `Web/dist/`;
- `Sources/Indexes/`;
- processed library files that declare an original and converter;
- ephemeral context previews or cached context builds.

If regeneration would destroy information not present in declared inputs, stop:
the artifact has accidentally become authoritative and the architecture must be
repaired before regeneration.

## 5. AI-authored material

AI output may be retained as a draft, note, discussion message, candidate link,
or explicitly labeled analysis. It must not be presented as original book text,
user authorship, or verified evidence. When an AI-assisted edit changes durable
factual content, retain the same citations and review obligations as a human
edit.

## 6. Schema changes

A schema change must specify:

- the owning document and version;
- backward-read and forward-write behavior;
- migration or lazy-upgrade rules;
- failure behavior for unknown or malformed data; and
- tests that protect user data and provenance.

Do not bulk-rewrite user data merely to make formatting uniform. Prefer a
validated migration with a recoverable backup or a lazy upgrade when practical.
