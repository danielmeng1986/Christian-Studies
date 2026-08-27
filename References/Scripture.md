# Scripture References

Repository-level Bible texts are stored in [Bible-Texts](Bible-Texts/README.md). The corpus currently includes CUV-T, CUV-S, KJV, ASV, WEB, and BSB.

## Default translations

- Use `CUV-T` when supplying Chinese Scripture alongside traditional-Chinese source material unless the source identifies another translation.
- Use `CUV-S` when the surrounding document is simplified Chinese.
- Use `KJV` when historical wording or English material from the early modern and Puritan periods makes it relevant.
- Use `WEB` or `BSB` when a modern public-domain English rendering is preferable.
- Always label the translation when inserting wording that was not already quoted in the source.

## Citation form

Human-readable citations remain preferable in prose, for example `约 3:16`、`羅 8:1–4`, or `John 3:16 (KJV)`. Structured tools should resolve these names through `Bible-Texts/citation-aliases.json` and `Bible-Texts/books.json`, then retrieve text from the chosen version's `verses.json`.

`books.json` defines one canonical code and two preferred Chinese abbreviations for every book. For example, `GEN -> 創 / 创 (創世記 / 创世记)`, `LUK -> 路 (路加福音)`, and `HEB -> 來 / 来 (希伯來書 / 希伯来书)`. Parsers accept both scripts regardless of the selected Chinese translation; display code should choose the abbreviation matching the interface language.

Do not silently replace Scripture wording already present in a studied book. Displaying a corpus translation beside an imported quotation is a comparison, not a correction.

## Copyright boundary

Only translations whose full-text license permits repository storage and redistribution belong in `Bible-Texts/`. Copyrighted translations may be cited within their quotation limits or accessed through an authorized API, but their complete text must not be copied into this repository without an appropriate license.
