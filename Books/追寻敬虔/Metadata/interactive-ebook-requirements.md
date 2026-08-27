# Local Interactive Edition of *A Quest for Godliness*: Requirements

> English execution version. Chinese review version: `interactive-ebook-requirements-zh.md`.

The English version is normative for implementation. Product decisions must be reviewed in Chinese and then reflected in both files in the same change. If the two versions conflict, stop implementation and reconcile them first.

## 1. Purpose

This document defines the product scope, technical direction, data model, and acceptance criteria for generating a local interactive edition of *A Quest for Godliness* from the reviewed Markdown sources.

Chapter 05, “John Owen on Communication from God,” is the first prototype. After that prototype is accepted, the same build pipeline will be extended to the rest of the book.

## 2. Existing inputs

- Body: `Reading/第2部分-清教徒与圣经/05-約翰．歐文論從神而來的交通.md`
- Footnotes: `References/Footnotes-05.md`
- Word source: `Original/QFG Draft 20170911 20211005.doc`
- Word-to-Markdown rules: `Metadata/word-to-markdown-spec.md`

The Chapter 05 Markdown already contains machine-readable structure:

- YAML metadata;
- one chapter heading and section headings;
- normal paragraphs, block quotations, and emphasis;
- links to specific headings in `Footnotes-05.md`.

The reviewed Markdown is the sole body-content source for the website. The web build must not reinterpret the Word file or introduce a separately maintained HTML copy of the chapter.

## 3. Product goals

The project will provide a local-first interactive book suitable for sustained reading:

1. Faithfully render the current Markdown structure and formatting.
2. Display, collect, and dismiss footnotes in the left panel without moving away from the reading position.
3. Let the reader select body text and create, edit, save, and delete private notes in the right panel.
4. Highlight annotated text and reopen the corresponding note when the highlight is clicked.
5. Restore the theme, panel preferences, notes, and highlights after the application is restarted.
6. Generate all chapters through one reusable build process rather than chapter-specific handwritten HTML.

## 4. Non-goals for version 1

- Scripture lookup or Scripture text in the left panel;
- cloud sync, accounts, or collaboration;
- a complete three-column editing experience on phones;
- EPUB, Kindle, Electron, or Tauri packaging;
- rich-text notes, images, or handwritten annotations;
- cross-chapter full-text search;
- automatic write-back from web notes into the source Markdown or Word document.

These items may be supported later, but they are not part of the Chapter 05 acceptance scope.

## 5. Technical direction

### 5.1 Decision

Use a local static web application built with HTML, CSS, and native JavaScript. A build step compiles the chapter Markdown and footnotes into web assets, and a loopback-only local service exposes those assets at `localhost`.

```text
Reviewed Markdown + References
              ↓ build
      HTML + CSS + JavaScript
              ↓ local browser
  Reading UI + repository note JSON
```

CSS owns layout, typography, themes, and highlights. JavaScript owns footnote interaction, selection, note editing, and calls to the note API. HTML contains the built semantic chapter content.

### 5.2 Why a double-clickable HTML file is not the primary design

A self-contained HTML file could demonstrate Chapter 05, but it is unsuitable as the long-term book workflow:

- `file://` pages have restrictions on reading and writing other local files;
- local storage origins vary across browsers and file locations;
- multi-chapter navigation and shared assets become difficult to maintain;
- source files and generated files are easier to confuse;
- Safari and Chrome cannot silently write arbitrary repository JSON from a normal page.

The application therefore runs at a stable `localhost` origin. It remains local and fully usable without an internet connection. The local service also exposes a narrowly scoped endpoint that writes chapter note JSON files.

### 5.3 Alternatives

| Route | Strengths | Limitations | Decision |
| --- | --- | --- | --- |
| One double-clickable HTML file | Simple to distribute | Weak multi-file workflow and unreliable persistence | Demonstration only |
| Static app plus local service | Offline, light, scalable to the book, repository persistence | Requires starting a local process | Selected |
| React or Vue | Component and state tooling | Unnecessary build and dependency cost for version 1 | Defer |
| Electron or Tauri | Native file access and desktop packaging | Substantial packaging and maintenance cost | Do not use now |
| EPUB | Good conventional reading format | Cannot reliably provide the required three-panel note workflow | Not the primary format |

