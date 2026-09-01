# Christian Studies Open Questions

**Version:** 0.4
**Status:** Active decision registry
**Authority:** Accepted decision records govern planning; open recommendations do not

> Chinese review version: [`Open-Questions-zh.md`](Open-Questions-zh.md).

This document holds architectural and product decisions that must be discussed
before their dependent work begins. Stable IDs allow plans, specifications,
tests, and commits to refer to the same question.

A “suggested starting position” is a concrete proposal for discussion, not an
authorization to implement it. An accepted record governs future planning but
does not claim that migration or implementation has occurred. Cross-cutting
decisions are preserved under [`Decisions/`](Decisions/README.md).

## Decision priority

| ID | Decision | Needed before | Status |
| --- | --- | --- | --- |
| OQ-001 | Product boundary | Structural refactor | Accepted — ADR-0001/0004 |
| OQ-002 | Runtime and deployment shape | Dedicated-device implementation | Accepted direction — ADR-0001/0004; mobile contract follow-up OQ-018 |
| OQ-003 | Durable storage and Git | Structural refactor | Accepted — ADR-0001/0002/0004; engine/package follow-ups OQ-016/OQ-019 |
| OQ-004 | Canonical normalized representation | Structural refactor | Accepted |
| OQ-005 | Platform and book-package boundary | Structural refactor | Accepted |
| OQ-006 | Database role | Structural refactor | Accepted — ADR-0002; engine follow-ups OQ-016/OQ-017 |
| OQ-007 | Import formats and review boundary | Ingestion pipeline | Accepted |
| OQ-008 | Annotation anchor identity | Shared reader/data model | Accepted — ADR-0003 |
| OQ-009 | Context Service contract | Context generalization | Accepted |
| OQ-010 | Model-routing policy | Multiple models | Accepted |
| OQ-011 | MCP and skill trust model | First external capability | Accepted |
| OQ-012 | Privacy and provider eligibility | Multiple providers/tools | Accepted |
| OQ-013 | Structured-note workflow | Knowledge features | Accepted with evaluation gate |
| OQ-014 | Cross-book knowledge identity | Knowledge features | Accepted; graph engine follow-up OQ-017 |
| OQ-015 | Source rights and repository exposure | Broader importing/sharing | Accepted |
| OQ-016 | Internal/external user-data persistence engine | Internal/external release | Open |
| OQ-017 | Knowledge graph projection engine | Graph implementation | Open |
| OQ-018 | Native mobile application and interaction boundary | Native mobile implementation | Open within accepted mobile-first direction |
| OQ-019 | Portable user-data package and synchronization boundary | Export/import implementation | Open within accepted export-before-sync direction |
| OQ-020 | Dictionary and grammar Source Provider contract | Language-learning prototype | Open |
| OQ-021 | Language-learning domain and durable knowledge model | Saving language knowledge | Open |
| OQ-022 | Managed-content packaging, rights, and update isolation | Bundled mobile content | Open |
| OQ-023 | Voice capability, discussion profiles, and session data | First durable Voice feature | Open |

## OQ-001 Product boundary

**Question:** Is Christian Studies primarily a personal local-first environment,
a locally deployed multi-user application, or a hosted product?

**Why it matters:** Accounts, synchronization, storage, concurrency, security,
deployment, and licensing depend on this boundary. Designing for all three at
once would add large costs before the need is known.

**Suggested starting position:** Keep the first platform release local-first and
single-reader. Define identities and APIs so a future multi-user layer is not
impossible, but do not implement accounts, cloud synchronization, or tenancy
without a separate product decision.

**Decision must state:** primary user, trusted machine boundary, collaboration
expectations, remote access expectations, and which future scenarios must remain
possible.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** The first platform is a local-first, single-reader personal
  environment. APIs and identities should preserve a possible future multi-user
  path, but accounts, cloud sync, tenancy, and collaborative reading are out of
  scope until a new product decision.
- **Rationale:** Real personal use has already established value; broader demand
  must first be tested with the project owner's reading group.
- **Consequences:** The user's machine is the trusted boundary. A collaborative
  edition is a future product branch, not a hidden first-release requirement.
- **Record:** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution.md).
- **Amendment:** ADR-0004 keeps this personal boundary and makes the iPhone the
  first dedicated-device target. It does not add public users or remote
  accounts.

## OQ-002 Runtime and deployment shape

