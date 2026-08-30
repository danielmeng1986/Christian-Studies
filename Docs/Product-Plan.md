# Christian Studies Product Plan

**Version:** 0.2
**Status:** Accepted planning baseline — implementation gated
**Authority:** Planning document; not a current implementation specification

> Chinese review version: [`Product-Plan-zh.md`](Product-Plan-zh.md).

The English version is the agent-facing planning source. Product decisions must
be reviewed in Chinese and reflected in both versions in the same change. If
the two versions conflict, stop planning or implementation and reconcile them.

## 1. Purpose

This plan describes how Christian Studies can grow from a working single-book
reader into a multi-book AI-assisted reading environment without losing the
qualities that made the current system valuable.

It establishes outcomes, sequencing, refactoring gates, and measures of success.
It does not select every implementation technology or make the target
architecture current. Accepted decisions and remaining questions are tracked in
[`Open-Questions.md`](Open-Questions.md) and [`Decisions/`](Decisions/README.md).

## 2. Origin and product insight

The project began with a modest goal: keep thoughts and notes from Christian
reading in Git. *A Quest for Godliness* exposed a practical problem. A legacy
Word manuscript was difficult to navigate and annotate, while reviewed Markdown
was comfortable to read and maintain. Building HTML from that Markdown made
footnotes, Scripture, selection-based notes, and richer reading interactions
possible.

The next step—AI discussion—revealed the deeper product value. Previously, a
reader had to upload a book or manually paste passages into a general chat. The
local reader can instead construct the exact context for a question: current
text, nearby structure, footnotes, Scripture, personal notes, identity matches,
and relevant passages elsewhere in the book.

The product thesis is:

> For serious reading, AI quality depends not only on the selected model but on
> a transparent, source-aware, task-specific context assembled around the
> reader's actual place in the book.

Christian Studies should make that context an inspectable product feature, not
an invisible implementation detail.

## 3. Primary user outcomes

The environment should help a reader:

1. import a legally possessed source without losing the original;
2. obtain a faithful, reviewable Markdown reading edition;
3. read comfortably with useful references close at hand;
4. attach durable notes to exact passages;
5. ask AI questions without manually rebuilding book context;
6. understand which evidence the AI used and what it did not know;
7. control whether personal or supplemental material leaves the machine;
8. move from isolated annotations to reviewed, structured knowledge; and
9. retain understandable, portable data independent of one model or UI.

The accepted first product is local-first and centered on an individual reader.
A collaborative or hosted edition requires a new product decision after demand
has been tested with the project owner's reading group.

## 4. Current validated baseline

《追寻敬虔》 demonstrates that the following ideas work in real use:

- Word-to-Markdown normalization with preserved source provenance;
- Markdown as the reviewed reading authority;
- deterministic HTML generation;
- interactive references and passage annotations;
- Git-readable user-data files;
- revision-aware local APIs;
- source-typed context assembly;
- visible per-turn context selection;
- cross-chapter retrieval and identity resolution;
- opt-in supplemental-library evidence; and
- useful AI answers without requiring external research.

This baseline is an asset to extract and generalize, not a prototype to discard.

## 5. Product boundaries

### In scope for the platform direction

- multiple books with a shared import and reading workflow;
- preserved originals and reviewed Markdown editions;
- a book catalog and management dashboard;
- interactive reading, references, notes, and AI discussions;
- book-independent context construction and retrieval;
- cost- and capability-aware model selection with user control;
- controlled MCP tools and reusable skills;
- structured-note and cross-book knowledge workflows with human review; and
- reproducible generation, migrations, tests, and evaluation.

### Accepted distribution model

- **Personal:** durable content, annotations, and discussions may be
  Git-managed on the project owner's machine.
- **Internal:** reading-group friends deploy locally; shared books and resources
  may use Git, while each reader's notes and discussions remain local.
- **External:** the application ships without books, may bundle redistributable
  Scripture resources, and lets readers import their own supported material.

