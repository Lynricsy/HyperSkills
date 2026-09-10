# Creating and editing presentations

Verified against: pptxgenjs 4.0.1, python-pptx 1.0, markitdown 0.1, LibreOffice 26.2

## Contents

- [Tool per task](#tool-per-task)
- [Failure modes](#failure-modes)
- [Deck skeleton](#deck-skeleton)
- [Text placement](#text-placement)
- [Tables](#tables)
- [Charts](#charts)
- [Images and speaker notes](#images-and-speaker-notes)
- [Filling an existing template](#filling-an-existing-template)
- [Structural edits before content edits](#structural-edits-before-content-edits)
- [Reading a deck](#reading-a-deck)
- [Delivery gate](#delivery-gate)

## Tool per task

| Task | Tool |
|---|---|
| Build a deck from scratch | pptxgenjs |
| Fill placeholders in a corporate template | python-pptx |
| Add, delete or reorder slides in an existing deck | python-pptx plus `p:sldIdLst` editing |
| Change theme colours, layouts, masters | Unpack and edit `ppt/theme`, `ppt/slideLayouts` |
| Extract text and notes | markitdown |

pptxgenjs cannot open an existing file. Anything that starts from a deck someone
else made belongs on the python-pptx or OOXML side.

## Failure modes

- **Colours silently become black.** pptxgenjs strips one leading `#` and then
  requires exactly six hex digits or a `pptx.SchemeColor` constant. An 8-digit
  value such as `"1F3864FF"`, a CSS name such as `"navy"`, or an `rgb()` string
  is replaced with `000000`; the only signal is a `console.warn` on stderr,
  which nothing surfaces when output is piped. Pass six hex digits.
  `[verified: pptxgenjs 4.0.1]`
- **pptxgenjs mutates the options object you pass in.** After
  `slide.addText("a", opts)`, `opts` has gained `color`, `objectName`, `line`,
  `lineSpacing` and `_bodyProp`. Reusing one options object across calls carries
  those derived values forward, so slide 4 inherits slide 1's state. Build a
  fresh object literal per call, or spread a frozen constant.
  `[verified: pptxgenjs 4.0.1]`
- **Text overflows its box in silence.** There is no autofit computation:
  `addText` places what it is given inside the box you specified and the render
  is the only place the overflow appears. Budget characters per box and check
  the images.
- **python-pptx cannot delete a slide.** `Presentation().slides` exposes
  `add_slide` and nothing else; removal means dropping the entry from
  `p:sldIdLst` and its relationship yourself. `[verified: python-pptx 1.0]`
- **A chart with mismatched axis configuration is dropped by PowerPoint.** A
  secondary-axis series with no matching value and category axis definition, or
  a data-label position that the chart type does not support, makes PowerPoint
  discard the chart on open while LibreOffice renders something. Add a secondary
  axis only together with its axis definitions, and render before delivering.
- **`addChart` rejects a top-level `fill` object.** Passing
  `fill: { color: "0B1B33" }` to `addChart` throws
  `TypeError: (colorStr || "").replace is not a function`, which says nothing
  about the real cause. A bare string (`fill: "0B1B33"`) works, and the two
  options that actually mean something are `plotArea: { fill: { color } }` and
  `chartArea: { fill: { color } }`. `[verified: pptxgenjs 4.0.1]`

## Deck skeleton

```js
import PptxGenJS from "pptxgenjs";

const NAVY = "1F3864";  // six hex digits, no leading #
const GOLD = "C9A227";
const pptx = new PptxGenJS();
// LAYOUT_WIDE is 13.33 x 7.5 in. The name for a widescreen deck is not
// LAYOUT_16x9: that constant is the 10 x 5.625 in default, and using it
// pushes every coordinate below off the right edge. `[verified: pptxgenjs 4.0.1]`
pptx.layout = "LAYOUT_WIDE";
pptx.defineSlideMaster({
  title: "BASE",
  background: { color: "FFFFFF" },
  objects: [{ line: { x: 0.5, y: 6.9, w: 12.33, h: 0, line: { color: NAVY, width: 1 } } }],
});

const title = pptx.addSlide({ masterName: "BASE" });
title.addText("Acme Robotics", { x: 0.8, y: 2.6, w: 11.7, h: 1.1, fontSize: 40, bold: true, color: NAVY, fontFace: "Arial" });
title.addText("Series A — September 2026", { x: 0.8, y: 3.7, w: 11.7, h: 0.6, fontSize: 20, color: "666666", fontFace: "Arial" });

await pptx.writeFile({ fileName: "deck.pptx" });
```

Coordinates and sizes are inches by default, measured against the layout you
set. The four layouts are `LAYOUT_16x9` (10 x 5.625, the default),
`LAYOUT_16x10` (10 x 6.25), `LAYOUT_4x3` (10 x 7.5) and `LAYOUT_WIDE`
(13.33 x 7.5). Numbers are absolute, so keep a small set of named x/y constants
rather than re-deriving margins per slide.

## Text placement

```js
slide.addText(
  [
    { text: "Problem", options: { bold: true, fontSize: 24, color: NAVY, breakLine: true } },
    { text: "Manual inspection misses 30% of defects.", options: { fontSize: 18, color: "333333" } },
  ],
  { x: 0.8, y: 1.2, w: 6, h: 2, valign: "top", fontFace: "Arial" }
);
```

Bullets come from `bullet: true` on a text object, or `bullet: { type: "number" }`
for numbering. `breakLine: true` ends a paragraph inside a single text frame,
which keeps related lines in one box that moves as a unit.

## Tables

```js
slide.addTable(
  [
    [{ text: "Metric", options: { bold: true, fill: { color: "DEE6F1" } } }, { text: "Value", options: { bold: true, fill: { color: "DEE6F1" } } }],
    ["ARR", "$1.2M"],
  ],
  { x: 0.8, y: 1.4, w: 11.7, colW: [6, 5.7], fontSize: 14, border: { pt: 0.5, color: "CCCCCC" } }
);
```

`colW` entries must sum to `w`, or the table drifts off the slide edge.

## Charts

```js
slide.addChart(
  pptx.ChartType.bar,
  [{ name: "Revenue", labels: ["Q1", "Q2", "Q3"], values: [820, 1010, 1200] }],
  { x: 0.8, y: 1.4, w: 7.5, h: 4.2, showValue: true, chartColors: [NAVY], catAxisLabelFontFace: "Arial" }
);
```

Keep to one series per axis unless the chart genuinely needs two, and check the
rendered image: an axis or legend that PowerPoint discards leaves a plot area
that looks fine in LibreOffice.

## Images and speaker notes

```js
slide.addImage({ path: "chart.png", x: 0.8, y: 1.4, w: 6, h: 3.4 });
slide.addNotes("Numbers from the Q3 close, finance-reviewed.");
```

Give both `w` and `h` computed from the real pixel dimensions; supplying one and
letting the other default distorts the image. `data:` URLs work in place of
`path` when the bytes are already in memory.

## Filling an existing template

1. Render the template and look at it, so the layouts are known rather than
   assumed.
2. List what is actually there:

```python
from pptx import Presentation
prs = Presentation("template.pptx")
for i, slide in enumerate(prs.slides):
    print(i, slide.slide_layout.name)
    for shape in slide.shapes:
        print("   ", shape.shape_id, shape.name, shape.shape_type,
              getattr(shape, "text", "")[:40])
```

3. Write into the placeholder's text frame, keeping its formatting:

```python
tf = slide.placeholders[1].text_frame
tf.paragraphs[0].runs[0].text = "New headline"
```

Assigning `tf.text = "New headline"` replaces all paragraphs and drops the run
properties with them, which is how a template-derived deck loses its fonts.
Replace run text, and only add paragraphs when more lines are needed.

4. After filling, check for shapes the content no longer explains — an orphaned
   caption, a leftover placeholder prompt, a chart still holding sample data.

## Structural edits before content edits

Adding, deleting or reordering slides rewrites `p:sldIdLst` and the presentation
relationships; every slide index and relationship id you cached before that
point is stale. Do all structural work first, save, reopen, then fill content.
Interleaving the two is the usual cause of "the text went onto the wrong slide".

To delete slide *n* with python-pptx:

```python
xml_slides = prs.slides._sldIdLst
slides = list(xml_slides)
prs.part.drop_rel(slides[n].rId)
xml_slides.remove(slides[n])
```

## Reading a deck

```bash
python -c "from markitdown import MarkItDown; print(MarkItDown().convert('deck.pptx').text_content)"
```

Output carries `<!-- Slide number: n -->` markers and a `### Notes:` section per
slide, which is what makes it usable for summarising a deck. Use python-pptx
instead when positions, sizes or theme colours matter.

## Delivery gate

1. Reopen with python-pptx.
2. Render every slide with `scripts/render_preview.py` and look at each image:
   text outside its box, a missing chart, a black block where a colour was
   meant, an unfilled placeholder.
3. For a template-derived deck, compare against a render of the original
   template to confirm the branding survived.

<!-- sources: pptxgenjs-docs, python-openxml-docs, anthropic-pptx -->
