# Local Interactive Edition of *A Quest for Godliness*: Roadmap

> English execution version. Chinese review version: `interactive-ebook-roadmap-zh.md`.

The English version drives execution. Phase or milestone changes must be mirrored in the Chinese review version in the same change.

## 1. Roadmap principle

Work is organized into testable phases rather than dates. A phase advances only after its exit criteria pass, so that build, UI, and persistence failures can be isolated.

Chapter 05 is the first major milestone. Do not expand to the complete book until it has been used for real reading and the resulting feedback has been incorporated.

## 2. Milestones

| Milestone | Outcome |
| --- | --- |
| M0: Specification baseline | Requirements, implementation specification, and data-source decisions agree |
| M1: Readable prototype | Chapter 05 builds and opens at localhost |
| M2: Footnote loop | Left-panel footnotes are complete |
| M3: Note loop | Notes persist to chapter JSON and restore highlights |
| M4: Chapter 05 acceptance | Safari and Chrome both pass acceptance |
| M5: Real-use revision | Specifications and implementation incorporate reading feedback |
| M6: Whole-book build | One pipeline covers every chapter |

## 3. Phase 0: Baseline and project skeleton

### Work

- Finalize the bilingual requirements, implementation specification, and roadmap.
- Create `Web/src`, `Web/scripts`, `Web/tests`, and `Notes/Annotations`.
- Ignore `Web/dist`, caches, logs, and temporary note files in Git.
- Create the empty Chapter 05 note file at `Notes/Annotations/05.json`.
- Pin the Markdown parser and define the Python runtime workflow.
- Provide consistent build, test, and local-launch entry points.

### Exit criteria

- Source files and generated files have unambiguous responsibilities.
- The empty note JSON passes schema validation.
- The local launcher can bind only to `127.0.0.1` by default.
- The actual directory layout agrees with both language versions of the specification.

## 4. Phase 1: Deterministic build and reading surface

### Work

- Read Chapter 05 YAML metadata and Markdown.
- Render headings, paragraphs, block quotations, emphasis, and ordinary links as semantic HTML.
- Add deterministic `data-block-id` values to annotatable blocks.
- Generate shared CSS/JavaScript references and the Chapter 05 page.
- Implement the toolbar, three-column layout, and narrow-screen drawers.
- Reserve a chapter-navigation dropdown in the toolbar; show Chapter 05 as its only MVP option.
- Implement light, dark, and sepia themes.
- Restore theme and panel preferences from `localStorage`.

### Exit criteria

- The page correctly contains one `h1`, eight `h2` elements, and the expected body formatting.
- Two consecutive builds from identical input have no output difference.
- `dist` contains no note, absolute repository path, or build timestamp.
- Reading width, scrolling, and all themes work in Safari and Chrome.

### Milestone

M1: Readable prototype.

## 5. Phase 2: Footnote system

### Work

- Parse `Footnotes-05.md` into a footnote index.
- Validate every body reference at build time.
- Implement left-panel footnote cards.
- Implement individual toggle, card close, show-all, and clear-all.
- Add active state, keyboard behavior, and accessibility attributes.
- Keep a typed left-panel item model for future Scripture content.

### Exit criteria

- All 35 Chapter 05 footnote entries display the correct content.
- The two translator-note identifiers work like numeric identifiers.
- Multiple cards retain deterministic order.
- Footnote actions do not move the article.
- Safari and Chrome behavior agrees.

### Milestone

M2: Footnote loop.

## 6. Phase 3: Chapter JSON and local persistence service

### Work

- Implement the chapter note schema and validation.
- Implement `GET /api/chapters/05/notes`.
- Implement revision-aware `PUT /api/chapters/05/notes`.
- Add same-origin validation, per-session write token, request-size limit, and chapter allowlist.
- Implement temporary-file plus atomic replacement.
- Reject stale revisions.
- Test the API and failure modes only against temporary directories.

### Exit criteria

- Empty and populated JSON load successfully.
- Valid writes produce stable, Git-readable JSON.
- Invalid paths and schemas cannot touch repository files.
- A simulated failure preserves the original file.
- Concurrent tabs cannot silently overwrite one another.

