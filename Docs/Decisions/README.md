# Architecture Decision Records

[中文索引](README-zh.md)

This directory contains accepted decisions that affect multiple Christian
Studies specifications or require long-lived rationale.

The English ADR is the agent-facing decision record. Each ADR has a complete
Chinese review companion. A decision change must update both versions and every
affected current or planning document in the same change.

| ADR | Decision | Status | Related questions |
| --- | --- | --- | --- |
| [ADR-0001](ADR-0001-Product-Deployment-and-Distribution.md) / [中文](ADR-0001-Product-Deployment-and-Distribution-zh.md) | Product boundary, original runtime direction, and distribution stages (amended by ADR-0004) | Accepted | OQ-001–OQ-003 |
| [ADR-0002](ADR-0002-Data-Authority-and-Database-Roles.md) / [中文](ADR-0002-Data-Authority-and-Database-Roles-zh.md) | Data authority, Git policy, and database roles | Accepted | OQ-003, OQ-006, OQ-014 |
| [ADR-0003](ADR-0003-Stable-Block-Anchoring.md) / [中文](ADR-0003-Stable-Block-Anchoring-zh.md) | Stable block identity with precise range selectors | Accepted | OQ-008 |
| [ADR-0004](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data.md) / [中文](ADR-0004-Mobile-First-Local-Device-and-Portable-User-Data-zh.md) | Mobile-first local device and portable user data | Accepted | OQ-001–OQ-003, OQ-018–OQ-019 |

An accepted ADR records direction. It does not claim that migration or
implementation has already occurred. Current runtime behavior continues to be
governed by the core specifications until they are deliberately revised.

ADR-0004 amends ADR-0001 only where ADR-0001 names a desktop application as the
first dedicated-device target. ADR-0001's local-first, single-reader boundary,
current browser/loopback development runtime, and deferred public/collaborative
stages remain in force.
