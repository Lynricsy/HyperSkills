# Markdown to Word

Verified against: docx 9.7.1, marked 18.0, pandoc 3.10

## Contents

- [Which path to take](#which-path-to-take)
- [Path A: the bundled converter](#path-a-the-bundled-converter)
- [Path B: pandoc with a reference document](#path-b-pandoc-with-a-reference-document)
- [Building a reference document](#building-a-reference-document)
- [Things Markdown cannot express](#things-markdown-cannot-express)
- [Delivery gate](#delivery-gate)

## Which path to take

Default to the bundled Node converter: it has no native dependency, so it works
wherever Node does, and its output is fully under your control.

Switch to pandoc when the document has to match a house template — corporate
fonts, numbered heading styles, a cover page, named callout styles. Pandoc maps
Markdown onto styles that already exist in a reference document, which is far
less work than reimplementing that template in code.

| Requirement | Path |
|---|---|
| Plain report, memo, notes, no template | Bundled converter |
| Must match an existing corporate `.docx` look | pandoc + reference document |
| Footnotes, citations, cross-references | pandoc |
| Mermaid or LaTeX to be rendered | Pre-render to PNG, then either path |
| No native binaries allowed on the machine | Bundled converter |

## Path A: the bundled converter

```bash
cd scripts && npm install        # once, installs docx + marked
node scripts/md_to_docx.mjs input.md output.docx
```

Front matter drives a title page. Only these keys are read; anything else is
ignored:

```markdown
---
title: Vendor Report — Q3 Summary
date: 2026-09-10
version: 1.0
audience: Finance
---
```

The title splits on an em or en dash into a title and a subtitle. A contents
page is emitted automatically when the document has two or more headings at
level 3 or above; it is written as plain paragraphs rather than a Word TOC
field, so it is populated in the delivered file instead of waiting for the
reader to update fields.

Supported: ATX headings, paragraphs with bold, italic, strikethrough, inline
code and links, bullet and ordered lists including nesting, fenced code blocks,
pipe tables, block quotes, horizontal rules, and images.

Images are resolved relative to the Markdown file. PNG, JPEG, GIF and BMP are
embedded with their intrinsic size read from the file header and scaled down to
the 6.5-inch text width; anything else, including SVG, becomes a visible
`[unsupported image format]` note rather than a silent omission. Convert SVG to
PNG first.

To extend the converter, add a `case` to `blockParagraphs` for the token type
`marked` produces. Print `marked.lexer(text)` for an unfamiliar construct rather
than guessing the token shape.

## Path B: pandoc with a reference document

```bash
pandoc input.md -o output.docx --reference-doc=template.docx --toc --toc-depth=3
```

Pandoc takes paragraph and character styles from `template.docx` — it never
copies its body text. Styles it looks for by name include `Title`, `Author`,
`Date`, `Heading 1`–`Heading 9`, `Body Text`, `First Paragraph`,
`Block Text` (block quotes), `Verbatim Char` (code), `Table Caption`,
`Image Caption`, `Compact` (tight lists) and `Hyperlink`. To see the exact set
a pandoc build expects, list the style ids in its default reference document.

Callouts use a div with an explicit style name:

```markdown
::: {custom-style="Warning"}
Signing before the audit closes carries risk.
:::
```

The style has to exist in the reference document, spelled exactly as in Word,
including spaces and capitalisation. When it does not, pandoc still writes
`<w:pStyle w:val="NoSuchStyle"/>` into the document without a warning; the name
resolves to nothing, so the block renders with default formatting and the
callout appears to have done nothing. `[verified]` Grep the packed
`word/document.xml` for the style name to tell the two cases apart.

## Building a reference document

```bash
pandoc --print-default-data-file reference.docx > reference.docx
```

Open that file in Word or LibreOffice, modify the styles (not the sample text),
save, and pass it with `--reference-doc`. To add a callout style, create a new
paragraph style with the name you will use in `custom-style`, give it the
shading and border you want, and save.

Two habits keep this maintainable: change styles only, never the placeholder
content; and keep the reference document in version control next to the
Markdown it renders, since a template change silently restyles every document.

## Things Markdown cannot express

Do not try to fake these in Markdown; add them after conversion through the
OOXML editing path, or build the document with docx-js instead.

- Tracked changes and comments.
- Precise table column widths and cell merges.
- Headers, footers and page numbering.
- Multi-column sections and landscape pages.
- Content controls and form fields.

## Delivery gate

1. Reopen the result with python-docx.
2. Render the pages and check the parts Markdown cannot see: page breaks in the
   wrong place, a table wider than the page, an image scaled past the margin.
3. When a reference document was used, confirm the headings really picked up its
   styles rather than falling back to Normal.

<!-- sources: copilot-md-to-docx, ourarash-md-docx, docx-js-docs, pandoc-docs -->