Version 1 should use native browser JavaScript and no front-end framework. Any build-time Markdown parser must be version-pinned and must not require runtime network access.

## 6. Information architecture and layout

### 6.1 Desktop layout

Use three columns:

| Region | Purpose | Behavior |
| --- | --- | --- |
| Left | Open footnotes; later, Scripture | Stays within the viewport and scrolls independently |
| Center | Chapter body | Primary reading surface with a comfortable line length |
| Right | Note list, viewer, and editor | Stays within the viewport and scrolls independently |

The center text width should target approximately 42–48 full-width Chinese characters. Panel widths and text width must be controlled through CSS variables.

### 6.2 Narrow viewports

Desktop browsers are the primary version 1 environment. When all columns cannot fit:

- preserve a readable center column;
- turn the left and right panels into toggleable drawers;
- do not require simultaneous three-column display on a phone;
- never discard an unsaved note when a panel is hidden.

### 6.3 Toolbar

Provide a compact fixed toolbar with:

- theme selection;
- left-panel toggle;
- right-panel toggle;
- current chapter title;
- a reserved chapter-navigation control, shown as a disabled or single-option menu in the Chapter 05 MVP;
- note save status.

“Show all” and “Clear” belong at the top of the footnote panel. The note panel must clearly show the current editor state.

## 7. Functional requirements

### 7.1 Markdown rendering

1. Strip YAML front matter from the visible body while retaining useful values as page metadata.
2. Render headings, paragraphs, block quotations, emphasis, and links according to their current Markdown semantics.
3. Do not edit source content in the browser.
4. Intercept chapter-footnote links instead of performing normal navigation.
5. Keep ordinary links functional and visually distinct from footnote triggers.
6. Assign a stable identifier to every annotatable body block.

### 7.2 Reading themes

Provide three themes:

- light: light background and dark body text;
- dark: dark background and light body text;
- sepia/eye-care: warm, low-glare background and dark brown-gray text.

Requirements:

1. Use CSS custom properties rather than three duplicated stylesheets.
2. Apply themes to all panels, controls, inputs, links, focus states, and highlights.
3. Persist the selected theme locally and restore it on restart.
4. The first visit may follow the system preference; an explicit user choice takes priority afterward.
5. Maintain clear contrast for text, links, controls, and form fields in every theme.

### 7.3 Footnotes

1. Clicking a footnote trigger adds its card to the left panel and brings that card into view.
2. Clicking the same trigger again closes only that footnote.
3. Multiple footnotes may be open and remain in click order.
4. “Show all” displays every chapter footnote in first-reference order.
5. “Clear” closes all open footnotes.
6. Each card has its own close control and visible identifier.
7. Preserve paragraphs, emphasis, and ordinary links inside footnote content.
8. Opening or closing a footnote must not change the center-column scroll position.
9. Triggers for open footnotes must have an active state.
10. Non-numeric identifiers such as translator notes must work.

The left-panel internal model must reserve a content `type`, initially `footnote`, so that `scripture` can be added later without rewriting the panel architecture.

The toolbar must reserve a table-of-contents or chapter dropdown location even though the MVP contains only Chapter 05. It must not fabricate links to chapters that have not been built.

### 7.4 Creating a note

Version 1 permits a continuous selection within one annotatable body block only. A block may be a heading, paragraph, or one paragraph inside a block quotation. Cross-block selection is deferred.

Flow:

1. The reader selects non-empty text in the center article.
2. A “Write note” action appears near the selection.
3. A contextual right-click action may provide the same command.
4. The right panel opens a new-note editor with the quotation and an empty note field.
5. A note is created only after “Save” succeeds; canceling leaves no record or highlight.
6. Whitespace-only, side-panel, cross-block, footnote-marker, and overlapping selections are rejected with a short explanation.

