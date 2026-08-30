# Christian Studies Working Contract

This file is the mandatory entry point for work in this repository. It routes
agents to the repository specifications; it does not duplicate them.

## Startup protocol

Before reasoning about or changing repository content:

1. Read [`Docs/README.md`](Docs/README.md).
2. Read every core document that the task matrix in that file marks as
   required for the task.
3. Read any linked, book-local specification or README that governs the files
   in scope.
4. Classify each file to be touched as authoritative, user data, derived data,
   generated output, or implementation source.
5. Identify the relevant generation and validation commands before editing a
   derived or generated system.

Do not begin from implementation guesses when a governing document exists.

## Repository authority

Within repository-owned instructions, use this order when two sources conflict:

1. the user's explicit instruction for the current task;
2. this `AGENTS.md` entry contract;
3. the core architecture documents listed in `Docs/README.md`;
4. the numbered repository specifications under `Docs/`;
5. book-local specifications and READMEs; and
6. current implementation behavior.

Higher-level system or developer instructions remain controlling. A task that
intentionally changes architecture must update the governing document in the
same change. Do not silently choose between conflicting specifications: report
the conflict and either resolve it in scope or ask for direction.

## Non-negotiable boundaries

- Never edit `Books/*/Web/dist/` directly. Change its inputs and rebuild it.
- Never treat a derived index as an authoritative source. Rebuild it from its
  declared inputs.
- Preserve files under `Books/*/Original/` unchanged unless the user explicitly
  requests source-file replacement or restoration.
- Treat `Books/*/Notes/` as user data. Preserve unknown fields and unrelated
  records, and use the owning application's validated write path when one
  exists.
- Do not silently rewrite normalized reading text with generated summaries,
  translations, or interpretations.
- Do not expose secrets in repository files, command arguments, generated
  output, logs, or discussion records.

The complete ownership and editability rules are defined in
[`Docs/Content-Model.md`](Docs/Content-Model.md).

## Change and verification protocol

For every material change:

1. edit the authoritative input or implementation source;
2. regenerate affected derived artifacts through the documented command;
3. run the smallest relevant validation suite, expanding it when the change
   crosses subsystem boundaries;
4. inspect the resulting diff for accidental user-data or generated-output
   changes; and
5. state what was verified and what was not.

Use [`Docs/Validation.md`](Docs/Validation.md) for the validation matrix. A
documented rule is binding even when no automated check exists; never claim
that a boundary is test-enforced unless the validation document says it is.

## Scope-specific instructions

More specific `AGENTS.md` files may add constraints for their directory, but
they may not weaken this contract or the core architecture. If one is added,
link it from the relevant architecture or local README so that the instruction
chain remains discoverable.