**Question:** Should the next platform remain a browser plus local service,
become a packaged desktop application, or introduce a hosted web deployment?

**Why it matters:** Filesystem access, secret storage, updates, browser security,
offline use, and frontend technology all depend on the runtime container.

**Suggested starting position:** Retain the loopback local-service architecture
during the structural refactor. Make the application interfaces packageable,
but defer Electron, Tauri, native mobile, and hosted deployment until the
multi-book workflow exposes a concrete need.

**Decision must state:** supported operating systems, launch experience, offline
expectations, update method, secret-storage method, and remote-access policy.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option, as amended:** Continue browser plus loopback local service
  during core development and use it as the compatibility baseline. Target the
  first dedicated-device release as a self-contained iPhone application; keep
  desktop as a possible later client.
- **Clarification:** A personal-release “registration” creates a local profile;
  it is not a remote account. The user's API key is configured and stored
  locally through an approved secret boundary.
- **Deferred detail:** The native/web boundary, iOS baseline, update delivery,
  and mobile interaction contract belong to OQ-018.
- **Record:** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution.md).
- **Amendment:** [ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md)
  replaces the desktop-first distributable target with a self-contained iPhone
  target. The browser plus loopback service remains the current development and
  compatibility runtime. The native application contract remains OQ-018.

## OQ-003 Durable storage and Git

**Question:** Which data remains stored as Git-managed files, and which data—if
any—moves to an application store?

**Why it matters:** The project began with Git as a feature. Book text, notes,
discussions, consent, and accepted knowledge have different size, privacy,
conflict, and portability needs.

**Suggested starting position:** Keep preserved sources, reviewed Markdown,
references, metadata, annotations, and accepted knowledge in portable files.
Keep Git as the expected history mechanism for a personal installation. Permit
derived or operational stores for search and jobs. Evaluate whether large
discussion bodies need a separate durable representation only with real size
and workflow measurements.

**Decision must state:** authoritative data by entity, Git inclusion and ignore
rules, privacy expectations, backup/export, conflict behavior, and migration
between storage modes.

### Decision

- **Status:** Accepted on 2026-08-30, with a storage-engine follow-up.
- **Chosen option:** Use three distribution stages. In the personal stage,
  durable content, notes, and discussions may be Git-managed. In the internal
  stage, shared books/resources may use Git while each reader's notes and
  discussions remain local. The external application ships without books;
  users import their own sources, while redistributable Scripture resources may
  be bundled.
- **Current authority:** Existing annotation and discussion JSON files remain
  authoritative in the personal stage.
- **Deferred detail:** The internal/external user-data persistence engine is
  OQ-016. The first portable export/import package and any later synchronization
  boundary are OQ-019.
- **Records:** [ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution.md),
  [ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles.md), and
  [ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md).

## OQ-004 Canonical normalized representation

**Question:** Should reviewed Markdown remain the canonical normalized reading
format, or should a structured AST/JSON document become authoritative?

**Why it matters:** Import, editing, rendering, anchors, diff quality,
portability, and ContextBuilder all depend on the canonical representation.

**Suggested starting position:** Keep reviewed Markdown authoritative for prose.
Parse it into a versioned intermediate document model for rendering, indexing,
and anchors, but treat that model as derived. Use structured files for entities
that are naturally records, not as a second prose copy.

**Decision must state:** supported Markdown dialect, extension syntax, stable
identity mechanism, round-trip expectations, and what requires human approval.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Reviewed Markdown remains the authoritative normalized prose.
  A versioned intermediate document model may support rendering, indexing, and
  anchors, but remains derived. Structured records may use structured storage
  without creating a second prose authority.
- **Consequences:** Import promotion requires human approval; renderers and
  indexes must rebuild from Markdown. The exact Markdown dialect and identity
  encoding will be specified in the Reading Document Model.
- **Tests required:** Parser fixtures, deterministic projection tests, and proof
  that no derived representation becomes the only prose copy.

## OQ-005 Platform and book-package boundary

**Question:** What belongs to the shared platform, and what travels with an
individual book package?

**Why it matters:** The current book owns its `Web/` implementation. Keeping
that shape would duplicate code; moving too much could make books impossible to
understand or version independently.

**Suggested starting position:** Make book packages data-focused and portable:
originals, reviewed content, references, metadata, and explicitly owned user
data. Move generic converters, UI, build logic, model clients, and indexes to a
shared platform. Wrap the current book layout through a compatibility adapter
before moving any durable files.