The floating action is the primary entry point. The implementation must not remove access to the browser’s native context menu in all circumstances.

### 7.5 Viewing, editing, saving, and deleting notes

1. After a successful save, close the editor by default and highlight the source text.
2. Clicking highlighted text opens the matching note in the right panel.
3. Show the quotation, body, creation time, and last-modified time.
4. Saved notes remain editable.
5. Do not replace the saved body until “Save changes” succeeds.
6. Warn before switching away from unsaved changes.
7. Confirm deletion; remove the JSON record and highlight only after deletion is saved.
8. When no note is active, show the chapter note list.
9. Selecting a list item scrolls the highlight into a comfortable viewport position and opens the note.
10. Multiple non-overlapping notes may exist in one block. Overlap is prohibited in version 1.

### 7.6 Note format

Version 1 uses plain text:

- preserve line breaks;
- never execute note HTML;
- provide no Markdown preview or rich-text toolbar;
- keep `format: "plain-text"` in the schema for future migration.

## 8. Anchoring and persistence

### 8.1 Anchor design

Character offsets alone become invalid when earlier text changes. DOM paths also break when Markdown rendering changes. Each note must therefore store a block identifier, offsets, the exact quote, and short surrounding context.

```json
{
  "schemaVersion": 1,
  "bookId": "qfg",
  "chapterId": "05",
  "notes": [
    {
      "id": "generated-note-id",
      "sourceRevision": "chapter-content-hash",
      "anchor": {
        "blockId": "05-p-0017",
        "startOffset": 24,
        "endOffset": 39,
        "exact": "selected source text",
        "prefix": "short preceding context",
        "suffix": "short following context"
      },
      "body": "plain-text note",
      "format": "plain-text",
      "createdAt": "ISO-8601 time",
      "updatedAt": "ISO-8601 time"
    }
  ]
}
```

Restore anchors in this order:

1. Verify `blockId + startOffset + endOffset` against `exact`.
2. Search for a unique `exact + prefix + suffix` match in the original block.
3. If the block changed, search all annotatable chapter blocks for a unique contextual match.
4. If no unique match exists, retain the note as “needs relocation” and do not draw an incorrect highlight.

Generated block IDs must be deterministic. They must never be random on each build.

### 8.2 Repository persistence

One repository JSON file per chapter is the sole source of truth for notes. Version 1 reads and saves that file through the local service and does not persist notes in IndexedDB.

Chapter-sized JSON is small enough to parse directly. Avoiding IndexedDB also avoids a two-source synchronization problem. `localStorage` is limited to UI preferences.

Store annotation files under `Notes/Annotations/`; Chapter 05 uses `Notes/Annotations/05.json`. These files are source content and must be committed to Git. Generated pages must neither embed nor copy private notes.

Safari and Chrome pages cannot silently modify arbitrary repository files. The local process must therefore provide a strictly limited notes API that can access only registered chapter JSON files.

Save requirements:

- save the complete chapter JSON after each create, edit, or delete action;
- write a temporary file and atomically replace the destination;
- validate the schema and chapter identity before writing;
- use UTF-8, two-space indentation, stable field ordering, and a final newline;
- do not rewrite a file when its semantic content has not changed;
- retain editor content and show a failure state when saving fails;
- do not add a separate browser-database import/export workflow in version 1.

## 9. Source and build layout

```text
Books/追寻敬虔/
├── Reading/                  # reviewed Markdown
├── References/               # footnotes, Scripture, bibliography
├── Notes/Annotations/        # one Git-tracked note JSON per chapter
├── Metadata/                 # requirements and specifications
└── Web/
    ├── src/                  # templates, CSS, and JavaScript
    └── dist/                 # deterministic generated output
```

Workflow:

1. Review a chapter against the Word source.
2. Run Markdown and footnote audits.
3. Build the website.
4. Compile the chapter and its footnotes into web output.
5. Start the local service and inspect the page in Safari and Chrome.
6. Save notes directly through the local service to `Notes/Annotations/`.

