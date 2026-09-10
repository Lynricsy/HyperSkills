# Creating Word documents with docx-js

Verified against: docx 9.7.1, python-docx 1.2, LibreOffice 26.2, pandoc 3.10

## Contents

- [Why docx-js for new documents](#why-docx-js-for-new-documents)
- [Failure modes that produce a file nobody notices is broken](#failure-modes-that-produce-a-file-nobody-notices-is-broken)
- [Document skeleton](#document-skeleton)
- [Headings and styles](#headings-and-styles)
- [Tables](#tables)
- [Images](#images)
- [Page breaks, sections, headers and footers](#page-breaks-sections-headers-and-footers)
- [Table of contents](#table-of-contents)
- [Reading a document](#reading-a-document)
- [Delivery gate](#delivery-gate)

## Why docx-js for new documents

For a document created from scratch, build the object tree with the `docx` npm
package and write it once. python-docx is the wrong tool here: it works by
mutating a template package, so anything the default template lacks (a heading
style, a numbering definition, a section with different margins) has to be
grafted in as raw XML anyway.

Use python-docx for the opposite job: opening a document somebody else made and
reading or lightly adjusting it. Editing structure in an existing document goes
through the OOXML path instead.

## Failure modes that produce a file nobody notices is broken

Every item below packs without an exception and opens without a warning. That is
what makes them expensive.

- **A run outside a paragraph is discarded.** `docx` will happily accept a
  `TextRun` or `PageBreak` as a direct child of `sections[].children`, emit it
  as a bare `<w:r>` under `<w:body>`, and every renderer then drops it.
  A `TextRun("bare run")` placed directly in a section renders as nothing at
  all; a `PageBreak` placed directly in a section produces a one-page document
  where you expected two. Wrap both in a `Paragraph`. `[verified]`
- **`ImageRun` without `type` writes an unreadable package.** Omitting `type`
  writes the media part as `word/media/<hash>.undefined` with no matching
  content-type entry. LibreOffice still converts the file, so a render-only
  check passes, while python-docx fails with
  `no content type for partname '/word/media/<hash>.undefined'`. Always pass
  `type: "png" | "jpg" | "gif" | "bmp" | "svg"` and make it match the bytes.
  `[verified]`
- **A style name that does not exist is silently ignored.** Referring to
  `style: "Quote"` when no such style is defined leaves the paragraph with
  default formatting and no error. Define custom styles in the `Document`
  constructor, or use the built-in `heading:` property.
- **Table cell widths are ignored unless the table has a width.** A `Table`
  without `width` collapses to content width in Word regardless of per-cell
  widths. Set `width: { size: 100, type: WidthType.PERCENTAGE }` on the table.

## Document skeleton

```js
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from "docx";
import fs from "node:fs";

const doc = new Document({
  creator: "Reporting",
  title: "Q3 Vendor Report",
  // Arial, Times New Roman and Courier New have metric-compatible substitutes
  // on Linux, so a LibreOffice render matches Word's line breaks.
  styles: { default: { document: { run: { font: "Arial", size: 22 } } } },
  sections: [
    {
      properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun({ text: "Q3 Vendor Report", color: "1F3864" })],
        }),
        new Paragraph({ children: [new TextRun("Revenue grew 12% quarter over quarter.")] }),
      ],
    },
  ],
});

fs.writeFileSync("report.docx", await Packer.toBuffer(doc));
```

Units are the ones Word uses, and they differ per property: `size` is
half-points (22 = 11 pt), margins and indents are twentieths of a point
(1440 = 1 inch), image transformations are points.

## Headings and styles

Prefer `heading: HeadingLevel.HEADING_n` over hand-rolled bold-and-bigger runs:
it populates the outline that a table of contents, the navigation pane and
accessibility tools read. Colour a heading by colouring its runs, not by
inventing a style.

For a repeated look, declare it once:

```js
styles: {
  paragraphStyles: [
    {
      id: "Callout",
      name: "Callout",
      basedOn: "Normal",
      run: { italics: true, color: "444444" },
      paragraph: { indent: { left: 360 }, spacing: { after: 120 } },
    },
  ],
}
```

Then `new Paragraph({ style: "Callout", children: [...] })`. The `id` is what
`style:` matches; a typo degrades to Normal without complaint.

## Tables

```js
new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  rows: [
    new TableRow({
      tableHeader: true, // repeats the row when the table breaks across pages
      children: ["Metric", "Value"].map(
        (t) =>
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: "DEE6F1" },
            children: [new Paragraph({ children: [new TextRun({ text: t, bold: true })] })],
          })
      ),
    }),
    new TableRow({
      children: ["Revenue", "1,200,000"].map((t) => new TableCell({ children: [new Paragraph(t)] })),
    }),
  ],
});
```

A `TableCell` takes block content only — always a `Paragraph`, never a bare
`TextRun`. Merge cells with `columnSpan` / `rowSpan` on the cell; for a vertical
merge the continuation cells must still exist in their rows.

## Images

```js
new Paragraph({
  children: [
    new ImageRun({
      type: "png",
      data: fs.readFileSync("chart.png"),
      altText: { name: "chart", description: "Revenue by quarter", title: "chart" },
      transformation: { width: 468, height: 260 }, // points; 468 pt = 6.5 in
    }),
  ],
});
```

Compute the height from the real pixel dimensions instead of guessing, or the
image is stretched. A Letter page with 1-inch margins gives 468 pt of usable
width.

## Page breaks, sections, headers and footers

- Page break: `new Paragraph({ children: [new PageBreak()] })`.
- A change of page size, orientation or margins needs a new entry in
  `sections`, not a break.
- Headers and footers are per section: `{ headers: { default: new Header({...}) },
  footers: { default: new Footer({...}) }, children: [...] }`.
- Page numbers come from field children:
  `new Paragraph({ children: [new TextRun({ children: [PageNumber.CURRENT] })] })`.

## Table of contents

`new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-3" })`
writes a TOC *field*. Word fills it when the user opens the document and agrees
to update fields; LibreOffice leaves it empty on conversion, so a rendered
preview shows a blank page there. That is expected, not a defect.

When the document must show a populated contents list without user interaction,
emit the entries yourself as ordinary paragraphs built from the headings you
just wrote.

## Reading a document

- Text and structure: `pandoc -f docx -t markdown report.docx`.
- Text with revision marks preserved: add `--track-changes=all`. The default is
  `accept`, which silently returns the post-edit text and hides that the
  document even had pending changes. `[verified]`
- Programmatic access to paragraphs, tables and styles: python-docx.

## Delivery gate

1. Reopen with python-docx (`docx.Document(path)`) — this catches the broken
   content-type and relationship cases LibreOffice tolerates.
2. Render and look at the pages, using `scripts/render_preview.py`.
3. For a document with revisions, also check accept and reject both read
   correctly, since a rendered page shows both versions at once.

<!-- sources: docx-js-docs, python-openxml-docs, pandoc-docs, anthropic-docx -->
