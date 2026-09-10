# Editing OOXML packages directly

Verified against: LibreOffice 26.2, python-docx 1.2, python-pptx 1.0, openpyxl 3.1

## Contents

- [When to unpack](#when-to-unpack)
- [Package anatomy](#package-anatomy)
- [The unpack, edit, repack loop](#the-unpack-edit-repack-loop)
- [Repack failure modes](#repack-failure-modes)
- [Namespaces](#namespaces)
- [Content types](#content-types)
- [Relationships](#relationships)
- [Adding a new part](#adding-a-new-part)
- [Editing XML safely](#editing-xml-safely)
- [Delivery gate](#delivery-gate)

## When to unpack

Reach for the XML only when the Python library cannot express the change:

- Tracked changes and comments in a Word document.
- Deleting or reordering slides, editing theme colours, layouts or masters.
- Content controls, custom XML parts, document-level settings.
- Repairing a package another tool damaged.

Everything else — text, styles, tables, images, formulas — is faster and safer
through python-docx, python-pptx or openpyxl.

## Package anatomy

An OOXML file is a zip archive. Same rules for all three formats:

```
[Content_Types].xml          declares a content type for every part
_rels/.rels                  package-level relationships (entry point)
word/document.xml            the Word body
word/_rels/document.xml.rels relationships owned by document.xml
word/styles.xml              style definitions
word/media/image1.png        binary parts
ppt/presentation.xml         the deck: slide id list, sizes
ppt/slides/slide1.xml        one part per slide
ppt/slideLayouts/, slideMasters/, theme/
xl/workbook.xml              sheet names and ids
xl/worksheets/sheet1.xml     one part per sheet
xl/sharedStrings.xml         deduplicated string table
```

Three invariants tie it together, and breaking any one produces "the file is
corrupt and cannot be opened":

1. Every part has a content type, by extension default or by explicit override.
2. Every part reachable from the document is referenced by a relationship.
3. Relationship ids used in the XML (`r:id="rId7"`) exist in that part's `.rels`.

## The unpack, edit, repack loop

```bash
uv run scripts/office_unpack.py report.docx work/
# edit work/word/document.xml
uv run scripts/office_pack.py work/ report-edited.docx
```

`office_unpack.py` records the original entry order in
`work/.opc-manifest.json`; `office_pack.py` replays that order, puts
`[Content_Types].xml` first and never packs the manifest itself. Keep the
original file: the diff between original and edited is the only cheap way to
review what a script changed.

## Repack failure modes

- **Directory-prefixed entries.** Zipping the *folder* rather than its contents
  produces entries named `work/[Content_Types].xml`. python-docx then reports
  `There is no item named '[Content_Types].xml' in the archive` and LibreOffice
  refuses the file outright. `[verified]` The paths inside the archive must be
  relative to the package root.
- **A missing part that a relationship still names.** Deleting
  `word/media/image1.png` without removing its relationship and the drawing
  that uses it makes Word offer to repair the document.
- **Rewritten XML declarations.** Some editors drop `standalone="yes"` or
  change the encoding label. Keep the first line byte-identical.
- **A BOM in front of the XML declaration.** Invisible in an editor, fatal on
  open.
- **Stored versus deflated entries.** Both are valid OOXML; entry *order* is
  not enforced by python-docx, LibreOffice or pandoc, but writing
  `[Content_Types].xml` first matches what Office produces and costs nothing.
  `[verified]`

## Namespaces

Every element name in these files is namespaced. Declarations live on the root
element, and a prefix that is not declared makes the part unparseable.

| Prefix | Namespace | Where |
|---|---|---|
| `w` | `.../wordprocessingml/2006/main` | Word body, styles |
| `a` | `.../drawingml/2006/main` | Shapes, text bodies, themes |
| `p` | `.../presentationml/2006/main` | Presentation, slides |
| `pic` | `.../drawingml/2006/picture` | Pictures |
| `r` | `.../officeDocument/2006/relationships` | `r:id`, `r:embed` |
| `wp` | `.../drawingml/2006/wordprocessingDrawing` | Inline and anchored drawings |
| `x` / none | `.../spreadsheetml/2006/main` | Workbook, sheets |

When adding an element that uses a prefix the part does not declare, add the
declaration to the root element in the same edit.

## Content types

```xml
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/comments.xml"
          ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
```

Defaults cover binary parts by extension; XML parts get an override. A media
file whose extension has no default and no override is the exact failure that
makes python-docx raise
`no content type for partname '/word/media/<hash>.undefined'`. `[verified]`

The overrides needed most often:

| Part | Content type |
|---|---|
| `word/comments.xml` | `…wordprocessingml.comments+xml` |
| `word/people.xml` | `…wordprocessingml.people+xml` |
| `ppt/slides/slideN.xml` | `…presentationml.slide+xml` |
| `ppt/notesSlides/notesSlideN.xml` | `…presentationml.notesSlide+xml` |
| `xl/worksheets/sheetN.xml` | `…spreadsheetml.worksheet+xml` |

(Prefix each with `application/vnd.openxmlformats-officedocument.`)

## Relationships

```xml
<Relationship Id="rId7"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
              Target="media/image1.png"/>
```

- `Target` is relative to the *owning part's* directory, so an image referenced
  from `word/document.xml` is `media/image1.png`, not `word/media/image1.png`.
- `Id` values only need to be unique within one `.rels` file. Allocate above the
  highest existing number rather than reusing a gap.
- External targets carry `TargetMode="External"` — hyperlinks, linked images.
- Deleting a part means deleting its relationship and every reference to that
  `r:id` in the XML.

## Adding a new part

Four edits, all required:

1. Write the part file, for example `word/comments.xml`.
2. Add an `Override` for it in `[Content_Types].xml`.
3. Add a `Relationship` in the owning part's `.rels`
   (`word/_rels/document.xml.rels`).
4. Reference it where it is used, by `r:id` or by the well-known part name.

Skip step 2 and Word reports the document as unreadable. Skip step 3 and the
part is inert — no error, no effect, which is worse to debug.

## Editing XML safely

- Parse rather than string-replace whenever the target is structural. A
  `<w:t>` boundary can fall in the middle of a visible phrase, so a plain text
  substitution silently matches nothing.
- Use `lxml` or `xml.etree.ElementTree` with the namespace map, and write back
  without pretty-printing. Added whitespace inside `<w:t>` becomes visible text.
- Preserve `xml:space="preserve"` on any run whose text has leading or trailing
  spaces; dropping it deletes those spaces.
- Change one thing, repack, verify. A batch of five XML edits that fails gives
  no information about which edit was wrong.
- Never reformat a part you did not otherwise change. It inflates the diff and
  hides the real edit.

## Delivery gate

1. Reopen with the matching library: python-docx, python-pptx or openpyxl. This
   is the check that catches missing content types and dangling relationships.
2. `soffice --headless --convert-to pdf` must succeed. A conversion that
   produces nothing means the package is malformed.
3. Render and look at the pages — the XML can be valid and the result still
   wrong.
4. For redlining, verify accept and reject separately rather than by looking at
   a render.

<!-- sources: ecma-376, python-openxml-docs, anthropic-docx, anthropic-pptx -->
