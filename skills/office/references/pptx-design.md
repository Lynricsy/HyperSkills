# Slide design that survives a projector

## Contents

- [Decide before drawing](#decide-before-drawing)
- [Layouts that carry a deck](#layouts-that-carry-a-deck)
- [Type scale](#type-scale)
- [Colour](#colour)
- [Spacing and alignment](#spacing-and-alignment)
- [Data on slides](#data-on-slides)
- [Avoid list](#avoid-list)
- [Self-review](#self-review)

## Decide before drawing

Answer these first; each one changes the layout, and discovering the answer
after slide 12 means rebuilding.

- Presented live or read on a laptop? Live means fewer words and bigger type.
- Total slide count and the one sentence each slide has to land.
- Where the numbers come from. Never invent a figure to fill a chart; leave the
  placeholder visible and say what is missing.
- Whether a brand template exists. If it does, fill it rather than inventing a
  look.

## Layouts that carry a deck

Six layouts cover almost every business deck. Reuse them instead of composing
each slide freehand — repetition is what makes a deck look designed.

| Layout | Shape | Use |
|---|---|---|
| Title | Large title, small subtitle, generous whitespace | Opening, section breaks |
| Statement | One short sentence at 40–54 pt, centred | The claim the section defends |
| Two column | Heading plus two equal blocks | Before/after, problem/solution |
| Bullets | Heading plus 3–5 lines | Lists that genuinely are lists |
| Chart | Heading, one chart, one takeaway line | Any quantitative claim |
| Table | Heading, table, source note | Comparisons, pricing |

## Type scale

Pick one family and three sizes. On a widescreen deck (`LAYOUT_WIDE`,
13.33 x 7.5 in):

| Role | Size | Weight |
|---|---|---|
| Slide title | 28–32 pt | Bold |
| Body | 16–20 pt | Regular |
| Caption, source, axis label | 12–14 pt | Regular |
| Statement slide | 40–54 pt | Bold |

Nothing below 12 pt: it is unreadable at the back of a room and signals that the
slide is carrying too much. Two families maximum, and only when one is reserved
for numbers.

Font choice interacts with verification. Arial, Times New Roman and Courier New
have metric-compatible substitutes on Linux, so a rendered preview shows the
same line breaks the audience will see. Calibri and Cambria need Carlito and
Caladea installed to be trustworthy, and Aptos has no metric substitute at all.

## Colour

Four to six named colours, defined once as constants and reused:

- One dark neutral for text (near-black, not pure black).
- One light neutral for backgrounds.
- One brand colour for emphasis and chart series.
- One accent for the single thing per slide that must be noticed.
- Optionally one success and one warning colour for status.

Rules that hold regardless of palette:

- Body text needs a contrast ratio of at least 4.5:1 against its background;
  large display text at least 3:1. Grey-on-grey fails on a washed-out
  projector even when it passes on a laptop.
- Never encode meaning in colour alone — add a label or a shape, or the
  colour-blind third of the room loses the point.
- One accent per slide. Two accents mean neither is one.

## Spacing and alignment

- Keep a consistent margin — 0.5 in on a 13.33 in wide slide — and let nothing cross it.
- Align every element to a small number of x positions. Three lefts and two
  centres look composed; eleven arbitrary positions look thrown together.
- Whitespace is content. A slide with one sentence and empty space reads as
  confident; the same sentence padded with a stock photo reads as filler.
- Group related items by proximity, not by drawing a box around them.

## Data on slides

- The heading states the conclusion; the chart supports it. "Revenue grew 46%
  in two quarters" beats "Revenue by quarter".
- One chart per slide, one message per chart.
- Label axes with units. Start value axes at zero for bar charts; a truncated
  axis exaggerates the difference and destroys trust when noticed.
- Put the source and as-of date in a 12 pt caption.
- Drop chart junk: gridline clutter, 3-D effects, drop shadows, a legend for a
  single series.

## Avoid list

These are the marks of a deck nobody designed:

- Wall-of-text slides: a paragraph pasted into a bullet box.
- More than five bullets, or bullets nested three deep.
- Decorative stock photography behind text.
- Gradient fills and drop shadows used as decoration.
- Clip-art icon sets mixed from different visual styles.
- Every slide titled with a noun phrase, so the deck argues nothing.
- Nine-digit numbers unformatted (`1200000` instead of `$1.2M`).
- Placeholder text shipped in the final file: "Lorem ipsum", "Your text here",
  "TBD".
- Invented data. If the number is unknown, the slide says so.

## Self-review

Render the deck, then read the images against this list before delivering:

- [ ] Every slide's message is legible from the heading alone.
- [ ] No text touches or crosses a slide edge or overlaps another element.
- [ ] Type sizes come from the scale; nothing below 12 pt.
- [ ] The palette is the one that was chosen; no stray default blue.
- [ ] Every chart has axis units, a source, and no invented figures.
- [ ] No placeholder text and no orphaned template shapes remain.
- [ ] Slide count matches what was asked for.

<!-- sources: slidespeak-design, anthropic-pptx -->
