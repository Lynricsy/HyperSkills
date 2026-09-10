---
name: office
description: "Creates, edits, reads and converts Word (.docx), PowerPoint (.pptx), Excel (.xlsx) and PDF files — reports, memos, letters, decks, slides, spreadsheets, financial models, forms, tracked changes and comments, markdown-to-docx, PDF merge, split, fill, OCR and table extraction — with a LibreOffice render-and-inspect quality gate that catches the layout and formula failures the libraries accept in silence. Use whenever the deliverable is an Office or PDF file, or when an existing one must be edited or extracted. Do not use for Google Docs, Sheets or Slides, for HTML or markdown output, or for data analysis that does not produce a spreadsheet."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.10"
  category: task
---

# office

Paths below are relative to this skill's directory.

## Scope

Local Office and PDF files: `.docx`, `.pptx`, `.xlsx`, `.pdf`, plus the
macro-enabled and template variants (`.docm`, `.pptm`, `.potx`, `.xlsm`).
Creating them, editing existing ones in place, extracting their content, and
converting between them and Markdown.

Not covered:

- Google Docs, Sheets and Slides, or any other hosted document API.
- HTML, Markdown or LaTeX as the deliverable. Markdown *input* that becomes a
  `.docx` is in scope.
- Analysis whose output is a chart, a number or a written answer rather than a
  file.
- Legacy binary formats (`.doc`, `.ppt`, `.xls`) beyond converting them to the
  modern equivalent with LibreOffice first.
- `.odt` / `.odp` / `.ods` as authored formats.

## Core rules

- Render the current version of the file and read the page images before
  calling any of this done. The libraries do not lay out text, so overflow,
  clipping and missing elements exist only in the render.
- Reopen every generated file with its matching Python library. LibreOffice
  converts packages that python-docx rejects, so conversion alone is not proof
  the file is well formed.
- Edit an existing file; never regenerate it from what you extracted.
  Extraction is lossy, so a rewrite silently drops styles, headers, fields and
  anything you did not read.
- Write formulas into spreadsheets, never computed values. A workbook of
  literals cannot be re-run when an assumption changes, which is the only
  reason the recipient wanted a spreadsheet.
- Never deliver a workbook until `scripts/xlsx_recalc.py` exits zero. openpyxl
  writes formula strings without evaluating them, so an unrecalculated workbook
  is entirely unverified.
- Write post-2007 Excel functions with the `_xlfn.` prefix, and prefer
  formulas that return one value per cell. Bare `XLOOKUP` recalculates to
  `#NAME?`, and a dynamic array truncates to its first element without raising
  an error.
- Pass pptxgenjs colours as six hex digits or a `pptx.SchemeColor`. Eight-digit
  hex and CSS names are replaced with black on a stderr warning nothing shows.
- Give every `ImageRun` an explicit `type`. Without it the media part is
  written with an `undefined` extension and no content type.
- Wrap every docx-js run in a `Paragraph`. A `TextRun` or `PageBreak` placed
  directly in a section is written to the file and then ignored by every
  renderer.
- Do structural work before content work: adding, deleting or reordering slides
  or sheets invalidates every index and relationship id cached before it.
- Choose fonts with metric-compatible substitutes — Arial, Times New Roman,
  Courier New — and never Aptos. A substituted font with different widths makes
  the visual check lie about line breaks.
- Verify tracked changes with `pandoc --track-changes=accept` and
  `--track-changes=reject`, not with a render, which shows both versions at
  once.
- Read a document that may carry revisions with `--track-changes=all`. The
  default silently returns the accepted text and hides that anything is
  pending.
- Never invent a figure to fill a table, chart or field. Leave the gap visible
  and say what is missing.

## Workflows

### Task routing

Pick the tool from the deliverable, then follow the matching workflow.

| Format | Create | Edit existing | Read |
|---|---|---|---|
| docx | docx-js (`docx` npm) | Unpack, edit `word/document.xml`, repack | `pandoc -f docx -t markdown` |
| pptx | pptxgenjs | python-pptx; `ppt/slides/slideN.xml` for structure | markitdown |
| xlsx | openpyxl | openpyxl | openpyxl, or pandas for bulk tables |
| pdf | reportlab | pypdf, qpdf | pdfplumber, `pdftotext -layout` |

Markdown to docx has its own path: `scripts/md_to_docx.mjs` by default, pandoc
with a reference document when a house template must be matched.

### create-document

- [ ] Confirm the format, the audience and whether a template must be matched.
- [ ] Read the reference for the format from the topic router before writing
      code, for the failure modes rather than the API.
- [ ] Pick fonts with metric substitutes and, for a deck, a named palette.
- [ ] Generate the file.
- [ ] Reopen it with the matching library.
- [ ] xlsx only: `uv run scripts/xlsx_recalc.py <file>` must exit zero.
- [ ] `uv run scripts/render_preview.py <file>` and read every image.
- [ ] Gate: **library reopen succeeds, recalc is clean where applicable, and
      the images show no overflow, no missing element and no placeholder text.**

### edit-existing

- [ ] Render the original first, so "what changed" has a baseline.
- [ ] Decide the layer: library API if it can express the change, OOXML unpack
      if it cannot (tracked changes, comments, slide order, themes).
