# Render-and-inspect QA, and the font problem

Verified against: LibreOffice 26.2.5.2, poppler 26.07, fontconfig on Linux

## Contents

- [Why rendering is the gate](#why-rendering-is-the-gate)
- [The three-layer gate](#the-three-layer-gate)
- [Running the render](#running-the-render)
- [What to look for in the images](#what-to-look-for-in-the-images)
- [Fonts decide whether the render tells the truth](#fonts-decide-whether-the-render-tells-the-truth)
- [Checking the substitution on this machine](#checking-the-substitution-on-this-machine)
- [Installing metric substitutes](#installing-metric-substitutes)
- [Known render differences that are not defects](#known-render-differences-that-are-not-defects)
- [LibreOffice operational notes](#libreoffice-operational-notes)

## Why rendering is the gate

A generated document is a claim about what a reader will see, and none of the
libraries can check that claim. openpyxl does not evaluate formulas. docx-js
does not lay out text. pptxgenjs does not measure whether a string fits its box.
The failures that reach a recipient are overwhelmingly layout failures, and the
only way to catch them is to look at the pages.

Nothing here is delivered before the current version of the file has been
rendered and the images read.

## The three-layer gate

Each layer catches a different class of defect, and they are cheap enough to run
all three every time.

| Layer | Command | Catches |
|---|---|---|
| Library round trip | `docx.Document(p)`, `Presentation(p)`, `load_workbook(p)`, `PdfReader(p)` | Missing content types, dangling relationships, a package that is structurally broken |
| Conversion | `soffice --headless --convert-to pdf` | Malformed XML, unresolvable references, a file no consumer can open |
| Visual | `pdftoppm -r 100 -png` then read the images | Overflow, clipping, overlap, missing element, wrong colour, placeholder text |

They are ordered by specificity, not by strength. A library round trip catches
things LibreOffice happily converts anyway: an image part written with an
`undefined` extension converts to a perfectly good PDF and still fails
`docx.Document`. `[verified]` Conversely, LibreOffice rejects packages python
libraries accept. Neither substitutes for the other.

Format-specific additions:

- **xlsx:** the recalculation scan, `scripts/xlsx_recalc.py`. Non-zero exit
  blocks delivery.
- **Tracked changes:** `pandoc --track-changes=accept` and `--track-changes=reject`
  must each read correctly. A render shows both versions superimposed and looks
  broken when the markup is right. `[verified]`
- **PDF forms:** re-read the fields and confirm each holds the intended value.

## Running the render

```bash
uv run scripts/render_preview.py report.docx            # all pages at 100 dpi
uv run scripts/render_preview.py deck.pptx --dpi 150    # finer, for type review
uv run scripts/render_preview.py long.pdf --first 1 --last 3
uv run scripts/render_preview.py model.xlsx --outdir qa/
```

It prints one PNG path per line, in page order. Read them; the point of the
gate is the reading, not the rendering.

100 dpi puts a Letter page at roughly 850 x 1100 px, which is legible for layout
review and small enough to page through a long document. Raise to 150 when
judging type sizes or thin rules.

## What to look for in the images

Layout, in rough order of how often it goes wrong:

- Text that runs past its box, its column, or the page margin.
- A table wider than the text area, or split badly across a page break.
- Elements overlapping each other.
- An element that is simply absent: a chart, an image, a heading.
- Blank pages, or a page break in the wrong place.
- A black or grey rectangle where a glyph should be — a missing font.

Content:

- Placeholder text: `TODO`, `TBD`, `Lorem ipsum`, `Your text here`, `{{name}}`.
- Numbers unformatted (`1200000`) or with the wrong unit.
- A colour that is not from the chosen palette — usually a value the library
  rejected and replaced with black.
- Headers, footers and page numbers present and correct on every page.
- For a template-derived file, branding still intact.

## Fonts decide whether the render tells the truth

LibreOffice cannot use a font it does not have; it substitutes. If the
substitute has different glyph widths, every line break in the render is wrong,
which means overflow checks report problems that will not occur and miss ones
that will.

Metric-compatible substitutes have identical advance widths, so the render is
trustworthy:

| Requested | Metric substitute | Ships with |
|---|---|---|
| Arial | Liberation Sans | Almost every Linux distribution |
| Times New Roman | Liberation Serif | Almost every Linux distribution |
| Courier New | Liberation Mono | Almost every Linux distribution |
| Calibri | Carlito | Needs installing |
| Cambria | Caladea | Needs installing |

Fonts with no metric substitute — Georgia, Verdana, Trebuchet MS, Impact,
Garamond, Palatino, Consolas, Calibri Light — fall back to something of a
different width, so the render approximates the layout rather than reproducing
it.

**Aptos** is the worst case: it is Office's current default, has no metric
substitute, and is absent from older Office installations as well as from Linux.
A document specifying Aptos renders differently for the author, for the
verification step, and for a recipient on an older Office. Choose a different
font.

Default choice for anything that must be verified on Linux: **Arial** for sans,
**Times New Roman** for serif, **Courier New** for monospace. Use Calibri and
Cambria when the house style demands it *and* Carlito and Caladea are installed.

## Checking the substitution on this machine

Never assume; the answer differs per machine.

```bash
fc-match Arial              # LiberationSans-Regular.ttf "Liberation Sans" — good
fc-match Calibri            # Carlito-Regular.ttf — good
                            # NotoSans-Regular.ttf — NOT metric compatible
fc-match Aptos              # always a non-metric fallback
fc-list : family | tr ',' '\n' | sort -u | grep -iE 'liberation|carlito|caladea'
```

On the machine this reference was verified against, `fc-match Arial`,
`Times New Roman` and `Courier New` resolve to the Liberation family, while
`Calibri` and `Cambria` resolve to Noto because Carlito and Caladea are not
installed — so a Calibri document's line breaks in the render are approximate.
`[verified]`

When `fc-match` returns a non-metric substitute, either install the substitute
or state in the handover that the visual check was approximate for that font.

## Installing metric substitutes

```bash
# Debian / Ubuntu
sudo apt-get install -y fonts-crosextra-carlito fonts-crosextra-caladea fonts-liberation
# real Microsoft fonts, EULA prompt
sudo apt-get install -y ttf-mscorefonts-installer

# Arch
sudo pacman -S ttf-carlito ttf-caladea ttf-liberation

# macOS
brew install --cask font-carlito font-caladea
```

After installing, `fc-cache -f` and re-check with `fc-match`.

## Known render differences that are not defects

Do not chase these:

- **An empty table of contents.** A Word TOC is a field; LibreOffice leaves it
  unpopulated on conversion. Word fills it when the reader updates fields.
- **Both old and new text visible in a redlined document.** That is what
  displaying revisions looks like.
- **Slightly different hyphenation and justification.** Different layout
  engines, same content.
- **A missing form-field highlight.** Interactive widget chrome is a viewer
  behaviour, not page content.
- **Chart fonts falling back.** Chart text often specifies a theme font the
  substitute list does not cover; check position and labels, not the typeface.

## LibreOffice operational notes

- A second `soffice` process cannot use the profile the first one holds; the
  headless convert then exits successfully having produced nothing. Both bundled
  scripts pass a private
  `-env:UserInstallation=file:///tmp/...` profile per run, which removes the
  whole class of "it worked yesterday" failures.
- Conversion writes to `--outdir` using the input's stem, so two inputs with the
  same stem in one directory overwrite each other.
- `--convert-to pdf` on a `.xlsx` prints the sheet as configured, which for a
  wide sheet means many narrow pages. Set the print area or accept that the
  render is checking content rather than pagination.
- No output plus exit code 0 means the input is malformed. Treat it as a
  failure, not as an empty document.

<!-- sources: libreoffice-docs, openai-pdf, anthropic-docx, anthropic-xlsx -->
