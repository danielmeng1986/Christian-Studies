# Local Interactive Edition of *A Quest for Godliness*: Implementation Specification

> English execution version. Chinese review version: `interactive-ebook-implementation-spec-zh.md`.

The English version is normative for implementation. Technical changes must be reflected in both language versions in the same change. If the two versions conflict, stop implementation and reconcile them first.

## 1. Specification status

This specification implements the confirmed decisions in `interactive-ebook-requirements.md`. Chapter 05 is the first target; all later chapters must use the same build and runtime architecture.

If implementation needs to diverge from this document, update the specification first and describe the compatibility impact. Never change the note JSON schema or anchoring rules without a migration plan.

## 2. Technical baseline

### 2.1 Application form

- The front end is a static application using HTML, CSS, and native JavaScript.
- Markdown is converted to HTML at build time, not parsed in the browser.
- A loopback-only service serves static files and a restricted notes API.
- Version 1 does not use React, Vue, IndexedDB, Service Workers, or cloud services.
- `localStorage` stores only UI preferences such as theme and panel visibility.
- The supported browsers are Safari and Chrome on the project machine.

### 2.2 Languages and dependencies

- Use Python 3 for the builder and local service.
- Use a pinned CommonMark-capable parser supporting headings, block quotes, emphasis, and links.
- Prefer Python’s standard library for HTTP and file I/O instead of a full web framework.
- Use native browser JavaScript, preferably as ES modules, with no CDN dependency.

Python aligns this project with the existing Word-to-Markdown tooling while leaving the browser application standards-based.

## 3. Directory contract

```text
Books/追寻敬虔/
├── Reading/
│   └── 第2部分-清教徒与圣经/
│       └── 05-約翰．歐文論從神而來的交通.md
├── References/
│   └── Footnotes-05.md
├── Notes/
│   └── Annotations/
│       └── 05.json
├── Metadata/
│   ├── interactive-ebook-requirements.md
│   ├── interactive-ebook-requirements-zh.md
│   ├── interactive-ebook-implementation-spec.md
│   ├── interactive-ebook-implementation-spec-zh.md
│   ├── interactive-ebook-roadmap.md
│   └── interactive-ebook-roadmap-zh.md
└── Web/
    ├── src/
    │   ├── assets/app.css
    │   ├── assets/app.js
    │   └── templates/chapter.html
    ├── scripts/
    │   ├── build.py
    │   └── serve.py
    ├── tests/
    ├── requirements.txt
    └── dist/
        ├── assets/
        └── chapters/05/index.html
```

Responsibilities:

- `Reading/`, `References/`, `Notes/Annotations/`, and `Web/src/` are maintained, Git-tracked sources.
- `Web/dist/` is reproducible generated output and is not committed.
- `Web/dist/` must never embed, copy, or cache notes.
- Runtime pages obtain notes only through the local API backed by `Notes/Annotations/05.json`.
- The builder must not modify Markdown, footnotes, or note JSON.

## 4. Build specification

### 4.1 Inputs and chapter identity

Each chapter entry must define `bookId`, `chapterId`, body path, footnote path, note path, and output path.

Chapter 05 uses:

```text
bookId: qfg
chapterId: 05
notes: Books/追寻敬虔/Notes/Annotations/05.json
page: Books/追寻敬虔/Web/dist/chapters/05/index.html
```

Read book title, chapter number, and source metadata from YAML front matter, but do not display the YAML block as article content.

### 4.2 Markdown mapping

| Markdown | HTML |
| --- | --- |
| `#` | the page’s single `h1` |
| `##` | `h2` |
| paragraph | `p` |
| `>` | `blockquote` containing paragraphs |
| `*text*` | `em` |
| ordinary link | `a` |
| link to `Footnotes-XX.md#anchor` | footnote trigger |

A footnote trigger must expose its identity and state:

```html
<a class="footnote-ref"
   href="#footnote-1"
   data-footnote-id="1"
   aria-controls="footnote-panel"
   aria-expanded="false">[1]</a>
```

Every body footnote target must exist in the chapter footnote source. A missing target is a build error.

### 4.3 Annotatable blocks and text coordinates

Annotatable blocks are `h1`, `h2`, ordinary paragraphs, and individual paragraphs inside block quotations. Generate a unique deterministic identifier for each:

```html
<p data-block-id="05-p-0017">…</p>
```

Version 1 may derive IDs from parsed block order. Anchor recovery must still verify exact text and use contextual fallback because inserting a block may shift later IDs.

The canonical annotatable text:

- includes normal text and text within inline semantic elements such as `em`;
- excludes footnote trigger text, controls, hidden templates, and accessibility-only UI text;
- must be selected entirely within one `data-block-id`;
- uses JavaScript string indices for offsets, always verified against `exact`.

### 4.4 Footnote compilation

- Each level-two heading in the footnote Markdown starts one footnote.
- Treat numeric and translator-note identifiers as strings.
- Compile footnotes into inert templates or static chapter data within generated output.
- Preserve paragraphs, emphasis, and ordinary links.
- Footnotes may enter `dist`; annotations may not.

