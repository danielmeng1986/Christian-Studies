# Platform Architecture Proposal

**Version:** 0.1
**Status:** Discussion draft — not current architecture
**Scope:** Proposed multi-book AI-assisted reading platform

> Chinese review version:
> [`Platform-Architecture-Proposal-zh.md`](Platform-Architecture-Proposal-zh.md).

The English version is the agent-facing proposal. Accepted decisions must be
reflected in both language versions in the same change. Until this document is
formally accepted and the current core specifications are revised, the
normative architecture remains [`Architecture.md`](Architecture.md),
[`Reader-Architecture.md`](Reader-Architecture.md), and
[`AI-Context-Architecture.md`](AI-Context-Architecture.md).

## 1. Purpose

This proposal describes the target shape of Christian Studies after the
single-book implementation is generalized. It focuses on logical boundaries and
data flow before selecting a final repository layout, framework, database, or
deployment package.

The target is not merely a bookshelf UI. It is a reading environment in which
source preservation, reviewed Markdown, interactive study, transparent AI
context, and durable knowledge form one traceable lifecycle.

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
    mutation.

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

This is an extraction and generalization strategy, not a requirement to replace
every current technology.

## 4. Proposed logical architecture

```text
┌──────────────────────── Multi-book frontend ────────────────────────┐
│ Catalog │ Import/Review │ Reader │ Notes │ AI Discussion │ Knowledge │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ versioned application API
┌──────────────────────────────▼───────────────────────────────────────┐
│                         Application backend                          │
│                                                                       │
│ Book Catalog      Ingestion Pipeline      Reader/Build Service        │
│ Note Service      Discussion Service      Source Library              │
│ Context Service   Model Router            Capability Gateway          │
│ Knowledge Service                     Jobs / migrations / validation  │
└───────────┬──────────────────┬───────────────────┬────────────────────┘
            │                  │                   │
            ▼                  ▼                   ▼
   Durable book packages   User-owned data   Operational/derived stores
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

The diagram shows logical services. They may begin in one local process and one
repository. Separate network services are not required unless measured scale or
deployment decisions justify them.

## 5. Durable book package

A book package is the portable boundary between content and platform. The exact
directory layout remains subject to [OQ-005](Open-Questions.md#oq-005-platform-and-book-package-boundary),
but the logical package contains:

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

The target frontend has six connected workspaces:

1. **Library** — books, editions, progress, validation, and recent activity.
2. **Import and review** — source selection, conversion diagnostics, Markdown
   review, and publication approval.
3. **Reader** — chapter content, navigation, references, themes, and search.
4. **Study** — annotations, discussions, supplemental sources, and unresolved
   anchors.
5. **Context inspector** — evidence preview, inclusion choices, budget, model,
   tools, consent, and manifest access.
6. **Knowledge** — reviewed structured notes and cross-book connections.

These may share one application shell. The target does not require a specific
frontend framework until interaction complexity and maintenance criteria are
agreed.

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

Whether durable user state remains Git-managed files, moves partly to SQLite,
or supports both is unresolved in [OQ-003](Open-Questions.md#oq-003-durable-storage-and-git)
and [OQ-006](Open-Questions.md#oq-006-database-role). A database must not become
an undocumented second source of truth.

## 13. Security and privacy

- Bind local services to loopback by default until deployment policy changes.
- Keep provider credentials in process-scoped secret storage, never content,
  browser bundles, logs, or command arguments.
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

Every migration step needs rollback or backward-read behavior for durable user
data. Directory moves and schema changes must not be bundled casually.

## 16. Readiness gates

Implementation of the structural refactor should not begin until:

- OQ-001 through OQ-006 have accepted decisions;
- current reader behavior and user-data schemas have compatibility fixtures;
- the target book-package contract is versioned;
- the migration and rollback path for 《追寻敬虔》 is documented;
- a representative second-book import fixture is selected; and
- success measures for import, anchoring, context, and portability are defined.

The proposal then becomes normative only through an explicit architecture
decision that updates the current core documents and validation contract.
