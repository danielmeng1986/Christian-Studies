# Christian Studies Documentation

**Version:** 1.4
**Status:** Active repository specification

This directory defines the repository's architectural truth, content
boundaries, and domain conventions. The root [`AGENTS.md`](../AGENTS.md) is the
mandatory startup entry point and routes work here.

## Core architecture

Read these documents according to the task matrix below:

1. [Repository Architecture](Architecture.md)
2. [Content Model](Content-Model.md)
3. [Reader Architecture](Reader-Architecture.md)
4. [AI Context Architecture](AI-Context-Architecture.md)
5. [Validation Contract](Validation.md)

These documents own repository-level boundaries. A book-local specification
may add detail but may not silently redefine them.

## Task routing

| Task | Required documents |
| --- | --- |
| Any repository change | `Architecture.md`, `Content-Model.md`, `Validation.md` |
| Import, normalize, or edit book text | Above + `03-Book-Format.md`, `05-Reading-Workflow.md`, relevant local normalization spec |
| Change repository directories or ownership | Above + `02-Repository-Structure.md` |
| Change references, footnotes, or Scripture links | Above + `04-Reference-System.md`, applicable `08-*` specification |
| Change the local reader or generated site | Above + `Reader-Architecture.md`, local reader README/spec |
| Change AI discussion, retrieval, or local library | Above + `AI-Context-Architecture.md`, local AI context/discussion specs |
| Change reusable knowledge or cross-book links | Above + `06-Knowledge-Graph.md` |
| Change architecture or roadmap | All core documents + affected numbered specifications |
| Discuss or plan the future platform/refactor | All core documents + `Product-Plan.md`, `Platform-Architecture-Proposal.md`, `Open-Questions.md`, `Decisions/README.md`, and affected numbered specifications |
| Discuss future voice/language-practice capabilities or commercialization | Above + `Voice-Capability-Hypothesis.md` and/or `Commercial-Product-Hypothesis.md` |

Reading a required document means reading the current file, not relying on a
summary from an earlier task.

## Design Book and domain specifications

The numbered documents preserve the repository's design rationale and detailed
study conventions:

1. [Vision](01-Vision.md)
2. [Repository Structure](02-Repository-Structure.md)
3. [Book Format](03-Book-Format.md)
4. [Reference System](04-Reference-System.md)
5. [Reading Workflow](05-Reading-Workflow.md)
6. [Knowledge Graph](06-Knowledge-Graph.md)
7. [Roadmap](07-Roadmap.md)
8. [Scripture Reference Specification (English)](08-Scripture-Reference-Spec.md) / [经文引用规范（中文）](08-Scripture-Reference-Spec-zh.md)

The design principles used throughout are collected in
[`01-Vision.md`](01-Vision.md#design-principles).

## Product direction, decisions, and remaining questions

These documents describe intended direction, accepted planning decisions, and
remaining choices. Their status labels are significant: an accepted target is
not current implementation authority until its gated migration updates the core
specifications.

- [Product Plan](Product-Plan.md) / [产品规划书](Product-Plan-zh.md)
- [Platform Architecture Proposal](Platform-Architecture-Proposal.md) /
  [平台架构规范草案](Platform-Architecture-Proposal-zh.md)
- [Open Questions](Open-Questions.md) / [未决问题](Open-Questions-zh.md)
- [Accepted Architecture Decisions](Decisions/README.md) /
  [已接受架构决议](Decisions/README-zh.md)

## Future capability and product hypotheses

These documents preserve directions worth testing without turning them into
implementation authority or accepted architecture:

- [Voice Capability Hypothesis](Voice-Capability-Hypothesis.md) /
  [语音能力假设](Voice-Capability-Hypothesis-zh.md)
- [Commercial Product Hypothesis](Commercial-Product-Hypothesis.md) /
  [商业产品假设](Commercial-Product-Hypothesis-zh.md)

A hypothesis may inform the Product Plan, target architecture, Roadmap, or an
Open Question. It authorizes no feature, schema, provider, commercial service,
or infrastructure. Promotion into implementation requires the evidence and
decision gates named in the hypothesis and the governing planning documents.

English planning and specification documents are the agent-facing source;
Chinese companions are full human-review versions. Product decisions must be
reviewed in Chinese and reflected in both versions in the same change. If the
two versions conflict, stop and reconcile them before planning or implementation
continues.

## Conflict and change policy

Use the authority order in [`AGENTS.md`](../AGENTS.md). When implementation and
documentation disagree, do not assume that implementation is correct. Determine
whether the code is stale, the document is stale, or a migration is incomplete.

An architectural change is incomplete until the owning core document, affected
domain specifications, implementation, generation flow, and validations agree.
The validation contract distinguishes rules enforced by current tests from
rules that still require review.

Accepted future decisions must also update the relevant Open Question status.
An unaccepted recommendation or target proposal does not authorize code, schema,
or directory migration.