**Decision must state:** logical package contract, physical repository layout,
user-data ownership, package version, discovery mechanism, and migration path.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Book packages are portable, data-centered units containing
  originals, reviewed content, references, metadata, and explicitly owned user
  data. Generic converters, UI, build logic, model clients, and indexes belong
  to the shared platform.
- **Migration:** Wrap the current 《追寻敬虔》 layout with a compatibility adapter
  before moving durable files. Physical layout and package schema are specified
  and tested before migration.
- **Consequences:** A book remains understandable without application code;
  shared application behavior is not copied into every book.

## OQ-006 Database role

**Question:** Should the platform use SQLite or another database, and if so,
which responsibilities may it own?

**Why it matters:** A catalog, jobs, search, full-text retrieval, and concurrency
benefit from a database, but an unscoped database can become an opaque second
source of truth.

**Suggested starting position:** Use SQLite first for derived indexes and local
operational state such as catalog projections and jobs. Keep durable book and
user authorities in declared portable files until a measured requirement proves
that a specific entity needs transactional database ownership.

**Decision must state:** authoritative tables versus projections, rebuild rules,
backup/export, schema migrations, failure recovery, and Git interaction.

### Decision

- **Status:** Accepted on 2026-08-30, with engine-specific follow-ups.
- **Chosen option:** Introduce local SQLite for an authoritative platform Book
  Catalog and, after explicit migration, authoritative platform-managed book
  metadata. SQLite may also hold operational jobs and derived search/retrieval
  projections.
- **Authority rule:** Authority is declared per entity or table. Retrieval and
  search indexes remain derived even when stored beside authoritative records.
  Current file metadata remains authoritative until a tested migration changes
  that boundary.
- **User data:** Current annotation/discussion JSON remains file-authoritative;
  the future engine is OQ-016. Graph storage is OQ-017.
- **Record:** [ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles.md).

## OQ-007 Import formats and review boundary

**Question:** Which source formats should the first generic ingestion pipeline
support, and where does human review become mandatory?

**Why it matters:** DOC, DOCX, PDF, EPUB, HTML, and OCR have different fidelity
and structural ambiguity. Claiming broad support too early would hide conversion
errors.

**Suggested starting position:** Begin with Markdown, DOCX, text-extractable PDF,
and plain text; keep the existing legacy-DOC path as a controlled compatibility
adapter. Add EPUB and OCR only with representative fixtures. Every format must
produce diagnostics and a review preview; no extracted prose becomes
authoritative without explicit approval.

**Decision must state:** first-release formats, unsupported features, conversion
quality threshold, review workflow, image/table/footnote treatment, and failure
behavior.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Start the generic pipeline with Markdown, DOCX,
  text-extractable PDF, and plain text. Preserve the legacy DOC workflow as a
  controlled compatibility adapter. Add EPUB and OCR only after representative
  fixtures exist.
- **Review boundary:** Every adapter produces diagnostics and a conversion
  preview. Extracted prose becomes authoritative only after explicit human
  approval.
- **Tests required:** Per-format fidelity fixtures, visible ambiguity, original
  preservation, and failure behavior for unsupported structures.

## OQ-008 Annotation anchor identity

**Question:** How should notes and discussions remain attached when Markdown,
parsing, or rendering changes?

**Why it matters:** Current deterministic block-order IDs plus quote context are
practical but can shift when blocks are inserted. A platform-wide reader needs
an explicit long-term identity and migration contract.

**Suggested starting position:** Introduce stable reading-unit and block IDs at
the reviewed-content layer, retain exact quote plus prefix/suffix selectors, and
keep source revision hashes. Provide a relocation/migration tool that never
accepts ambiguous matches silently. Do not use DOM paths as durable identity.

**Decision must state:** where IDs live, how imports generate them, how human
editing preserves them, recovery order, ambiguity UI, and migration tests.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Assign a stable opaque UUID to each reviewed semantic block,
  normally a paragraph. Preserve precise sub-block selection through exact text,
  offsets, prefix/suffix context, and source revision. Do not require persistent
  sentence UUIDs in the first platform model.
- **Consequences:** Neighboring insertions do not change a block's durable
  identity; revision and ambiguity checks remain required. Cross-block anchors
  need a later schema extension.
- **Record:** [ADR-0003](Decisions/ADR-0003-Stable-Block-Anchoring.md).

## OQ-009 Context Service contract

