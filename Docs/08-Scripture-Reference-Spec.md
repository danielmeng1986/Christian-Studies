# 8. Scripture Reference Specification

**Version:** 1.0  
**Scope:** Entire Christian Studies repository  
**Audience:** AI agents, build scripts, and maintainers implementing Scripture links and interactive readers

The Chinese review version is [08-Scripture-Reference-Spec-zh.md](08-Scripture-Reference-Spec-zh.md). Keep both versions semantically aligned. Use this English version as the authoritative implementation contract when a machine rule would otherwise be ambiguous; use the Chinese version as the authority for the intended reading experience.

## 1. Core model

1. Markdown records semantic Scripture references; it does not duplicate passage text.
2. `References/Bible-Texts/` is the sole text, translation-metadata, and book-mapping authority.
3. Resolve and validate references at build time. Embed only passages used by the current chapter.
4. At runtime, the browser only toggles cards and switches among already compiled translations. It must not load a full Bible corpus.
5. Preserve the source-visible citation exactly. A source label such as `來11.39` must not be rewritten merely because CUV-S is the default translation.
6. Every generated passage must identify its translation.
7. Never silently replace a verbatim Scripture quotation already present in an imported source. Generated corpus text is a parallel reference, not a correction.

## 2. Authoritative files

```text
References/
├── Scripture.md
└── Bible-Texts/
    ├── manifest.json
    ├── books.json
    ├── citation-aliases.json
    └── versions/<translation>/verses.json

Books/<Book>/
├── Metadata/scripture-config.json
├── Reading/**/*.md
└── References/Scripture.md
```

- `manifest.json` defines translation IDs, labels, languages, provenance, and licenses.
- `books.json` defines canonical 66-book codes, localized names, and preferred abbreviations.
- `citation-aliases.json` maps source aliases to canonical book codes.
- `verses.json` supplies passage text.
- `Metadata/scripture-config.json` defines book-level defaults and allowed translations.
- Book-level `References/Scripture.md` records exceptions and policy, never duplicate passage bodies.

## 3. Markdown authoring contract

Use an ordinary Markdown link with a `scripture:` URI:

```markdown
[路4:23](scripture:LUK.4.23)
[路1:44-45](scripture:LUK.1.44-45)
```

The label is source-authoritative. The target uses canonical uppercase book codes.

### 3.1 URI grammar

```text
scripture:<BOOK>.<CHAPTER>.<VERSE-SPEC>[;<CHAPTER>.<VERSE-SPEC>][?version=<ID>]
```

Definitions:

- `BOOK` is a canonical code from `books.json`, such as `GEN`, `LUK`, or `HEB`.
- `CHAPTER` is a positive decimal integer.
- `VERSE-SPEC` is a single verse, an inclusive range, or a same-chapter comma list.
- Optional `version` selects the initially displayed translation and must be allowed by the book config.

Valid targets:

```text
scripture:LUK.4.23
scripture:LUK.1.44-45
scripture:JER.36.3,8
scripture:1TH.1.5-10;2.13
scripture:1CO.2.4,5;15.25,26
scripture:LUK.1.44-45?version=kjv
```

Version 1 does not allow one link to span multiple books. Create separate links for separate books.

### 3.2 Visible punctuation

- Labels may preserve source `:`, `：`, `.`, `．`, `-`, `–`, commas, and semicolons.
- URIs use only ASCII `.`, `,`, `;`, and `-` delimiters.
- Do not normalize a Word source's book abbreviation, digits, or punctuation for appearance alone.
- Keep same-book continuations in one semantic link:

```markdown
[耶36:3, 8](scripture:JER.36.3,8)
[帖前1:5-10; 2:13](scripture:1TH.1.5-10;2.13)
```

## 4. Book-level translation configuration

Use `Books/<Book>/Metadata/scripture-config.json`:

```json
{
  "schema_version": 1,
  "default_translation": "cuv-s",
  "available_translations": ["cuv-s", "kjv"],
  "translation_labels": {
    "cuv-s": "新标点和合本简体",
    "kjv": "King James Version 1769"
  }
}
```

Requirements:

