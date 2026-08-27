---
name: qfg-word-to-markdown
description: Convert chapters of the Chinese book 《追寻敬虔》 from its legacy Word draft into repository-compliant Markdown while preserving Word heading levels, indented quotations, italicized titles or foreign terms, paragraph boundaries, and linked chapter footnotes. Use when extracting, repairing, auditing, or regenerating files under Books/追寻敬虔/Reading and Books/追寻敬虔/References from Original/QFG Draft 20170911 20211005.doc.
---

# Convert 《追寻敬虔》 Word chapters to Markdown

Treat the Word draft as the content and style authority. Treat the repository's metadata and file layout as the Markdown packaging authority.

## Required context

Read `Books/追寻敬虔/Metadata/word-to-markdown-spec.md` completely before converting or reviewing a chapter. It contains the canonical mapping, footnote policy, exceptions, and QA gates.

## Workflow

1. Inspect the target Markdown, its neighboring chapters, and the canonical specification.
2. Open the original `.doc` in Microsoft Word, repaginate it, and record the physical page containing the body `heading 1` for the target chapter and the next chapter. Ignore the table-of-contents occurrence. The source range is `target start` through `next start - 1`. For chapter 20, use Word's total physical page count as the end. Do not substitute LibreOffice/PDF pagination: this legacy document reflows differently outside Microsoft Word.
3. Run `scripts/convert_qfg_chapter.py` against `Books/追寻敬虔/Original/QFG Draft 20170911 20211005.doc`, first writing to temporary output paths, and pass the verified range with `--source-pages START-END`.
4. Compare temporary output with the existing chapter. Preserve intentional repository metadata while preferring Word text, paragraph structure, and semantic styles.
5. Verify the page range, all headings, quotations, inline italics, footnote references, footnote bodies, and chapter boundaries.
6. Write the approved chapter and `References/Footnotes-NN.md` only after the audit passes.
7. Run the script again with `--audit-only`, then run the link/content checks in the canonical specification.

## Command pattern

Use the bundled workspace Python runtime. Make `soffice` available on `PATH` or pass it explicitly when the source remains `.doc`.

```bash
python scripts/convert_qfg_chapter.py \
  "Books/追寻敬虔/Original/QFG Draft 20170911 20211005.doc" \
  --chapter 5 \
  --source-pages 97-116 \
  --output "Books/追寻敬虔/Reading/第2部分-清教徒与圣经/05-約翰．歐文論從神而來的交通.md" \
  --footnotes "Books/追寻敬虔/References/Footnotes-05.md"
```

## Page-range detection on macOS

Use Microsoft Word's AppleScript dictionary so the result comes from Word's own layout engine:

1. Open the source document and run `repaginate` on the active document.
2. Reset the active selection to character position 0.
3. Set the selection's find-object style to `style heading1`, enable `find format`, and search for the target chapter marker. Read `active end page number` with `get selection information`.
4. Repeat for the next chapter marker. Subtract one from that page to obtain the target chapter's final page.
5. Report the matched text and character range together with the page number. This makes a table-of-contents match or failed style filter visible during audit.

AppleScript automation may require local approval to control Microsoft Word. Keep the operation read-only and close the source without saving if the skill opened it.

## Non-negotiable rules

- Do not modernize, silently correct, summarize, translate, or reorder the source prose.
- Do not infer headings from typography when a reliable Word paragraph style exists.
- Do not interpret proofing or editing character styles such as `labellist`, `textblue`, or `st` as semantic Markdown.
- Do not leave raw footnote numbers or symbols in the body. Link every Word footnote reference to its chapter footnote file.
- Do not include the following part or chapter heading in the current chapter.
- Do not accept a table-of-contents hit as the chapter start, and do not infer Word page numbers from a LibreOffice-rendered PDF.
- Do not overwrite a hand-edited chapter until temporary output has been compared and audited.