**Question:** What is the stable boundary between evidence discovery, context
selection, prompt rendering, model routing, and discussion persistence?

**Why it matters:** `ContextBuilder` is the product's central advantage. If its
responsibilities remain mixed with one UI or provider, it will be difficult to
reuse, test, and improve.

**Suggested starting position:** Define provider-neutral, versioned
`ContextRequest`, `EvidenceCandidate`, `ContextPreview`, `ContextBundle`, and
`EvidenceManifest` contracts. Separate discovery/ranking from user selection,
budgeting, prompt rendering, and model execution. Freeze and hash selected
evidence before sending.

**Decision must state:** schemas, extension mechanism, required evidence order,
budget behavior, cache rules, revision verification, and evaluation fixtures.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Define provider-neutral, versioned `ContextRequest`,
  `EvidenceCandidate`, `ContextPreview`, `ContextBundle`, and
  `EvidenceManifest` contracts. Separate discovery/ranking, user selection,
  budgeting, prompt rendering, model execution, and persistence.
- **Integrity rule:** Freeze and hash selected evidence before sending; reject
  stale or unresolvable evidence rather than silently substituting it.
- **Migration:** Refactor the current `ContextBuilder` in layers behind
  compatibility tests, without tying the contract to one UI or provider.

## OQ-010 Model-routing policy

**Question:** How should the system select a model for a question while balancing
accuracy, cost, latency, privacy, and user preference?

**Why it matters:** A router can reduce cost or improve difficult answers, but it
can also create opaque, inconsistent behavior that is harder to evaluate than a
single model.

**Suggested starting position:** Begin with a small deterministic policy over
explicit task features and user-selectable modes such as Economy, Automatic,
and Deep. Allow user override. Route only among models that satisfy source
privacy and capability requirements. Require evaluation evidence before adding
an AI classifier to choose another AI model.

**Decision must state:** task classes, supported providers/models, user modes,
quality floors, cost caps, fallback, logging, and evaluation criteria.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Begin with a small deterministic routing policy and
  user-selectable Economy, Automatic, and Deep modes. Permit user override when
  privacy and capability constraints remain satisfied.
- **Guardrail:** Do not add an AI model to select another model until evaluation
  demonstrates value. Context quality is repaired before model capability is
  escalated.
- **Tests required:** Fixed reading tasks comparing grounding, focus, cost,
  latency, fallback, and mode override.

## OQ-011 MCP and skill trust model

**Question:** How are MCP servers and skills registered, permitted, invoked, and
audited?

**Why it matters:** Tools may read private context, access accounts or networks,
write data, and return content containing further instructions.

**Suggested starting position:** Keep all capabilities disabled until registered.
Declare input data classes and side effects, use least privilege, default to
read-only, require explicit approval for external transmission or writes, and
record tool results as untrusted typed evidence in the manifest.

**Decision must state:** capability manifest, permission lifetime, user prompts,
secret access, sandboxing, write policy, provenance, and failure behavior.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Capabilities are disabled until registered, use least
  privilege, and default to read-only. External transmission and writes require
  explicit permission. Tool results remain untrusted typed evidence recorded in
  the manifest.
- **Consequences:** Imported content cannot grant tool access. Each capability
  must declare inputs, side effects, secrets, permission lifetime, provenance,
  and failure behavior before use.

## OQ-012 Privacy and provider eligibility

**Question:** How does the system determine which content may be sent to which
model, tool, or provider?

**Why it matters:** Book sources, personal notes, discussions, and supplemental
documents may have different privacy and rights constraints. Per-turn selection
alone is insufficient if provider eligibility is unknown.

**Suggested starting position:** Assign durable outbound policy to each source
and user-data category, maintain a provider allowlist, and require both source
eligibility and per-request inclusion. Default new private supplemental sources
to no external transmission.

**Decision must state:** data classifications, provider policy, local-model
behavior, consent persistence, revocation, audit records, and UI language.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Assign durable outbound policy to every source and user-data
  category, maintain a provider allowlist, and require both source eligibility
  and per-request inclusion. New private supplemental sources default to no
  external transmission.
- **Consequences:** Derived chunks inherit—not broaden—their source policy.
  Consent can be revoked, and the UI must show the relevant provider and data
  categories before transmission when a choice is required.

## OQ-013 Structured-note workflow

**Question:** What does “more structured notes” mean, and how does an AI proposal
become accepted user knowledge?

