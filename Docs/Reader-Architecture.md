# Reader Architecture

**Status:** Core normative specification

**Current implementation:** `Books/追寻敬虔/Web/`

This document defines the repository-level contract for local book readers. The
current reader's book-specific READMEs and specifications refine this contract.

## 1. Responsibilities

The reader has three components:

1. a deterministic build that renders repository content into static assets;
2. a local service that serves those assets and exposes validated APIs for
   user data, library operations, and AI discussion; and
3. browser code that presents the reading experience without becoming a source
   of record.

The reader consumes content; it does not own the canonical book text.

## 2. Inputs and outputs

The current build reads:

- `Books/追寻敬虔/Reading/**/*.md`;
- `Books/追寻敬虔/References/`;
- `Books/追寻敬虔/Metadata/`;
- repository Scripture data under `References/Bible-Texts/`; and
- templates and assets under `Books/追寻敬虔/Web/src/`.

The build implementation is `Books/追寻敬虔/Web/scripts/build.py`. Its output is
`Books/追寻敬虔/Web/dist/`.

`Web/dist/` is disposable generated output:

- it is ignored by Git;
- it must be reproducible from declared inputs;
- it must not contain the only copy of user data; and
- it must never be edited directly.

If rendered output is wrong, correct the reading/reference/configuration input,
template, asset, or build implementation and run the build again.

## 3. Runtime write boundaries

The local service may write only through an explicit, validated user operation:

| Operation | Durable target | Required protection |
| --- | --- | --- |
| Create/update/delete annotation | `Notes/Annotations/<chapter>.json` | Schema validation, source revision, conflict-safe save |
| Create/continue discussion | `Notes/Discussions/<chapter>/` | Schema validation, message state, evidence provenance |
| Confirm library import | `Sources/Originals/`, `Sources/Processed/`, `Sources/catalog.json` | Preview, explicit confirmation, privacy defaults |
| Rebuild/remove library index | `Sources/Indexes/` | Never delete originals or registry consent state |

Serving a page, building the reader, previewing context, or running retrieval
must not mutate user data.

Browser storage may hold presentation preferences, but it must not be the only
durable location of annotations, discussions, library ownership, or consent.

## 4. Build and runtime flow

```text
Reading + References + Metadata + Bible data + Web/src
                         │
                         ▼
                  Web/scripts/build.py
                         │
                         ▼
                     Web/dist
                         │
                         ▼
                  Web/scripts/serve.py
                    │             │
                    ▼             ▼
                 Browser       validated APIs
                                      │
                                      ▼
                             Notes / Sources user data
```

The service reads current authoritative files at the point required by its
contract. Static generated output must not be trusted as a substitute for
revision checks on mutable reading or user data.

## 5. Security boundary

- API keys and other secrets belong to the service process, not the browser or
  repository.
- Do not put secrets in `.env` files, command arguments, generated JavaScript,
  logs, notes, or discussion JSON.
- The browser must not receive the OpenAI API key.
- Markdown and imported material are untrusted content. Raw HTML and unsafe URL
  protocols must not execute merely because the content is rendered.
- External transmission of supplemental sources requires the consent rules in
  [`AI-Context-Architecture.md`](AI-Context-Architecture.md).

The current safe-start procedures are documented in
[`Books/追寻敬虔/Web/README-zh.md`](../Books/追寻敬虔/Web/README-zh.md).

## 6. Required workflow for reader changes

Before changing the reader, read this document, the content model, the
validation contract, and the relevant book-local README/specification. Then:

1. identify whether the change belongs to content, application source, runtime
   data handling, or context assembly;
2. change only the authoritative input or implementation;
3. build the reader;
4. run the relevant tests; and
5. inspect generated behavior without committing or hand-editing `dist/`.

Commands for the current reader are listed in [`Validation.md`](Validation.md)
and the book-local README.

## 7. Book-local specifications

The following current documents add implementation detail:

- [`Web/README.md`](../Books/追寻敬虔/Web/README.md) and
  [`Web/README-zh.md`](../Books/追寻敬虔/Web/README-zh.md);
- [`Web/AI-DISCUSSION-SPEC-zh.md`](../Books/追寻敬虔/Web/AI-DISCUSSION-SPEC-zh.md);
- [`Web/AI-CONTEXT-SPEC.md`](../Books/追寻敬虔/Web/AI-CONTEXT-SPEC.md) and its
  [Chinese review version](../Books/追寻敬虔/Web/AI-CONTEXT-SPEC-zh.md); and
- the implementation requirements and roadmap documents under
  `Books/追寻敬虔/Metadata/`.

If a local document contradicts a core repository boundary, the core boundary
controls until the architecture is deliberately revised.

## 8. Accepted evolution direction

[ADR-0001](Decisions/ADR-0001-Product-Deployment-and-Distribution.md), as
amended by
[ADR-0004](Decisions/ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md),
keeps the browser plus loopback service as the development and compatibility
runtime. The first dedicated-device target is now a self-contained iPhone
application; desktop packaging remains a possible later client. Neither record
authorizes a packaging framework, native rewrite, or immediate platform
extraction.

The mobile target must preserve offline reading and device-local user data,
store provider credentials in Keychain or equivalent secret storage, and
provide versioned export/import before synchronization. These are future
acceptance constraints; the runtime write boundaries above continue to govern
the current Reader.

[ADR-0003](Decisions/ADR-0003-Stable-Block-Anchoring.md) replaces
rendering-order identity in the future Reading Document Model with stable UUIDs
for reviewed semantic blocks while retaining exact range/context/revision
selectors. Current anchors are not migrated until that model and its
compatibility tests exist.
