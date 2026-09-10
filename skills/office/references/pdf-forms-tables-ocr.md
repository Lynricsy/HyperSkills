# PDF forms, tables and OCR

Verified against: pypdf 6.18, pdfplumber 0.11, tesseract 5.5, poppler 26.07

## Contents

- [Forms: detect before filling](#forms-detect-before-filling)
- [Filling text fields](#filling-text-fields)
- [Checkboxes and radio groups](#checkboxes-and-radio-groups)
- [Flattening](#flattening)
- [When there are no form fields](#when-there-are-no-form-fields)
- [Table extraction](#table-extraction)
- [OCR](#ocr)
- [Delivery gate](#delivery-gate)

## Forms: detect before filling

"Fill in this PDF" splits into two completely different jobs depending on
whether the file has an AcroForm. Find out first:

```bash
uv run scripts/pdf_form_fields.py list intake.pdf
```

```
intake.pdf: 3 field(s), 2 page(s)
  vendor_name  [text]  value=''
  amount  [text]  value=''
  approved  [button]  value='/Off'  states=['/Off', '/Yes']
```

No output rows means no AcroForm, and the overlay path below is the only option.
The equivalent in code is `PdfReader(path).get_fields()`, which returns `None`
or an empty dict for a flat document.

Field types come from `/FT`: `/Tx` text, `/Btn` button (checkbox, radio, push),
`/Ch` choice (dropdown, list), `/Sig` signature.

## Filling text fields

```bash
uv run scripts/pdf_form_fields.py fill intake.pdf filled.pdf \
  --set vendor_name="Acme Ltd" --set amount=42000
```

The script rejects a field name that does not exist and prints the available
names, because pypdf's own behaviour is to accept the unknown key and write
nothing. It also re-reads the output and fails if a value did not stick.

In code:

```python
from pypdf import PdfReader, PdfWriter

writer = PdfWriter(clone_from="intake.pdf")
writer.set_need_appearances_writer(True)
for page in writer.pages:
    names = {a.get_object().get("/T") for a in (page.get("/Annots") or [])}
    subset = {k: v for k, v in updates.items() if k in names}
    if subset:
        writer.update_page_form_field_values(page, subset)
writer.write("filled.pdf")
```

Two details matter. `update_page_form_field_values` only touches widgets on the
page it is given, so passing every page a full update dict logs a warning per
page that owns none of the fields. And `set_need_appearances_writer(True)` asks
the viewer to rebuild widget appearances; pypdf also writes its own appearance
streams, so the value renders either way, but setting it costs nothing and
covers viewers that trust only their own rendering.

## Checkboxes and radio groups

A checkbox value is not a boolean and not a plain string: it is the widget's
appearance-state name **including the leading slash**. Read the states from
`/AP /N`, then use one of them.

```python
annot.get("/AP").get("/N").keys()   # dict_keys(['/Off', '/Yes'])
```

`True`, `"Yes"`, `"1"` and `"/1"` all leave the box at `/Off` with no error
raised. `"/Yes"` sets both `/V` and the widget's `/AS`. `[verified: pypdf 6.18]`

The on-state name is per widget: `/Yes`, `/On`, `/1` and `/Choice1` are all
common. Radio groups work the same way — one field, one on-state per button,
and setting the field to a state selects the matching button.

## Flattening

A filled form still is a form: the recipient can edit it. To hand over
something fixed, render the filled document and rebuild it from the page
images, or stamp the values as page content instead of field values. pypdf has
no flatten operation, so the two honest options are:

```bash
# raster flatten: correct, loses selectable text
uv run scripts/render_preview.py filled.pdf --dpi 200
# then reassemble the PNGs into a PDF with reportlab

# or draw the values as content from the start (overlay path below)
```

State which one was done: "flattened to images at 200 dpi" and "values drawn as
page content" have different consequences for search and accessibility.

## When there are no form fields

Draw the values on a transparent overlay and merge it onto the page. The whole
difficulty is finding the coordinates, and guessing them wastes more time than
measuring.

1. Locate the anchors by text position:

```python
import pdfplumber

with pdfplumber.open("flat.pdf") as pdf:
    page = pdf.pages[0]
    print(page.width, page.height)
    for word in page.extract_words():
        if "Vendor" in word["text"]:
            print(word)   # {'text': 'Vendor', 'x0': 72.0, 'top': 62.48, 'height': 12.0, ...}
```

2. Convert to reportlab coordinates. pdfplumber's `top` is measured from the
   top of the page; reportlab's `y` from the bottom. So
   `y = page.height - top - font_size`.

3. Draw and merge:

```python
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

c = canvas.Canvas("overlay.pdf", pagesize=(page.width, page.height))
c.setFont("Helvetica", 10)
c.drawString(160, page.height - 62.48 - 10, "Acme Ltd")
c.save()

writer = PdfWriter(clone_from="flat.pdf")
writer.pages[0].merge_page(PdfReader("overlay.pdf").pages[0])
writer.write("filled.pdf")
```

4. Render and look. Overlay work is never finished on the first pass: text
   lands on top of a rule, or one line too high. Iterate against the images.

Build the overlay at the exact page size from `page.width` and `page.height`.
A Letter overlay on an A4 page shifts every value.

## Table extraction

```python
with pdfplumber.open("statement.pdf") as pdf:
    page = pdf.pages[0]
    for table in page.extract_tables():
        for row in table:
            print(row)
```

The default strategy detects ruling lines. When a table has no borders, tell
pdfplumber to infer columns from text alignment instead:

```python
page.extract_tables({
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    # tighten when adjacent columns merge; loosen when one column splits
    "text_x_tolerance": 2,
})
```

Or fix the columns explicitly, which is the reliable option for a repeating
report:

```python
page.extract_table({"vertical_strategy": "explicit",
                    "explicit_vertical_lines": [50, 200, 320, 480],
                    "horizontal_strategy": "text"})
```

Expected trouble, and the fix:

| Symptom | Cause | Fix |
|---|---|---|
| Two columns merged into one cell | No ruling line, words close together | Lower `text_x_tolerance`, or use explicit lines |
| One column split in two | Wide intra-cell spacing | Raise `text_x_tolerance` |
| Header repeated mid-table | Table spans pages | Extract per page, drop repeats, concatenate |
| Rows shifted by one | Multi-line cells | Crop the region and extract in slices |
| Empty result | Page is a scan | OCR path |

Always spot-check extracted numbers against the rendered page. A silently
mis-parsed table is worse than a failed extraction.

## OCR

Confirm the page is really a scan before reaching for OCR, since OCR on a text
PDF is slower and less accurate than extraction:

```python
with pdfplumber.open("scan.pdf") as pdf:
    if len((pdf.pages[0].extract_text() or "").strip()) < 20:
        ...  # image page
```

Then rasterise and recognise:

```python
from pdf2image import convert_from_path
import pytesseract

for i, image in enumerate(convert_from_path("scan.pdf", dpi=300), start=1):
    text = pytesseract.image_to_string(image, lang="eng")
    print(f"--- page {i} ---\n{text}")
```

What actually moves accuracy:

- **300 dpi.** Below 200 the error rate climbs sharply; above 400 costs time for
  nothing.
- **The right language pack.** `lang="eng+deu"` for mixed documents; a missing
  pack fails loudly, which is preferable to quiet garbage.
- **`--psm` for unusual layouts.** `image_to_string(image, config="--psm 6")`
  treats the page as a single uniform block, which helps on tables and columns
  that the default segmentation shreds.
- **Deskew and threshold** a photographed page before recognition; a straight,
  high-contrast image beats every parameter tweak.
- **Never present OCR output as verbatim.** Say it came from OCR and flag
  low-confidence figures. `image_to_data` returns per-word confidence when the
  numbers matter.

Searchable PDF in one step, when the deliverable is the document rather than the
text: `ocrmypdf scan.pdf searchable.pdf` (separate package, wraps tesseract).

## Delivery gate

1. Forms: re-read the output with the list command and confirm every field
   holds the intended value — text values as text, checkboxes as their on-state.
2. Overlays and flattened output: render and look at the pages.
3. Extraction: cross-check a sample of the extracted numbers against the
   rendered page before anyone acts on them.

<!-- sources: pypdf-docs, pdfplumber-docs, reportlab-docs, openai-pdf, anthropic-pdf -->