### 4.5 Deterministic output

Identical source input must produce byte-stable or semantically stable output. Generated files must not contain build timestamps, random IDs, absolute user paths, or note JSON.

Any clean operation must target only the explicit `Web/dist/` directory. Post-build validation must check headings, outline targets, footnote count and targets, resource paths, and the absence of note content.

## 5. Page and style contract

Top-level structure:

```text
Application toolbar
└── Three-column reading region
    ├── Left: footnote panel
    ├── Center: article
    └── Right: note panel
```

### 5.1 Toolbar and columns

The toolbar includes the chapter title, chapter navigation, a current-chapter outline control, three theme choices, left/right panel toggles, and note save status. The build derives the outline in source order from the rendered `h1` and `h2` tokens and links each entry to the same deterministic block ID assigned to that heading.

The outline opens as a toolbar popover, not as content in the reference panel. Browser code updates `aria-current="location"`, the current-section label, and reading percentage from the center column's scroll position. Opening, closing, or using the outline must not change reference, note, or discussion state. Escape closes the popover and restores focus to its trigger; narrow viewports use the same outline and reduce only nonessential trigger text.

- Use CSS Grid when all three columns fit.
- Target 42–48 full-width Chinese characters in the reading column.
- Keep side panels within the viewport with independent scrolling.
- Convert side panels to overlay drawers on narrow viewports.
- Hiding a panel must preserve open footnotes, the active note, and unsaved editor contents.

### 5.2 Themes and highlight palette

Set the theme on the root element:

```html
<html data-theme="light|dark|sepia">
```

Each theme defines CSS variables for backgrounds, text, muted text, borders, links, controls, fields, focus rings, active footnotes, and annotation highlights.

Highlights use orange in every theme:

- light: pale orange background with dark text;
- dark: deeper orange-brown background with light text;
- sepia: low-saturation warm orange with dark brown text.

Add a border or other non-color indication. Final values must be verified in Safari and Chrome.

## 6. Footnote interaction

Maintain an ordered list of open footnote IDs.

- Clicking a closed trigger appends its ID and scrolls its card into the left-panel viewport.
- Clicking an open trigger removes only that ID.
- “Show all” uses first-reference order.
- “Clear” empties the list.
- A card close button removes only that card.
- Synchronize trigger styling and `aria-expanded`.
- Never move the article scroll position as a side effect.

Left-panel items must include a `type`; version 1 uses only `footnote`, while the model may later support `scripture`.

## 7. Chapter note JSON

### 7.1 File schema

`Notes/Annotations/05.json` starts as:

```json
{
  "schemaVersion": 1,
  "bookId": "qfg",
  "chapterId": "05",
  "notes": []
}
```

Note entry:

```json
{
  "id": "uuid",
  "sourceRevision": "sha256-of-canonical-article-text",
  "anchor": {
    "blockId": "05-p-0017",
    "startOffset": 24,
    "endOffset": 39,
    "exact": "selected source text",
    "prefix": "up to 32 preceding characters",
    "suffix": "up to 32 following characters"
  },
  "body": "plain-text note",
  "format": "plain-text",
  "createdAt": "2026-08-27T12:00:00.000Z",
  "updatedAt": "2026-08-27T12:00:00.000Z"
}
```

Constraints:

- `id` is immutable after creation.
- Root `bookId` and `chapterId` must match the requested chapter.
- `body` is non-blank Unicode plain text.
- `exact` is non-empty and `startOffset < endOffset`.
- Valid ranges must not overlap in version 1.
- Timestamps are UTC ISO 8601; editing updates only the note’s `updatedAt`.
- Sort notes by `createdAt`, then `id`.
- Serialize as UTF-8, LF, two spaces, and a final newline.

### 7.2 Source-of-truth rule

- Load the complete chapter JSON through the API.
- Browser memory is only a session working copy.
- Create, edit, or delete succeeds only after the service atomically writes JSON and returns a new revision.
- On failure, the editor remains dirty.
- Do not copy notes into IndexedDB.

## 8. Local service and API

### 8.1 Startup

- Bind only to `127.0.0.1`, never to a LAN interface by default.
- Use a configurable but stable default port so UI preferences share one origin.
- Validate repository root, `Web/dist`, and the note directory at startup.
- If output is missing or stale, provide a clear build instruction.
- The launcher may open a browser but must not assume the default browser is the only supported one.

### 8.2 Endpoints

Version 1 exposes whole-chapter operations only:

```text
GET /api/chapters/05/notes
PUT /api/chapters/05/notes
```

These are the minimum MVP endpoints. Keep handlers and routing separable so the local service can evolve into a broader REST API later, but do not add speculative resources in version 1.

`GET` returns the chapter JSON and an `ETag` or equivalent file revision.

`PUT` requirements:

- require `Content-Type: application/json`;
- validate the schema and chapter identity;
- require the revision read by the client;
- return `409 Conflict` and do not write when the revision is stale;
- return normalized data and a new revision on success.