Development remains browser plus loopback service. The first distributable
release targets a desktop application built on the web application. See
[ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution.md).

### Not assumed yet

- a hosted multi-user service;
- accounts, collaboration, or public sharing;
- a specific desktop packaging technology or operating-system matrix;
- automatic acceptance of AI conversions or theological conclusions;
- a database as the authority for current annotations and discussions;
- unrestricted web, MCP, filesystem, or model access; or
- support for every ebook and document format in the first platform release.

These are decision areas, not hidden requirements.

## 6. Delivery strategy

Work proceeds through evidence-based phases rather than target dates. Each phase
must leave the current reader usable and must have explicit entry and exit
criteria before implementation begins.

### Phase 0 — Architecture and decision baseline

Outcome: current and target responsibilities are documented before refactoring.

- maintain the repository working contract and current architecture;
- record the product story and platform direction;
- decide the critical questions that affect storage, deployment, content
  representation, and platform boundaries;
- inventory current 《追寻敬虔》 behavior and test coverage; and
- define compatibility fixtures that future implementations must preserve.

The decision portion of this gate is complete. Phase 0 exits when current
behavior is inventoried, compatibility fixtures exist, initial domain contracts
are versioned, and the migration/rollback outline is documented.

### Phase 1 — Extract stable domain contracts

Outcome: book-independent contracts exist before code is physically moved.

- specify `Book`, `Edition`, `ReadingUnit`, `Reference`, `Annotation`,
  `Discussion`, `Source`, `ContextBundle`, and `EvidenceManifest` identities;
- separate domain behavior from 《追寻敬虔》 paths and UI assumptions;
- create contract tests using the existing book as a compatibility fixture;
- define schema versioning and migration policy; and
- establish repository-wide policy validation.

Exit gate: current reader behavior passes through documented, book-independent
interfaces without moving authoritative user data.

### Phase 2 — Build the ingestion pipeline

Outcome: a new book can move from import to a reviewable reading package.

- preserve imported originals and record rights/provenance metadata;
- use format adapters for extraction rather than one monolithic converter;
- produce a conversion preview and diagnostics;
- support human correction and approval before Markdown becomes authoritative;
- validate structure, links, references, and required metadata; and
- make every processed artifact and index reproducible.

Exit gate: at least one additional representative book is imported without
book-specific code in the core pipeline.

### Phase 3 — Introduce the multi-book application shell

Outcome: the frontend and backend manage books rather than one fixed directory.

- add a book catalog and lifecycle state;
- expose book, chapter, note, discussion, source, and build operations through
  stable application interfaces;
- provide import, validation status, library management, and reading entry
  points in one dashboard;
- keep the shared web application usable through the development browser/local
  service and ready for a later desktop shell;
- provide local-profile onboarding and local AI-provider configuration without
  introducing remote accounts;
- retain current reading features as a vertical slice; and
- keep all mutations inside validated, scoped APIs.

Exit gate: both 《追寻敬虔》 and the second book can be opened and studied through
the same application flow.

### Phase 4 — Generalize the context platform

Outcome: `ContextBuilder` becomes a book-independent, evaluated service.

- define a versioned context request, bundle, preview, and manifest contract;
- separate evidence discovery, ranking, user selection, budgeting, and prompt
  rendering;
- add repeatable retrieval and answer-quality evaluation cases;
- preserve per-source consent and prompt-injection boundaries; and
- make context explainability part of the UI.

Exit gate: the same context pipeline handles multiple books without weakening
source labels, revision checks, or user control.

### Phase 5 — Add model orchestration

Outcome: model choice can balance answer quality, latency, privacy, and cost.

- classify request needs using transparent policy inputs;
- select among approved models or providers;
- allow explicit user override where appropriate;
- record model, policy version, estimated cost, and fallback behavior;
- evaluate routing against fixed reading questions; and
- fail safely when a capability or provider is unavailable.