**Why it matters:** Structure could mean tagged notes, outlines, atomic claims,
people/concepts, argument maps, or summaries. Building all forms at once would
create an unclear knowledge model and risk attributing AI work to the user.

**Suggested starting position:** Start with evidence-linked synthesis notes and
stable people, concepts, and Scripture entities. AI creates proposals in a
separate review queue. Only explicit acceptance or user editing creates durable
knowledge.

**Decision must state:** first knowledge types, required citations, proposal
schema, review actions, authorship, revision history, and rejection behavior.

### Decision

- **Status:** Accepted on 2026-08-30 with an evaluation gate.
- **Chosen option:** First evaluate whether one completed chapter's annotations
  and discussions contain enough quality to support useful synthesis. Begin
  structured output with evidence-linked synthesis notes and stable person,
  concept, and Scripture entities.
- **Review boundary:** AI output enters a separate proposal queue. Only explicit
  user acceptance or editing creates durable knowledge.
- **Gate:** Do not design a broader ontology until the chapter-level experiment
  identifies what the reader actually understood and gained.

## OQ-014 Cross-book knowledge identity

**Question:** How should the same person, work, concept, or Scripture passage be
identified and linked across books?

**Why it matters:** Filename-only identity is fragile; a database-only graph is
opaque. Translation variants and theological ambiguity also make automatic
merging unsafe.

**Suggested starting position:** Give accepted knowledge entities stable IDs and
human-readable Markdown pages, with aliases and evidence links. Build graph and
search indexes as derived projections. Require review for ambiguous merges and
do not treat a shared label as proof of identical meaning.

**Decision must state:** entity types, ID rules, aliases, merge/split workflow,
citation edges, Markdown representation, and index rebuilding.

### Decision

- **Status:** Accepted on 2026-08-30; projection engine remains open.
- **Chosen option:** Accepted knowledge entities receive stable IDs and
  human-readable Markdown pages with aliases and evidence links. Ambiguous
  merges require review; identical labels do not prove identical meaning.
- **Projection rule:** Search and graph stores are derived by default. A graph
  database is a candidate, not an accepted Source of Truth.
- **Follow-up:** OQ-017 selects a graph projection engine only after real graph
  queries and scale are known.
- **Record:** [ADR-0002](Decisions/ADR-0002-Data-Authority-and-Database-Roles.md).

## OQ-015 Source rights and repository exposure

**Question:** What rights and visibility metadata are required before an
original source or generated reading edition enters Git, is synchronized, or is
shared?

**Why it matters:** Many books are copyrighted even when the reader legally owns
a copy. A private local workflow, a private remote repository, and publication
have different consequences.

**Suggested starting position:** Record acquisition, rights basis, permitted
uses, and repository visibility during import. Default copyrighted originals
and full derived reading text to local/private use and exclude them from public
distribution unless permission or public-domain status is documented.

**Decision must state:** rights metadata schema, visibility classes, Git/remote
rules, export checks, redaction or exclusion behavior, and responsibility for
review.

### Decision

- **Status:** Accepted on 2026-08-30.
- **Chosen option:** Record acquisition, rights basis, permitted use, and
  repository visibility during import. Copyrighted originals and full derived
  reading text default to local/private use and are excluded from public
  distribution without documented permission or public-domain status.
- **Application requirement:** Import, export, synchronization, and distribution
  interfaces must present and enforce this declaration rather than relying only
  on documentation.
- **Tests required:** Distribution-package and export checks must reject or omit
  content whose visibility and rights do not permit the requested operation.

## OQ-016 Internal/external user-data persistence engine

**Question:** After the personal file-backed stage, which embedded or external
database should own annotations and discussions?

**Why it remains open:** The internal and external editions need local privacy,
JSON document fidelity, revision conflicts, backup/export, migrations, and easy
deployment. Current real-use data has not yet shown whether JSON files are
insufficient or which database tradeoff matters most.

**Candidates:** Continue schema-versioned JSON files; use an embedded database
with robust JSON document operations; or use a service database only if a later
multi-user product boundary requires it.

**Evaluation criteria:** lossless JSON semantics, transactions, revision
conflicts, migration tooling, backup/export, portability, encryption options,
desktop packaging, operational burden, and performance on representative notes
and discussions.

**Needed before:** The internal/external release changes user-data authority.

## OQ-017 Knowledge graph projection engine

**Question:** Which technology, if any, should implement the derived cross-book
knowledge graph and graph queries?