### 8.3 File and request safety

The service must:

- resolve chapter IDs through a manifest, never by direct path concatenation;
- access only registered files inside `Notes/Annotations/`;
- limit request size and reject non-JSON writes;
- require same-origin requests and a per-session write token;
- write a same-directory temporary file, flush it, then atomically replace the destination;
- preserve the original file on failure;
- expose no general file browser, command execution, or arbitrary write API.

### 8.4 Concurrent edits

Stale writers must be rejected by revision matching. On conflict, the UI must preserve unsaved text, explain that the disk version changed, and offer to reload. Version 1 does not auto-merge.

## 9. Selection, notes, and anchor recovery

### 9.1 Creation

1. Observe selections only within the article.
2. Convert the browser Range to canonical offsets within one body block.
3. Reject blank, cross-block, footnote-containing, and overlapping selections.
4. Show “Write note” near the valid selection.
5. Open the right-panel editor with the quotation and an empty plain-text field.
6. Generate UUID and timestamps only when save is requested.
7. Close the editor and draw a highlight only after the API succeeds.

### 9.2 Open, edit, and delete

- Clicking an orange highlight opens its note.
- Editing preserves `id` and `createdAt`.
- A successful edit updates body, `updatedAt`, and the file revision.
- Confirm deletion and remove the highlight only after successful persistence.
- Warn before abandoning dirty state.
- When no editor is active, show the chapter note list; selecting an item scrolls to and opens it.

### 9.3 Anchor recovery order

1. Verify offsets and `exact` in the saved `blockId`.
2. Find a unique contextual match within that block.
3. Find a unique contextual match across all annotatable chapter blocks.
4. Otherwise mark the note “needs relocation” and do not highlight it.

If a note is recovered at a new location, use the recovered position in memory. Write the new anchor only when the user explicitly saves or edits that note, so page load alone does not create a Git diff.

### 9.4 Highlight rendering

- Use semantic `mark` elements carrying note IDs.
- Apply multiple non-overlapping ranges in reverse offset order within a block.
- Preserve inline semantics such as `em` and ordinary links.
- Never include a footnote trigger inside a highlight.
- Removing and rebuilding highlights must leave article plain text unchanged.

## 10. State and user feedback

Distinguish at least:

- saved;
- unsaved changes;
- saving;
- save failed;
- disk revision conflict.

Only an API success may produce “Saved.” Every failure must preserve user input. Error messages must identify missing footnotes, malformed note JSON, unresolved anchors, and request failures in concise Chinese UI text.

## 11. Safari and Chrome compatibility

- Do not use the File System Access API.
- Do not depend on Chromium-only selection or experimental CSS APIs.
- Implement selection with standard Selection, Range, and TreeWalker APIs.
- Keep the floating selection action as the primary command; right-click is secondary.
- Verify sticky positioning, nested scrolling, drawers, and selection in both browsers.
- Automated tests do not replace manual selection and context-menu checks in both browsers.

## 12. Verification

### 12.1 Build tests

- Two consecutive builds from identical input have no output diff.
- Output contains one `h1`, eight `h2` elements, and every Chapter 05 footnote.
- Output contains no absolute repository path, build time, or note body.
- A missing footnote target fails the build.

### 12.2 API tests

- Read empty and populated chapter files.
- Create, edit, and delete produce valid, stable JSON.
- Reject unknown chapters, path traversal, bad schema, oversized bodies, and incorrect content types.
- A stale revision returns a conflict and leaves the file unchanged.
- Simulated write failure leaves the original JSON intact.

### 12.3 Browser tests

- Themes and three-column state behave consistently in Safari and Chrome.
- All 35 footnotes, including two translator notes, work.
- Same-block selection, cross-block rejection, overlap rejection, save, edit, and delete meet requirements.
- Refresh, service restart, and switching browsers restore from the same JSON.
- After inserting an earlier paragraph and rebuilding, notes recover contextually or become explicitly unresolved.

## 13. Git and generated files

Commit:

- `Web/src/`, `Web/scripts/`, tests, and pinned dependencies;
- `Notes/Annotations/*.json`;
- English and Chinese Metadata documents.

Do not commit:

- `Web/dist/`;
- Python caches, temporary write files, or local logs;
- browser caches.

Validate note JSON before committing it. Tests must use temporary directories and fixtures, never real note files.

## 14. Version 1 definition of done

Chapter 05 is complete only when:

1. Its Markdown and footnotes build deterministically.
2. The loopback service opens it in Safari and Chrome.
3. Layout, themes, and footnotes pass acceptance.
4. Same-block, non-overlapping, plain-text notes complete the create/save/restore/edit/delete cycle.
5. Every successful save atomically updates `Notes/Annotations/05.json`.
6. The page and `dist` contain no note copy.
7. Anchor failures cannot cause incorrect highlights or data loss.
8. Automated checks and manual Safari/Chrome checks pass.