Exit gate: routing demonstrates measurable value over a single-model baseline
without making context behavior opaque.

### Phase 6 — Add MCP and skill capabilities

Outcome: external capabilities extend reading without bypassing evidence,
consent, or security rules.

- define a capability registry and least-privilege permission model;
- distinguish deterministic processing tools from research tools;
- expose tool use in previews and evidence manifests;
- sandbox imported content from instructions; and
- test denial, failure, and provenance behavior.

Exit gate: one tightly scoped capability improves a real reading workflow and
passes its permission and provenance acceptance criteria.

### Phase 7 — Develop structured knowledge

Outcome: annotations and discussions can become reviewed knowledge that remains
linked to evidence.

- propose structured notes from existing study material;
- first evaluate one completed chapter to determine whether its annotations and
  discussions support useful synthesis;
- keep proposals separate from accepted user knowledge;
- preserve citations to chapters, references, discussions, and external
  evidence;
- support cross-book people, concepts, Scripture, events, and themes; and
- keep Markdown-readable exports or representations.

Exit gate: a reader can review, accept, edit, reject, and trace a structured
knowledge proposal without AI silently changing durable knowledge.

## 7. Refactoring policy

The platform should use an incremental replacement strategy:

1. characterize current behavior with tests and real data;
2. define the new contract beside the current implementation;
3. route one vertical slice through the new contract;
4. compare outputs and user-data behavior;
5. migrate deliberately with rollback or compatibility support; and
6. remove old code only after the replacement satisfies acceptance criteria.

Avoid a big-bang rewrite. Do not combine directory migration, schema migration,
frontend replacement, model routing, and new product behavior in one change.

## 8. Measures of success

| Area | Example measure |
| --- | --- |
| Import fidelity | Reviewed reading text remains traceable to preserved source; unresolved conversion issues are visible |
| Time to readable | A supported source reaches review preview with minimal book-specific setup |
| Reader durability | Existing notes survive rebuilds and source revisions without silent mis-anchoring |
| Context quality | Required evidence is present; irrelevant evidence and unsupported claims are reduced on a fixed evaluation set |
| Explainability | Every AI turn can show source types, source identity, revisions, model, and tool use |
| Economics | Cost and latency are measured per task class; routing does not sacrifice acceptance quality |
| Portability | Books, reviewed text, notes, and manifests remain understandable outside one UI or provider |
| Reuse | A second book requires configuration and content review, not copied application code |

Metrics should be defined with concrete fixtures before a phase claims success.

## 9. Principal risks

- conversion automation may create plausible but unfaithful reading text;
- a platform abstraction may erase book-specific editorial needs;
- source revisions may orphan annotations or discussions;
- retrieval may add volume without improving evidence quality;
- model routing may optimize price while hiding inconsistent behavior;
- MCP tools or imported documents may widen trust and data-exposure boundaries;
- a database may become an opaque second source of truth;
- structured-note automation may blur user judgment and AI proposals; and
- a large refactor may interrupt the working reading environment.

Each phase must convert its relevant risks into tests, previews, permissions, or
explicit user decisions.

## 10. Decision process and next step

Accepted decisions and remaining questions live in
[`Open-Questions.md`](Open-Questions.md), with cross-cutting rationale under
[`Decisions/`](Decisions/README.md). Stable IDs allow plans, specifications,
tests, and commits to reference the same boundary.

The immediate next step is still planning rather than structural migration:

1. inventory current behavior and define compatibility fixtures;
2. specify the versioned Book Package and Reading Document Model, including
   stable block UUID representation;
3. specify SQLite schemas with an explicit authoritative/derived/operational
   role for every table and a metadata migration/export plan;
4. specify provider-neutral Context Service contracts; and
5. select a representative second-book fixture.

[OQ-016](Open-Questions.md#oq-016-internalexternal-user-data-persistence-engine)
and [OQ-017](Open-Questions.md#oq-017-knowledge-graph-projection-engine) remain
open but do not block these contract-design steps.
