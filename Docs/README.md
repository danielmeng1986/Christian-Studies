# Christian Studies Documentation

**Version:** 1.1
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

## Conflict and change policy

Use the authority order in [`AGENTS.md`](../AGENTS.md). When implementation and
documentation disagree, do not assume that implementation is correct. Determine
whether the code is stale, the document is stale, or a migration is incomplete.

An architectural change is incomplete until the owning core document, affected
domain specifications, implementation, generation flow, and validations agree.
The validation contract distinguishes rules enforced by current tests from
rules that still require review.
