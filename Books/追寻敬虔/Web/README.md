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

Open `http://127.0.0.1:4173/chapters/05/` in Safari or Chrome.

The current MVP includes deterministic Chapter 05 rendering, a reserved chapter menu, the three-column reading layout, responsive side panels, light/dark/sepia themes, and left-panel footnote interaction. Note persistence belongs to a later roadmap phase.
