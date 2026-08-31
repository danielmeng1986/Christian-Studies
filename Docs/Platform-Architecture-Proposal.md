# Platform Architecture Proposal

**Version:** 0.3
**Status:** Accepted target direction — implementation gated, not current architecture
**Scope:** Proposed personal AI-assisted reading platform with domain profiles

> Chinese review version:
> [`Platform-Architecture-Proposal-zh.md`](Platform-Architecture-Proposal-zh.md).

The English version is the agent-facing target proposal. Accepted decisions
must be reflected in both language versions in the same change. The target
direction is accepted, but it is not the current implementation architecture;
until the gated migrations revise the core specifications, normative behavior
remains under [`Architecture.md`](Architecture.md),
[`Reader-Architecture.md`](Reader-Architecture.md), and
[`AI-Context-Architecture.md`](AI-Context-Architecture.md).

## 1. Purpose

This proposal describes the possible target shape after the single-book
Christian Studies implementation is generalized from evidence. Christian
Studies is the first Domain Profile; language learning is a candidate second
profile. It focuses on logical boundaries and data flow before selecting a
physical layout, frontend framework, user-data/graph engine, or native client
technology.

The target is not merely a bookshelf UI. It is a reading environment in which
source preservation, reviewed Markdown, interactive study, transparent AI
context, and durable knowledge form one traceable lifecycle.

## Accepted decision baseline

- The first product is local-first and single-reader.
- Development and discovery continue with a browser plus loopback service; the
  first dedicated-device target is a self-contained iPhone application, while
  desktop remains a possible later client.
- Local-first means the active device owns core reading capability and
  authoritative personal data. Export/import precedes sync, and cloud remains
  optional transport, replication, or backup.
- Personal, internal reading-group, and external distribution stages have
  different Git, bundled-content, and user-data policies.
- Reviewed Markdown remains authoritative normalized prose.
- Book packages are portable data units; generic application behavior belongs
  to the shared platform.
- SQLite may own the platform Book Catalog and migrated platform metadata;
  search/retrieval indexes remain derived.
- Reviewed semantic blocks receive stable UUIDs while precise selections retain
  quote/range/revision selectors.
- Context contracts are provider-neutral; model routing is initially
  deterministic and user-overridable; capabilities are registered,
  least-privilege, and consent-aware.
- Structured knowledge requires user acceptance, and source rights/visibility
  are recorded and enforced.
- The current Reader remains the compatibility baseline, and no platform
  extraction begins until a second representative real use case validates the
  abstraction.

Cross-cutting rationale is indexed in [`Decisions/README.md`](Decisions/README.md).

## 2. Architectural drivers

The platform must:

1. support multiple books without copying reader code into each book;
2. import heterogeneous source formats while preserving originals;
3. keep human review between extraction and authoritative reading content;
4. keep content, user data, generated output, and indexes distinguishable;
5. preserve the current reader and user data during migration;
6. make `ContextBuilder` book-independent and separately evaluable;
7. support multiple models without coupling context quality to one provider;
8. add MCP and skills through explicit capabilities and permissions;
9. remain understandable and useful when AI or network access is unavailable;
10. keep evidence and provenance visible from import through AI answer; and
11. allow structured knowledge to emerge through review rather than silent AI
    mutation;
12. support offline-first device operation with credentials isolated in native
    secret storage;
13. separate shared Reading Core services from Domain Profiles; and
14. admit dictionaries, grammar references, books, Scripture, notes, and
    discussions as typed Source Providers only through explicit contracts.

## 3. Current-to-target shift

| Concern | Current implementation | Proposed target |
| --- | --- | --- |
| Application boundary | `Books/追寻敬虔/Web/` owns one reader | One shared application operates on registered book packages |
| Book discovery | Paths and constants know one book | A catalog resolves stable book and edition identities |
| Import | Book-specific scripts and manual workflow | Format adapters plus a reviewable ingestion pipeline |
| Rendering | Book-local deterministic builder | Shared rendering service consuming book-package contracts |
| User data | Book-local JSON through scoped APIs | Same durable ownership behind book-independent interfaces |
| Context | Working book-local `ContextBuilder` | Versioned Context Service with pluggable retrieval providers |
| Model call | One configured model path | Policy-driven Model Router with user-visible selection and fallback |
| Tools/skills | Limited or absent | Capability registry with consent, provenance, and least privilege |
| Knowledge | Notes and discussions mostly book-local | Reviewed structured knowledge linked across books and evidence |
| Product domain | Christian-study behavior and paths coexist in one implementation | Shared Reading Core plus evidence-tested Domain Profiles |
| Primary device | Browser on a Mac-hosted local service | Self-contained mobile client using portable contracts; browser remains baseline |
| Personal data | Book-local files | Device-local authority with versioned portable export/import after explicit migration |
| Trusted lookup | Book, Scripture, notes, and supplemental library | Registered typed Source Providers, with dictionary/grammar contracts still open |