## 7. Phase 4: Selection and complete note workflow

### Work

- Map browser selections to canonical block IDs, offsets, exact text, and context.
- Add the floating “Write note” action.
- Add the optional contextual right-click action.
- Reject blank, cross-block, footnote-containing, and overlapping selections.
- Implement right-panel create, cancel, save, view, edit, and delete.
- Implement orange highlights and the chapter note list.
- Implement dirty-state warnings, save errors, and revision-conflict UI.
- Implement contextual anchor recovery and “needs relocation.”

### Exit criteria

- Saving updates `Notes/Annotations/05.json`, closes the editor, and draws a highlight.
- Refresh and service restart restore notes from JSON.
- Clicking a highlight opens and edits the correct note.
- Successful deletion removes both JSON data and highlight.
- Save failure never loses editor text.
- Body revisions never move a highlight to unverified text.

### Milestone

M3: Note loop.

## 8. Phase 5: Chapter 05 integrated acceptance

### Automated checks

- deterministic build and Markdown structure;
- footnote completeness;
- JSON schema, atomic writes, and stale-revision conflicts;
- anchor restoration and overlap detection;
- proof that `dist` contains no note content.

### Manual Safari and Chrome checks

- theme visuals and orange-highlight contrast;
- independent column scrolling and narrow-screen drawers;
- mouse selection, drag selection, context menu, and floating action;
- Chinese, Latin text, and emphasis selection boundaries;
- selection near footnote triggers;
- unsaved exit, save failure, and multi-tab conflict;
- long notes and many open footnotes.

### Exit criteria

- Section 13 of `interactive-ebook-requirements.md` passes.
- The definition of done in `interactive-ebook-implementation-spec.md` passes.
- Known issues are recorded and separated into blocking and non-blocking items.

### Milestone

M4: Chapter 05 accepted.

## 9. Phase 6: Real-reading feedback and specification revision

Observe:

- how many simultaneously open footnotes remain comfortable;
- whether note-list/editor switching feels natural;
- how often the same-block restriction blocks a useful annotation;
- whether orange highlights are too strong or weak in each theme;
- whether a Git diff after every save matches the desired workflow;
- anchor-recovery success while Markdown continues to be reviewed;
- whether note search, ordering, tags, or Markdown are actually needed.

Feedback process:

1. Record the real problem and reproduction steps.
2. Classify it as a requirement, interaction, data-model, or implementation issue.
3. Update both language versions of the requirements/specification before changing behavior.
4. If the JSON schema changes, provide migration and backward-compatibility tests.

### Milestone

M5: Real-use revision complete.

## 10. Phase 7: Expand to the complete book

### Work

- Define a whole-book chapter manifest and body-to-footnote mapping.
- Create one empty note JSON per chapter.
- Build all chapter pages and chapter navigation.
- Add table-of-contents, previous-chapter, and next-chapter entry points.
- Run structural and footnote audits for every chapter.
- Verify that chapter changes always call the matching note endpoint.
- Preserve a single-chapter build mode.

### Exit criteria

- One configuration builds every chapter without chapter-specific handwritten HTML.
- Each chapter writes only its own JSON.
- A failed chapter cannot masquerade as a successful whole-book build.
- The whole build remains deterministic and contains no notes.

### Milestone

M6: Whole-book build.

## 11. Deferred candidates

- Scripture in the left panel;
- cross-block annotations;
- overlapping annotations or selectable colors;
- Markdown notes, tags, search, and sorting;
- manual relocation of unresolved notes;
- full-text search and a richer book index;
- export notes as reading-journal Markdown;
- IndexedDB offline cache;
- PWA or desktop packaging;
- multi-device synchronization.
- a broader REST API for multi-chapter and additional-resource operations.

Adopt IndexedDB only if real whole-book scale, offline behavior, or search measurements justify it. Do not preemptively add a second persistence source in version 1.

## 12. Immediate next step

Execute Phase 0: create the project skeleton, the empty Chapter 05 annotation JSON, deterministic build entry point, and restricted local launcher. Begin visual implementation only after Phase 0 passes its exit criteria.