**Why it remains open:** A graph database may fit entity relationships, but the
project does not yet have accepted knowledge volume or concrete query patterns
that justify an engine. Selecting one now would confuse the knowledge identity
decision with a storage implementation choice.

**Candidates:** Derived adjacency/index tables in SQLite, an embedded graph
engine, or a dedicated graph database. Accepted Markdown knowledge remains the
default authority unless a later decision explicitly changes it.

**Evaluation criteria:** required graph queries, provenance edges, rebuildability,
local deployment, backup/export, ecosystem maturity, query complexity, and
measured data size.

**Needed before:** Implementing a persistent graph projection beyond simple
derived indexes.

## OQ-018 Native mobile application and interaction boundary

**Question:** Which native application architecture and interaction contract
should implement the accepted mobile-first direction without coupling the
Reading Core to one Apple UI or rewriting the current Reader prematurely?

**Why it remains open:** ADR-0004 selects a self-contained iPhone application
as the first dedicated-device target, but does not select SwiftUI, an embedded
web runtime, a shared rendering layer, package layout, background behavior, or
the exact selection/bottom-sheet interaction. Those decisions require a real
second reading use case and compatibility fixtures.

**Suggested starting position:** Keep the Reader as the primary surface. Text
selection may reveal contextual actions such as Look Up, Explain, Grammar,
Translate, Ask AI, Note, and Save in a transient mobile sheet, returning to the
same reading position when dismissed. Treat this as an interaction hypothesis,
not an implemented contract.

**Decision must state:** native/web boundary, supported iOS baseline, book
package access, offline behavior, navigation and restoration, selection model,
accessibility, update/migration behavior, secret storage, and compatibility
fixtures.

**Needed by:** Before native mobile application implementation. Platform
extraction remains gated by a representative second real use case.

## OQ-019 Portable user-data package and synchronization boundary

**Question:** What is the versioned portable representation for user data, and
how should import behave when the destination already contains related data?

**Accepted direction:** ADR-0004 requires explicit export/import before
automatic synchronization, forbids whole-database replacement as the long-term
protocol, and keeps cloud infrastructure optional. The package details and
merge policy remain open.

**Suggested starting position:** Export a manifest plus human-readable or
documented records for progress, highlights, notes, discussions, accepted
knowledge, and attachments. Use stable entity IDs, preserve unknown compatible
fields, validate checksums and schema versions, preview conflicts, and keep a
recoverable pre-import backup. Do not export provider credentials.

**Decision must state:** package layout and schema, included/excluded data,
identity and revision rules, import modes, duplicate/conflict behavior,
attachments, integrity and encryption, downgrade/forward compatibility,
recovery, and rights filtering.

**Needed by:** Before export/import implementation. LAN transfer, LAN sync,
AirDrop/Share Sheet integration, or cloud replication may transport this
package or future change sets only after separate transport and threat-model
decisions.

## OQ-020 Dictionary and grammar Source Provider contract

**Question:** How should dictionary and grammar evidence participate in search,
Context Builder, citation, licensing, offline packaging, and AI discussion?

**Why it remains open:** Dictionary is a first-class evidence source rather
than a UI convenience, but no provider schema, licensing policy, language-pair
model, lookup normalization, or citation contract has been validated with a
real language-learning book.

**Suggested starting position:** Define a shared `SourceProvider` contract whose
results are typed, source-linked, revisioned, rights-aware, and independently
renderable. Dictionary and grammar providers must supply evidence; the model may
explain and compare it but must not impersonate a dictionary entry.

**Decision must state:** provider identity and version, supported language
pairs, headword/expression lookup, morphology, sense and example provenance,
offline/index rules, licensing and export restrictions, context priority,
failure behavior, and evaluation fixtures.

**Needed by:** Before a language-learning prototype treats dictionary or grammar
results as durable evidence.

## OQ-021 Language-learning domain and durable knowledge model

**Question:** Which language-learning entities and workflows belong in a Domain
Profile, and which contracts are genuinely shared with Christian Studies?

**Why it remains open:** Lexemes, expressions, collocations, grammar patterns,
usage contrasts, examples, personal examples, and mistakes are plausible
entities, but designing them before real English or German reading would repeat
the premature abstraction the roadmap is intended to avoid.