1. `default_translation` must occur in `available_translations`.
2. Every ID must exist in the shared manifest.
3. A link without `version` initially uses the default.
4. A link with `version` initially uses that translation, but the card may still switch to every configured translation.
5. Changing book defaults must not require rewriting Markdown links.
6. Optional `translation_labels` override translation display names for this book. Every key MUST name an available translation and every value MUST be a non-empty string.

《追寻敬虔》 uses `cuv-s` by default.

## 5. Build-time resolution

The builder must:

1. Recognize every `scripture:` link and convert it to a non-navigating interactive reference.
2. parse the URI strictly and reject unknown books, invalid chapters, reversed ranges, malformed selectors, and disallowed translations;
3. load every requested verse from each configured translation's `verses.json`;
4. fail with the translation and canonical reference if any requested verse lacks an independent record; never silently fall back to another translation;
5. embed only passages referenced by the current chapter as safe JSON or an equivalent static resource;
6. deduplicate identical canonical references so repeated links control one card; and
7. remain deterministic: identical Markdown, configuration, and corpus inputs must produce byte-identical output.

Generated anchors must include at least:

```html
<a class="scripture-ref"
   href="#scripture-LUK.4.23"
   data-scripture-id="LUK.4.23"
   data-initial-version="cuv-s"
   aria-controls="reference-panel"
   aria-expanded="false">路4:23</a>
```

## 6. Passage rendering

### 6.1 Joining verse text

- Remove VPL book/chapter/verse prefixes.
- Join Chinese verse records with an empty string.
- Join English verse records with exactly one ASCII space.
- Preserve all translation text, punctuation, paragraph marks, and brackets. Do not edit or repair it.
- Join discontinuous verses and chapter continuations in URI order.

### 6.2 Citation line and translation identity

The translation selector in the card header is the sole current-translation label. The citation line MUST contain only the localized book label and passage selector; it MUST NOT repeat the translation name.

For a Chinese translation, use its preferred localized abbreviation:

```text
路 1:44–45
```

For an English translation, use its English book name:

```text
Luke 1:44–45
```

Do not expose internal codes such as `LUK` as the default reader-facing label. The selector MUST always expose the active translation's full display label.

## 7. Shared left-panel interaction

The left column is a typed reference panel for both footnotes and Scripture. It is not a footnote-only container.

Use stable typed keys:

```text
footnote:12
scripture:LUK.4.23
```

Behavior:

1. Clicking a footnote or Scripture anchor opens its card in the left panel.
2. Clicking the same anchor again closes that card.
3. Footnote and Scripture cards may remain open simultaneously.
4. “Show all” opens every chapter footnote and Scripture item; “Clear” closes all items.
5. Each Scripture card has a translation selector initialized from the link override or book default.
6. Switching a card changes only that card. It does not mutate configuration or Markdown.
7. All anchors controlling an open item share an active state and correct `aria-expanded`.
8. Preserve the existing responsive panel-collapse behavior.

## 8. Annotation compatibility

Reference-link text is visible prose but is excluded from annotation anchor canonical text. Selection, offset calculation, and anchor restoration must exclude both `.footnote-ref` and `.scripture-ref`. Users must not create a note selection containing either reference type. This prevents link additions or changes from shifting saved annotation anchors.

## 9. Acceptance gates

An implementation is complete only when:

1. every Markdown Scripture link has one valid canonical target;
2. every requested verse resolves in every configured translation;
3. Chinese verses have no inserted inter-verse spaces and English verses have exactly one;
4. card headers show the active translation name and citation lines show only the localized reference;
5. click, second click, close, show-all, clear, and translation switching work;
6. existing footnote behavior has no regression;
7. note selection rejects both link types and existing anchors remain stable;
8. Safari and Chrome work through localhost without external network access; and
9. repeated builds are byte-identical and do not embed full Bibles or local machine paths.

## 10. Copyright and evolution

- Add a full translation to the corpus only when its license permits storage, redistribution, and the intended software or AI use.
- Do not scrape copyrighted translations into the repository. Use an authorized API or explicit license.
- A future REST API must preserve the `scripture:` Markdown URI, canonical book codes, and book configuration; replace only the resolution/transport layer.
- A generated chapter Scripture inventory may exist for review, but it is derived output and never a second passage-text authority.