This is an extraction and generalization strategy, not a requirement to replace
every current technology.

## 4. Proposed logical architecture

```text
┌──────────────────── Device reading clients ─────────────────────────┐
│ Mobile Reader │ Browser baseline │ Later desktop/tablet clients      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ versioned application API
┌──────────────────────────────▼───────────────────────────────────────┐
│                         Application backend                          │
│                                                                       │
│ Reader Core       Book Catalog            Ingestion Pipeline          │
│ Reader/Build      Domain Profiles         Source Providers            │
│ Note Service      Discussion Service      Source Library              │
│ Context Service   Model Router            Capability Gateway          │
│ Knowledge Service                     Jobs / migrations / validation  │
└───────────┬──────────────────┬───────────────────┬────────────────────┘
            │                  │                   │
            ▼                  ▼                   ▼
   Managed content/packages User-owned data  Operational/derived stores
   originals + Markdown    notes + consent   indexes + caches + job state
            │                                      │
            └──────────────────┬───────────────────┘
                               ▼
                    Evidence manifests / audits
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Approved models      Approved MCP/skills
```

The diagram shows logical services, not a required network topology. They may
begin in one local process and repository through the development browser, then
run inside a device-local client. A Mac server or separate network service is
not a product requirement. Separate services require a future decision and
measured need.

### 4.1 Reader Core and Domain Profiles

The candidate shared core owns content access, anchors, annotation, discussion,
context, search, provenance, and portable user-data contracts. Domain Profiles
add domain-specific source types, actions, knowledge proposals, and UI wording.
Christian Studies may configure Bible and theological reference behavior;
language learning may configure dictionary, grammar, translation, personal
examples, and recurrence. A responsibility moves into the core only after both
real workflows demonstrate the shared contract.

## 5. Durable book package

A book package is the accepted portable boundary between content and platform.
Its exact physical layout remains to be specified and versioned, but the logical
package contains:

- stable book and edition identity;
- preserved primary source files;
- reviewed normalized Markdown reading units;
- curated references and Scripture configuration;
- metadata and normalization provenance;
- user annotations and discussions, if the chosen ownership model keeps them
  with the book;
- optional supplemental source-library records; and
- schema versions required to validate and migrate the package.

Application templates, shared UI code, model clients, generic conversion
adapters, and generic indexing code do not belong inside each book package.

The package must remain understandable without running the frontend. Platform
indexes and rendered HTML may be deleted and reconstructed.

## 6. Ingestion and publication pipeline

```text
Receive source
    ↓
Record identity, rights, checksum, and import metadata
    ↓
Preserve immutable original
    ↓
Extract through a format adapter
    ↓
Produce conversion report and review preview
    ↓
Human correction and approval
    ↓
Publish authoritative normalized Markdown
    ↓
Validate references, structure, metadata, and provenance
    ↓
Build reader assets and retrieval indexes
```

### Required stages

**Import registration** assigns stable identity and records provenance before
conversion. A failed conversion must not lose or modify the original.

**Format adapters** extract DOC/DOCX, PDF, EPUB, HTML, Markdown, or other
supported formats into a common intermediate result with diagnostics. Adapters
must not silently declare their output authoritative.

**Review workspace** shows extraction uncertainty, heading structure,
quotations, footnotes, images, and page/source locations. Human approval is the
boundary that promotes reviewed Markdown to reading authority.

**Validation** checks book-package contracts and blocks publication when
required evidence or structure is unresolved.

**Publication** updates declared reading content, then rebuilds disposable
reader assets and indexes. It must not overwrite user notes or discussions.

## 7. Backend capability boundaries

### 7.1 Book Catalog

Resolves stable `bookId` and `editionId`, lifecycle state, package location,
available chapters, build state, and validation state. It does not copy full
book content into an opaque catalog record.