- [ ] Keep the original file untouched and work on a copy.
- [ ] Structural edits first, then save, reopen, then content edits.
- [ ] For OOXML work: `uv run scripts/office_unpack.py in.docx work/`, edit,
      `uv run scripts/office_pack.py work/ out.docx`.
- [ ] Reopen with the matching library.
- [ ] Render the result and compare against the baseline render.
- [ ] Gate: **the intended change is visible, nothing else moved, and for
      redlining `pandoc --track-changes=reject` reproduces the original text
      while `--track-changes=accept` shows the edit.**

### read-extract

- [ ] Establish what is being asked for: text, tables, numbers, or a summary.
- [ ] Use the read tool from the routing table.
- [ ] Word documents: pass `--track-changes=all` when revisions may exist.
- [ ] PDFs: a page yielding no text is a scan — switch to OCR rather than
      concluding the file is broken.
- [ ] Spot-check extracted numbers against the rendered page before anything
      acts on them.
- [ ] Gate: **every figure reported has been checked against the rendered
      source, and OCR-derived text is labelled as such.**

### convert

- [ ] Markdown to docx: `node scripts/md_to_docx.mjs in.md out.docx`, or
      pandoc with `--reference-doc` when a template must be matched.
- [ ] Office to PDF: `soffice --headless --convert-to pdf <file>`.
- [ ] Office to Markdown: pandoc for docx, markitdown for pptx and xlsx.
- [ ] Legacy binary to modern: `soffice --headless --convert-to docx old.doc`,
      then treat the result as the source.
- [ ] Render the output and confirm the conversion did not reflow anything that
      matters — tables, page breaks, image placement.
- [ ] Gate: **the converted file opens in its library and its render matches
      the source's intent.**

## Topic router

| Topic | Read when | File |
|---|---|---|
| Word creation, styles, tables, images, TOC | Building or reading a `.docx` | `references/docx.md` |
| Tracked changes, comments, redlining | A reviewer must accept or reject edits | `references/docx-tracked-changes-comments.md` |
| Markdown to Word, reference templates | Converting Markdown, or matching a house template | `references/markdown-to-docx.md` |
| pptxgenjs, python-pptx, template filling | Building or editing a deck | `references/pptx.md` |
| Layouts, type scale, palette, avoid list | The deck has to look designed | `references/pptx-design.md` |
| openpyxl, merged cells, formats, charts, VBA | Any spreadsheet work | `references/xlsx.md` |
| `_xlfn.` prefixes, dynamic arrays, model conventions | Writing formulas, or a financial model | `references/xlsx-formulas.md` |
| reportlab, pypdf, merge, split, watermark, encrypt | Any PDF work | `references/pdf.md` |
| AcroForm fields, overlays, table extraction, OCR | Filling a form or extracting from a PDF | `references/pdf-forms-tables-ocr.md` |
| Package layout, content types, relationships, repack | The library cannot express the change | `references/ooxml-editing.md` |
| Render loop, what to look for, font substitution | Every delivery; before choosing fonts | `references/render-qa-fonts.md` |

## Output format

When the deliverable is a file, report it like this — path, what was verified,
and what a reader still has to decide:

```
report.docx — 4 pages
  verified: python-docx reopen; rendered 4/4 pages and reviewed
  assumptions: Q3 figures from the attached CSV; growth rate left at 12%
  open: the appendix table runs to the margin at A4; confirm Letter is intended
```

For a spreadsheet, include the recalculation result:

```
model.xlsx — Model sheet, 12 formula cells
  verified: xlsx_recalc.py clean (0 errors); openpyxl reopen keeps formulas
  assumptions: B2 growth 12%, B3 COGS 40% — both editable, everything derives
```

When a gate fails, say which one and what the failure was, rather than
delivering with a caveat:

```
deck.pptx — NOT delivered
  gate: visual review, slide 4
  failure: the traction chart title overflows its box at 24 pt
```

## Environment

System packages:

```bash
# Debian / Ubuntu
sudo apt-get install -y libreoffice poppler-utils pandoc qpdf tesseract-ocr \
  fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea
# macOS
brew install --cask libreoffice && brew install poppler pandoc qpdf tesseract
```

Python (each bundled script declares its own PEP 723 dependencies, so
`uv run scripts/<name>.py` needs no environment setup):

```bash
uv pip install openpyxl pandas "markitdown[pptx,docx,xlsx,pdf]" Pillow lxml \
  python-docx python-pptx pypdf pdfplumber reportlab pytesseract pdf2image
```

Node, for document generation:

```bash
cd scripts && npm install     # docx, marked
npm install pptxgenjs         # in the working directory for a deck
```

Bundled scripts:

| Script | Mode | Purpose |
|---|---|---|
| `scripts/render_preview.py` | Run | Any Office or PDF file to page PNGs for review |
| `scripts/xlsx_recalc.py` | Run | Recalculate with LibreOffice, scan for error cells, non-zero exit on any |
| `scripts/office_unpack.py` | Run | Unpack an OOXML package, recording entry order |
| `scripts/office_pack.py` | Run | Repack it with `[Content_Types].xml` first and no directory prefix |
| `scripts/md_to_docx.mjs` | Run | Markdown to Word with no native dependency |
| `scripts/pdf_form_fields.py` | Run | List AcroForm fields with checkbox states; fill them with validation |

Fonts are a correctness dependency, not cosmetics: check
`fc-match <font>` returns the metric-compatible substitute before trusting a
render, as described in `references/render-qa-fonts.md`.
