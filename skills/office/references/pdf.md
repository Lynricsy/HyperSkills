# PDF reading, writing and manipulation

Verified against: pypdf 6.18, pdfplumber 0.11, reportlab 4.x, qpdf 12.4, poppler 26.07

## Contents

- [Tool per task](#tool-per-task)
- [Failure modes](#failure-modes)
- [Creating a PDF with reportlab](#creating-a-pdf-with-reportlab)
- [Merge, split, rotate, reorder](#merge-split-rotate-reorder)
- [Text extraction](#text-extraction)
- [Metadata](#metadata)
- [Watermarks and overlays](#watermarks-and-overlays)
- [Encryption](#encryption)
- [Images](#images)
- [Command-line recipes](#command-line-recipes)
- [Delivery gate](#delivery-gate)

## Tool per task

| Task | Tool |
|---|---|
| Generate a report, invoice, letter | reportlab (`platypus` for flowing content) |
| Merge, split, rotate, encrypt, stamp | pypdf |
| Extract text with position, extract tables | pdfplumber |
| Fast bulk text extraction | `pdftotext -layout` |
| Repair, linearise, decrypt, split by page range | qpdf |
| Page images for visual review | `pdftoppm` |
| Extract embedded images | `pdfimages` |
| Scanned pages | OCR path |

Do not layer libraries where one suffices. reportlab writes, pypdf rearranges,
pdfplumber reads; mixing writers on one file is how content ends up duplicated.

## Failure modes

- **Text extraction returning nothing means the page is an image.** Zero or
  near-zero characters from a page is the signature of a scan, not a broken
  extractor. Check before assuming the PDF is malformed, and switch to OCR.
- **Extracted text order is not reading order.** Extraction follows the content
  stream, so a two-column page can interleave columns and a table can arrive
  cell-by-cell out of sequence. Use positional extraction when order matters.
- **Merging PDFs that both contain forms collides field names.** Appending the
  same form twice gives two sets of widgets sharing one set of field names, so
  filling one fills both. Four pages, six widgets, three distinct names.
  `[verified: pypdf 6.18]` Rename fields before merging, or flatten first.
- **Page indices are zero-based in pypdf and one-based everywhere in the UI.**
  `reader.pages[0]` is what a user calls page 1. Off-by-one here produces a
  plausible-looking wrong document.
- **`reportlab` measures from the bottom left.** `drawString(72, 720)` on a
  Letter page is one inch from the left and one inch from the top, because 792
  minus 720 is 72. Treating y as a distance from the top silently mirrors the
  layout.

## Creating a PDF with reportlab

For anything with flowing text, use `platypus` rather than absolute
`drawString` placement — it handles pagination, keeps tables together and wraps
paragraphs:

```python
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

styles = getSampleStyleSheet()
doc = SimpleDocTemplate("report.pdf", pagesize=LETTER,
                        leftMargin=inch, rightMargin=inch,
                        topMargin=inch, bottomMargin=inch)
story = [
    Paragraph("Q3 Vendor Report", styles["Title"]),
    Spacer(1, 12),
    Paragraph("Revenue grew 12% quarter over quarter.", styles["BodyText"]),
    Spacer(1, 12),
    Table(
        [["Metric", "Value"], ["Revenue", "1,200,000"]],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DEE6F1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]),
    ),
]
doc.build(story)
```

Notes that save a rebuild:

- Paragraph text is mini-HTML: `<b>`, `<i>`, `<font color="...">`, `<super>`,
  `<sub>`, `<br/>`. A literal `&`, `<` or `>` must be escaped, or the paragraph
  silently loses text from the bad tag onward.
- Use plain ASCII hyphens. A non-breaking hyphen (U+2011) and other Unicode
  dashes are missing from the built-in Type 1 fonts and render as a black box.
- Register a TTF before using a non-standard font
  (`pdfmetrics.registerFont(TTFont("Inter", "Inter-Regular.ttf"))`); an
  unregistered name falls back to Helvetica.
- Page numbers come from an `onPage` callback that draws on the canvas.

## Merge, split, rotate, reorder

```python
from pypdf import PdfReader, PdfWriter

# merge
w = PdfWriter()
for path in ["cover.pdf", "body.pdf"]:
    w.append(path)
w.write("merged.pdf")

# split out pages 3-5 (as the user counts them)
r = PdfReader("body.pdf")
w = PdfWriter()
for page in r.pages[2:5]:
    w.add_page(page)
w.write("extract.pdf")

# rotate, reorder
page = r.pages[0]
page.rotate(90)                     # clockwise, must be a multiple of 90
w = PdfWriter()
for i in [2, 0, 1]:
    w.add_page(r.pages[i])
w.write("reordered.pdf")
```

`append` accepts a page range: `w.append("body.pdf", pages=(0, 5))`.
`PdfWriter(clone_from=path)` starts from an existing document and keeps its
catalog, which is what you want when modifying rather than assembling.

## Text extraction

```python
import pdfplumber

with pdfplumber.open("report.pdf") as pdf:
    page = pdf.pages[0]
    print(page.extract_text(layout=True))          # preserves column geometry
    for word in page.extract_words():              # x0, x1, top, bottom per word
        ...
    print(page.extract_tables())
```

`layout=True` reconstructs the visual arrangement using character positions and
is the right default for anything with columns. For bulk extraction where
fidelity does not matter, `pdftotext -layout in.pdf out.txt` is an order of
magnitude faster.

pypdf's `page.extract_text()` is adequate for a quick look and weaker on
layout; prefer pdfplumber when the answer depends on position.

## Metadata

```python
r = PdfReader("report.pdf")
print(r.metadata.title, r.metadata.author, len(r.pages))

w = PdfWriter(clone_from="report.pdf")
w.add_metadata({"/Title": "Q3 Vendor Report", "/Author": "Finance"})
w.write("report.pdf")
```

Metadata keys are name objects and need the leading slash. Deliverables that
leave `/Producer` as the default library string look unfinished.

## Watermarks and overlays

```python
stamp = PdfReader("watermark.pdf").pages[0]
w = PdfWriter(clone_from="report.pdf")
for page in w.pages:
    page.merge_page(stamp)          # stamp on top
    # page.merge_transformed_page(stamp, Transformation().translate(tx=0, ty=0))
w.write("stamped.pdf")
```

`merge_page` draws the stamp over existing content; to put it underneath, merge
in the other direction — start from the stamp and merge the page onto it. Sizes
are not reconciled automatically: a Letter stamp on an A4 page lands off-centre,
so generate the stamp at the target page size.

## Encryption

```python
w = PdfWriter(clone_from="report.pdf")
w.encrypt(user_password="", owner_password="secret", algorithm="AES-256")
w.write("protected.pdf")
```

An empty user password with a set owner password gives "opens freely, editing
restricted". Encryption is advisory: every reader can ignore permission flags.
Never treat it as access control for confidential content.

Reading an encrypted file: `reader.decrypt(password)` before touching
`reader.pages`, or `qpdf --password=pw --decrypt in.pdf out.pdf`.

## Images

```bash
pdfimages -list report.pdf              # inventory with resolution and colour space
pdfimages -png -f 2 -l 2 report.pdf out # extract page 2's images as PNG
```

pdfplumber exposes `page.images` with bounding boxes when the position of an
image matters more than its bytes.

## Command-line recipes

```bash
# repair a file other tools choke on
qpdf --replace-input broken.pdf

# split into single pages
qpdf --split-pages=1 in.pdf page.pdf        # -> page-01.pdf, page-02.pdf, ...

# page subset
qpdf in.pdf --pages . 3-5 -- out.pdf

# linearise for web delivery
qpdf --linearize in.pdf out.pdf

# page count and geometry
pdfinfo report.pdf

# render for review
pdftoppm -r 100 -png report.pdf page
```

## Delivery gate

1. Reopen with pypdf and check `len(reader.pages)` matches the intent.
2. Render every page with `scripts/render_preview.py` and read the images:
   clipped text, overlapping elements, a black rectangle where a glyph is
   missing, a table split badly across a page break.
3. For a generated document, extract the text once and confirm no placeholder
   or template token survived.

<!-- sources: openai-pdf, pypdf-docs, pdfplumber-docs, reportlab-docs, anthropic-pdf -->