**Suggested starting position:** Use one representative English or German book
to test the complete flow from selection through trusted lookup, AI explanation,
personal example, review, save, and later recurrence. Keep AI proposals separate
from user-accepted knowledge and reuse stable anchors, evidence, provenance, and
discussion contracts where the evidence shows they fit.

**Decision must state:** first knowledge types, stable identity and recurrence,
source sentence/anchor links, personal-example review, AI authorship, acceptance
and correction workflow, cross-language relations, portable export, and which
Study, Language Tutor, Speaking Practice, or Free Discussion outputs belong to
the Language Learning Domain.

**Needed by:** Before durable language-learning knowledge or a generalized
cross-domain ontology is implemented.

## OQ-022 Managed-content packaging, rights, and update isolation

**Question:** How may books, Bible data, dictionaries, grammar references, and
other trusted materials be bundled on a personal device without confusing them
with mutable user data or violating rights?

**Why it remains open:** ADR-0004 permits legally appropriate first-party
bundling for the personal stage, but package layout, licensing records, update
diffs, removal behavior, and user-data survival are not specified.

**Suggested starting position:** Give every managed content package a stable
identity, version, checksum, provenance, rights/visibility record, and declared
indexes. Install or update it separately from the user-data store; never delete
user records merely because a package is updated or removed.

**Decision must state:** package manifest, signature/integrity, licensing and
visibility, content version and anchor migration, bundled versus user-imported
material, index rebuilding, application-update behavior, rollback, and orphaned
user-data handling.

**Needed by:** Before books or trusted reference collections are embedded in a
mobile build.

## OQ-023 Voice capability, discussion profiles, and session data

**Question:** Which speech responsibilities belong to shared capabilities,
which policies belong to Domain Profiles, and which Voice Session outputs may
become durable user data or reviewed knowledge?

**Why it remains open:** Word playback, sentence prosody, expression practice,
and book-based voice discussion have different latency, offline, provider,
privacy, interaction, evaluation, and retention requirements. No representative
language-learning book has yet established which stages are repeatedly useful.
Selecting providers or schemas now would turn a staged hypothesis into an
unproven platform commitment.

**Suggested starting position:** Keep Speech Playback, Speech Recognition,
Realtime Conversation, and Practice Session orchestration in a candidate
Capability Layer. Let Domain Profiles define Study, Language Tutor, Speaking
Practice, and Free Discussion policies. Implement only the smallest evidenced
stage. Treat transcript, summary, feedback, target-use records, practice
signals, and session metadata as separately typed outputs; raw audio is
ephemeral by default and a speaking sample is saved only by explicit choice.

**Decision must state:** first Voice stage and use case, local/external provider
boundary, supported languages, offline fallback, latency and interruption
behavior, microphone and transmission consent, Discussion Profile contracts,
transcript authorship, output schemas, retention/deletion, portable export,
accessibility, evaluation fixtures, and failure recovery. Phoneme-level scoring
requires a separately evaluated specialized capability and must not be inferred
from general Voice support.

**Needed by:** Before the first durable Voice feature, retained transcript or
audio, or shared Voice service is implemented. The representative second-book
and real-use gates still apply. See the
[Voice Capability Hypothesis](Voice-Capability-Hypothesis.md).

## ADR queue

The following are candidate records, not accepted decisions or implementation
authority:

| Candidate ADR topic | Trigger |
| --- | --- |
| Native mobile application boundary and Reader interaction | Resolve OQ-018 after the second representative use case and compatibility fixtures |
| Portable user-data package, import, and recovery | Resolve OQ-019 before export/import implementation |
| Source Provider evidence and trust contract | Resolve OQ-020 before dictionary/grammar integration |
| Language-learning knowledge acceptance and recurrence | Resolve OQ-021 before durable language knowledge |
| Managed-content packaging and update isolation | Resolve OQ-022 before bundling mobile content |
| Voice capability boundary, discussion profiles, and session lifecycle | Resolve OQ-023 before the first durable Voice feature |
| Change-based LAN or cloud replication | Only after export/import works and a measured multi-device need exists |

## Decision record template

When a question is accepted, append a record beneath it or link a dedicated ADR:

```markdown
### Decision

- Status: Accepted
- Date: YYYY-MM-DD
- Chosen option:
- Rationale:
- Rejected alternatives:
- Consequences:
- Migration impact:
- Security/privacy impact:
- Documents to update:
- Tests or evaluations required:
```

Then update the priority table, both language versions, the product plan, the
target proposal, and any current normative document affected by the decision.
