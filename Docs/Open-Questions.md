# Christian Studies Open Questions

**Version:** 0.1
**Status:** Active decision queue
**Authority:** Questions and recommendations are not accepted decisions

> Chinese review version: [`Open-Questions-zh.md`](Open-Questions-zh.md).

This document holds architectural and product decisions that must be discussed
before their dependent work begins. Stable IDs allow plans, specifications,
tests, and commits to refer to the same question.

A “suggested starting position” is a concrete proposal for discussion, not an
authorization to implement it. A question is closed only when its decision
record is accepted and all affected English and Chinese documents are updated.

## Decision priority

| ID | Decision | Needed before | Status |
| --- | --- | --- | --- |
| OQ-001 | Product boundary | Structural refactor | Open |
| OQ-002 | Runtime and deployment shape | Application shell | Open |
| OQ-003 | Durable storage and Git | Structural refactor | Open |
| OQ-004 | Canonical normalized representation | Structural refactor | Open |
| OQ-005 | Platform and book-package boundary | Structural refactor | Open |
| OQ-006 | Database role | Structural refactor | Open |
| OQ-007 | Import formats and review boundary | Ingestion pipeline | Open |
| OQ-008 | Annotation anchor identity | Shared reader/data model | Open |
| OQ-009 | Context Service contract | Context generalization | Open |
| OQ-010 | Model-routing policy | Multiple models | Open |
| OQ-011 | MCP and skill trust model | First external capability | Open |
| OQ-012 | Privacy and provider eligibility | Multiple providers/tools | Open |
| OQ-013 | Structured-note workflow | Knowledge features | Open |
| OQ-014 | Cross-book knowledge identity | Knowledge features | Open |
| OQ-015 | Source rights and repository exposure | Broader importing/sharing | Open |

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