### 7.2 Ingestion Pipeline

Owns import jobs, adapter selection, conversion diagnostics, review artifacts,
and publication requests. It cannot promote content without the required user
approval.

### 7.3 Reader and Build Service

Renders reviewed Markdown and references through shared templates/components.
Build output is deterministic where practical and never contains the sole copy
of notes, discussions, or consent.

### 7.4 Note and Discussion Services

Own validated mutations, revision conflicts, schema migration, and durable
provenance for user data. Reading, building, and context preview remain
read-only operations.

### 7.5 Source Library

Owns supplemental import, processing, indexing, privacy state, and per-source
outbound eligibility. Removing a processed copy or index never removes the
preserved source or silently changes consent.

### 7.5a Source Providers

A Source Provider exposes typed, source-linked evidence through a versioned
contract. Candidate providers include the current book, Bible, dictionaries,
grammar references, personal notes, discussions, and supplemental references.
A provider does not grant its content instruction authority, broaden outbound
eligibility, or let a model present generated wording as a source entry.
Dictionary and grammar details remain open under OQ-020.

### 7.6 Context Service

Owns evidence discovery, typed selection, ranking, budgeting, preview, source
revision verification, and manifest generation. It produces a provider-neutral
`ContextBundle`; it does not decide durable note content or silently call tools.

### 7.7 Model Router

Chooses among explicitly configured models based on request needs, context
size, tool requirements, privacy constraints, quality policy, latency, and
budget. It consumes a provider-neutral bundle and produces a recorded routing
decision. It must not hide evidence changes behind model selection.

### 7.8 Capability Gateway

Mediates MCP servers, skills, external research, and other tools. It exposes
only registered capabilities, enforces user and source permissions, treats tool
results as typed evidence, and records use in the turn manifest.

### 7.9 Knowledge Service

Creates proposals for structured notes, entities, links, and synthesis. A
proposal remains AI-authored working material until the user accepts or edits
it. Accepted knowledge retains evidence links and change history.

## 8. Frontend information architecture

The target capabilities have six connected workspaces:

1. **Library** — books, editions, progress, validation, and recent activity.
2. **Import and review** — source selection, conversion diagnostics, Markdown
   review, and publication approval.
3. **Reader** — chapter content, navigation, references, themes, and search.
4. **Study** — annotations, discussions, supplemental sources, and unresolved
   anchors.
5. **Context inspector** — evidence preview, inclusion choices, budget, model,
   tools, consent, and manifest access.
6. **Knowledge** — reviewed structured notes and cross-book connections.

On a phone these capabilities should appear around the Reader as contextual
surfaces rather than permanent desktop columns. A selection-triggered bottom
sheet with Look Up, Explain, Grammar, Translate, Ask AI, Note, and Save is a
candidate interaction, not an accepted UI specification. OQ-018 owns the native
boundary and interaction contract.

## 9. AI request flow

```text
User question and reading focus
           ↓
Context Service discovers candidate evidence
           ↓
User-visible preview applies inclusion and consent choices
           ↓
Context Service freezes and verifies the selected bundle
           ↓
Model Router selects an approved model and fallback policy
           ↓
Capability Gateway runs only explicitly permitted tools, if any
           ↓
Model receives typed evidence plus behavior instructions
           ↓
Answer streams to the reader
           ↓
Discussion turn stores answer, model decision, and evidence manifest
```

Model routing must occur after the core evidence need is understood. Choosing a
more capable model is not a substitute for repairing missing, irrelevant, or
misclassified context.

## 10. Model-routing policy

The future router should consider:

- task class: explanation, comparison, synthesis, extraction, or research;
- required reasoning depth and acceptable latency;
- context size and supported input types;
- whether tool use or a particular capability is needed;
- privacy and provider eligibility for every included source;
- quality evaluation thresholds;
- estimated and maximum cost; and
- provider health and safe fallback.

The UI should show the selected model or policy tier and allow a user override
where the request remains valid and safe. Routing decisions require evaluation
against fixed reading tasks; intuition about model quality is insufficient.

## 11. MCP and skill architecture

MCP servers and skills are capabilities, not ambient authority. Each registered
capability should declare:

- purpose and input/output types;
- local or external execution boundary;
- data categories it may receive;
- required user confirmation or durable permission;
- network, filesystem, account, and write effects;
- provenance returned with results;
- timeout and failure behavior; and
- tests or evaluation cases.

