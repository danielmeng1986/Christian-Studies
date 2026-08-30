# Local reader development

> English execution guide. Chinese review guide: `README-zh.md`.

## Setup

From the repository root:

```sh
python3 -m venv 'Books/追寻敬虔/Web/.venv'
'Books/追寻敬虔/Web/.venv/bin/python' -m pip install -r 'Books/追寻敬虔/Web/requirements.txt'
```

## Build and test

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/build.py'
'Books/追寻敬虔/Web/.venv/bin/python' -m unittest discover -s 'Books/追寻敬虔/Web/tests'
```

Generated files are written to `Books/追寻敬虔/Web/dist/` and are intentionally ignored by Git.

## Read locally

```sh
'Books/追寻敬虔/Web/.venv/bin/python' 'Books/追寻敬虔/Web/scripts/serve.py'
```

Open `http://127.0.0.1:4173/chapters/01/` in Safari or Chrome. Use the top menu to navigate between all 20 chapters.

The current reader deterministically builds all 20 chapters and includes working chapter navigation, a current-chapter outline with live section/progress feedback, the three-column reading layout, responsive side panels, light/dark/sepia themes, left-panel footnote and Scripture interaction, per-chapter annotations, AI discussions, and a local source library. The outline opens from the top toolbar and stays separate from reading-context references. The annotation panel shows the three most recently updated notes by default and can expand to show all notes.

The divider beside the study panel can be dragged or adjusted with the arrow keys, and double-clicking restores the default width. Notes and AI discussions remember separate widths. AI discussion mode collapses the reference panel by default and opens it as an overlay on demand so it does not squeeze the reading or discussion columns. On narrow screens both side panels remain overlays.

Completed AI replies are rendered as safe Markdown, including headings, lists, quotations, emphasis, links, code blocks, and tables. Discussion JSON files continue to store the original Markdown rather than derived HTML. Raw HTML and unsafe link protocols are not executed, while user messages remain plain text.

The local service exposes a per-chapter note data layer. `GET /api/chapters/{chapter}/notes` reads the Git-tracked JSON source, while revision-checked `PUT` requests save it atomically. Select a continuous range inside one body block, use “Write note,” and manage the saved note from the right panel. Version 1 rejects cross-block and overlapping selections.

The first AI discussion MVP is implemented. A same-block selection can include Scripture and footnote links and offers both note and AI discussion actions. Discussions stream through the local Python service and persist as one JSON file per thread under `Notes/Discussions/<chapter>/`. The browser never receives the OpenAI API key.

Before a turn is sent, the reader now shows a compact local context preview. Exact and overlapping personal notes are selected by default and can be excluded individually; non-overlapping notes in the same block remain unsent candidates. Translation-index identity matches are shown separately: exact matches can be excluded, while ambiguous candidates require explicit selection. Relevant passages from other chapters are listed separately and can be expanded, opened at their source block, excluded one by one, or expanded with “find more book content.” These choices affect only that turn and never edit or delete the underlying notes or book sources.

The Library tab imports Markdown, TXT, JSON, and text-extractable PDF files only after a conversion preview is confirmed. Originals remain unchanged under `Sources/`, while structured processed copies drive a disposable, fully rebuildable index. Private sources are disabled by default. A local-library hit is never sent automatically: its source first needs explicit outbound approval, and the exact chunk must then be selected in that turn's context preview. Removing a derived index never removes the original or processed copy.

The preview now freezes a short-lived server-side context build. Sending requires the matching build ID; the server re-reads and hashes every source before using that exact bundle in the Responses payload. The preview shows a deliberately conservative token estimate and blocks visible overflow without truncating required evidence or history. New discussion files use schema version 2 with one manifest per user turn. Version 1 discussions remain readable and migrate only when the user continues them; historical turns are marked as legacy without invented manifests.

Start without `OPENAI_API_KEY` to keep reading and notes available with AI sending disabled. On macOS, a website-password item can be injected with `--keychain-internet-password-label`; a generic Keychain item can be injected with `--keychain-generic-password-service`. Do not paste a current project key into the interactive `security add-generic-password -w` prompt: that prompt truncates input beyond 128 characters. Create the restricted item with a non-secret placeholder as documented in `README-zh.md`, then use `scripts/store_openai_key.py` to replace and verify the complete value through Security.framework. Neither setup path exposes the secret in shell history or process arguments. The secret exists only as `OPENAI_API_KEY` in that server process; do not store it in the repository, `.env`, scripts, or command arguments. Full requirements, data model, defaults, and security boundaries are documented in [`AI-DISCUSSION-SPEC-zh.md`](AI-DISCUSSION-SPEC-zh.md).