`Web/dist` must not be committed. Builds must be deterministic and contain no notes. Web source, build configuration, and `Notes/Annotations/*.json` must be committed.

## 10. Error handling

- Missing footnote source or target: fail the build or show a clear broken-reference state; never navigate to an empty location.
- Unresolved note anchor: retain the note under “needs relocation”; never silently delete it.
- Save failure: keep the editor contents and do not show “Saved.”
- Invalid chapter JSON: do not write; retain the last successfully loaded UI state.
- Leaving with unsaved edits: warn the reader.
- Concurrent tabs or browsers: detect stale writes and prevent silent overwrites.

## 11. Privacy, security, and accessibility

1. Keep all body content and notes on the local machine.
2. Do not load scripts, styles, or fonts from a CDN.
3. Do not execute untrusted Markdown or note text as raw HTML.
4. Make controls and panels keyboard-operable with visible focus states.
5. Expose expanded footnote state and panel labels to assistive technology.
6. Do not use color as the only signal for an annotation or open footnote.
7. Centralize base type size, line height, and text width in CSS variables.
8. Bind the service to loopback only and expose no arbitrary file-write endpoint.

## 12. Chapter 05 prototype scope

- the complete Chapter 05 body and all 35 footnote entries;
- light, dark, and sepia themes;
- desktop three-column layout with narrow-screen drawers;
- individual and multiple footnote opening, closing, show-all, and clear-all;
- same-block selection and a floating “Write note” action;
- plain-text create, save, hide, reopen, edit, and delete;
- orange body highlights and a chapter note list;
- one chapter JSON file and a restricted local note API;
- recovery after small body revisions and a visible unresolved-anchor state;
- fully offline operation.

## 13. Acceptance criteria

### Reading and themes

- The chapter title, eight section headings, paragraphs, quotations, and emphasis render correctly.
- Themes switch immediately and survive refresh.
- Independent panel scrolling does not cause unrelated columns to jump.

### Footnotes

- Every body reference opens the correct content, including two translator notes.
- Clicking an open reference closes only that note.
- “Clear” closes all open cards.
- “Show all” displays all footnotes in body-reference order.

### Notes

- A valid same-block selection can create a note through the floating action.
- A successful save closes the editor, draws an orange highlight, and updates the chapter JSON.
- Refreshing or restarting restores the note and highlight from JSON.
- Clicking a highlight opens the correct editable note.
- Successful deletion removes both JSON data and the highlight.
- Canceling creation leaves no empty record or highlight.
- Cross-block and overlapping selections are rejected with an explanation.

### Resilience

- Inserting a paragraph before an annotated block and rebuilding still restores the note through contextual matching.
- A note that cannot be uniquely restored is listed as unresolved and is never highlighted against the wrong text.
- A successful save produces an immediately reviewable Git diff in the chapter JSON.

## 14. Confirmed decisions

1. Access the application through local `localhost`.
2. Officially support Safari and Chrome in version 1.
3. Limit selections to a continuous range within one body block.
4. Prohibit overlapping note ranges.
5. Use plain-text note bodies.
6. Use one repository JSON file per chapter as the sole source of truth; do not use IndexedDB in version 1.
7. Keep notes out of `Web/dist`; deterministic generated output is not committed.
8. Use one orange highlight palette adjusted for each theme.

The MVP uses only the minimum loopback endpoints needed for chapter notes. The local API may later be reorganized into a broader REST API when multiple chapters or additional resources justify it; that future shape is not required for the Chapter 05 MVP.

## 15. Recommended implementation order

1. Create the web directories, deterministic builder, and Chapter 05 page.
2. Implement layout, themes, and responsive drawers.
3. Implement the footnote index and left-panel behavior.
4. Implement deterministic block IDs and selection mapping.
5. Implement the chapter JSON model, restricted API, and anchor restoration.
6. Implement the note list, editor, delete flow, and unsaved-change warnings.
7. Implement atomic saves, revision conflicts, and unresolved anchors.
8. Run automated checks and manual Safari/Chrome acceptance testing.
9. Revise the specification from real reading feedback before building the whole book.