Imported books, notes, web pages, tool results, and retrieved documents remain
untrusted content. They cannot grant themselves capability access or override
system behavior.

## 12. Data and persistence strategy

The proposal preserves three categories regardless of the selected storage
technology:

| Category | Examples | Required property |
| --- | --- | --- |
| Durable content | originals, reviewed Markdown, references, metadata | Portable, traceable, human-reviewable |
| User-owned state | notes, discussions, consent, accepted knowledge | Conflict-safe, recoverable, never rebuild-only |
| Operational/derived state | indexes, caches, token estimates, build assets, job state | Disposable or reconstructable from declared inputs |

Authority is declared per entity or table. In the personal stage, current
annotations and discussions remain JSON file authorities and may be
Git-managed. SQLite may become authoritative for the platform Book Catalog and
migrated platform-managed metadata, while search/retrieval data remains derived.
The internal/external user-data engine is deferred to
[OQ-016](Open-Questions.md#oq-016-internalexternal-user-data-persistence-engine),
and graph projection technology to
[OQ-017](Open-Questions.md#oq-017-knowledge-graph-projection-engine). See
[ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles.md).

For a future device-local client, bundled books and trusted references are
managed content; progress, highlights, notes, discussions, accepted knowledge,
and preferences are mutable user data. A local database may become authoritative
only through a tested migration and must have a versioned portable export/import
representation. Whole-database replacement is not the archival or sync
contract. See [ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md)
and OQ-019.

## 13. Security and privacy

- Bind local services to loopback by default until deployment policy changes.
- Keep provider credentials in native approved secret storage—Keychain on
  iOS—never content, ordinary configuration, SQLite fields, browser bundles,
  manifests, discussions, exports, logs, or command arguments.
- Validate every write against registered resources and schema versions.
- Treat all imported and retrieved content as untrusted data.
- Apply source-level outbound eligibility and per-request inclusion.
- Show external model and tool transmission before it occurs when policy
  requires user choice.
- Record model, provider, tools, and evidence provenance without recording
  secrets.
- Make offline reading and notes useful when AI services are unavailable.

## 14. Evaluation and observability

The platform needs evaluation at four independent layers:

1. **Conversion:** fidelity, structural preservation, and unresolved ambiguity.
2. **Retrieval/context:** evidence recall, irrelevant evidence, provenance, and
   deterministic behavior.
3. **Answer:** factual grounding, citation support, focus, and useful
   uncertainty.
4. **System:** latency, token use, monetary cost, failures, privacy decisions,
   and migration integrity.

Logs and manifests must distinguish user content from operational metadata and
avoid retaining secrets or unnecessary private text.

## 15. Migration strategy

1. Freeze the current behavior in compatibility tests.
2. Define book-independent contracts without moving content.
3. Wrap the existing 《追寻敬虔》 implementation behind those contracts.
4. Build a second book through the proposed ingestion path.
5. Introduce the shared application shell around both books.
6. Move context assembly behind the provider-neutral Context Service.
7. Add model routing only after context evaluations are stable.
8. Add capabilities and structured knowledge as separate vertical slices.
9. Remove book-local application code only after data and behavior parity are
   verified.

Steps 1–3 remain preparatory. Steps that extract a shared platform or build a
native client begin only after a representative second real use case has been
used enough to test the supposed common contracts. Portable export/import is
proved before any LAN or cloud synchronization layer.

Every migration step needs rollback or backward-read behavior for durable user
data. Directory moves and schema changes must not be bundled casually.

## 16. Readiness gates

The initial direction gate is complete. Implementation of the structural
refactor or native mobile client should still not begin until:

- current reader behavior and user-data schemas have compatibility fixtures;
- the target book-package contract is versioned;
- the Reading Document Model defines stable block UUID representation;
- SQLite schemas declare authoritative, derived, or operational role per table
  and define metadata export/migration;
- the migration and rollback path for 《追寻敬虔》 is documented;
- a representative second-book import fixture is selected;
- that representative second book has been used as a real workflow, not only a
  synthetic fixture; and
- success measures for import, anchoring, context, and portability are defined.

OQ-018 through OQ-022 block their dependent mobile, portable-data, Source
Provider, language-learning, and managed-content implementation. OQ-016 and
OQ-017 remain later engine choices.

The proposal then becomes normative only through an explicit architecture
decision that updates the current core documents and validation contract.
