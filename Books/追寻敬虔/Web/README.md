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

The current reader deterministically builds all 20 chapters and includes working chapter navigation, the three-column reading layout, responsive side panels, light/dark/sepia themes, left-panel footnote and Scripture interaction, and a per-chapter annotation workflow. The annotation panel shows the three most recently updated notes by default and can expand to show all notes.

The local service exposes a per-chapter note data layer. `GET /api/chapters/{chapter}/notes` reads the Git-tracked JSON source, while revision-checked `PUT` requests save it atomically. Select a continuous range inside one body block, use “Write note,” and manage the saved note from the right panel. Version 1 rejects cross-block and overlapping selections.
