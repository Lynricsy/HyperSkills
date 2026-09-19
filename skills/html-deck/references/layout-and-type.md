# Layout and type on a fixed canvas

Numbers for a 1920x1080 authoring canvas. Palette judgement, contrast ratios and web typography
belong to the `frontend-design` skill; this file only covers what changes because the medium is a
fixed, projected, non-scrolling frame.

## Contents

- [Canvas, safe area, grid](#canvas-safe-area-grid)
- [Type scale](#type-scale)
- [Layout families](#layout-families)
- [Image slots](#image-slots)
- [Density](#density)
- [Tokens the export path can read](#tokens-the-export-path-can-read)
- [What the gate checks and what it cannot](#what-the-gate-checks-and-what-it-cannot)

## Canvas, safe area, grid

| Quantity | Value | Why this one |
|---|---|---|
| Canvas | 1920 x 1080 | 16:9, and the px equal the projector's pixels at 1080p, so a font size is a real size |
| Safe area | 96px all sides | 5% of width; projector overscan and screen bezels eat the outer band |
| Columns | 12 | divides by 2, 3 and 4, so halves, thirds and quarters all land on the grid |
| Column width | 136px | `(1920 - 2*96 - 11*32) / 12` |
| Gutter | 32px, or 8px when a table needs density | two values, not a slider: pick one per deck and every gap matches |
| Baseline step | 8px | every margin and padding is a multiple; unaligned spacing is the most visible amateur tell |

Gutters are an enumeration rather than a free value on purpose: a design system that ships its grid
as source constants exposes exactly two gutter widths, and that is what makes "these two blocks are
aligned" checkable instead of arguable.

Alignment rule: every element starts on one of the 12 column edges. Three distinct left edges per
slide is a composition; eleven is a mess, and it reads as one even to people who cannot name why.

## Type scale

The deck inherits the slide type scale from the pt sizes used for `.pptx` decks, converted once: a
widescreen slide is 540pt tall, this canvas is 1080px tall, so **1pt = 2px**.

| Role | Size | Weight | Line height | Source pt |
|---|---|---|---|---|
| Statement / cover | 80-108px | Bold | 1.05 | 40-54pt |
| Slide title | 56-64px | Bold | 1.1 | 28-32pt |
| Body, list item | 32-40px | Regular | 1.4 | 16-20pt |
| Caption, source, axis label | 24px | Regular | 1.3 | 12pt |
| Floor | 24px | — | — | 12pt |

Nothing renders below 24px. It is unreadable from the back of a room, and reaching for a smaller
size is the symptom of a slide carrying more than one idea — split the slide or cut the content.
Shrinking type to make content fit is the one failure the render gate cannot attribute later: the
geometry passes and the room cannot read it.

Measure is shorter here than on a page: about 24em, roughly 45-60 characters at body size, half
that for CJK. A projected line longer than that loses the reader between line ends.

Two families at most, and only when one is reserved for figures. Prefer faces with stable metrics
across machines (Arial, Helvetica, Georgia, Times New Roman): a substituted face with different
metrics changes every line break, so the render that was reviewed is not the render that projects.

Statement slides carry one sentence at 80-108px. If the sentence does not fit at 80px, it is a
paragraph and belongs in the notes.

## Layout families

Six families cover almost every deck. Reuse them; repetition is what makes a deck look designed,
and inventing a composition per slide is what makes it look generated.

| Family | Grid | Use |
|---|---|---|
| Cover | full bleed, title on columns 1-8 | opens the deck, names the speaker and date |
| Statement | full bleed, one centred block, columns 2-11 | the sentence the talk is built on |
| Title + body | title on 1-12, body on 1-7, optional figure on 8-12 | the default working slide |
| Split | two blocks on 1-6 and 7-12 | before/after, two options, claim and evidence |
| Figure-led | figure on 1-12 or 1-8, caption on 9-12 | the chart is the argument |
| Section divider | full bleed, number and label | only in decks past 12 slides |

One family per slide, and no more than two consecutive slides in the same family. A deck that
alternates title+body and split for twenty slides reads as a form someone filled in.

## Image slots

- Slots are fixed ratios: 16:9 full bleed, 4:3 inset, 1:1 portrait, 21:9 band. Pick the slot first,
  then crop the image to it. Cropping to whatever the image happens to be is why deck images look
  pasted.
- Reserve the slot in markup with `width`/`height` or `aspect-ratio` so a slow image cannot reflow
  the slide between the review render and the talk.
- Text over an image needs a scrim — a solid or gradient layer between them — not a thicker font.
  Faces and horizons move; a scrim makes legibility independent of what the photo contains.
- Keep the subject out of the outer 96px: that band is where overscan and the progress indicator
  live.
- A screenshot pasted at its native size is illegible on a projector. Crop to the region under
  discussion and scale that to the slot; a full IDE window is never the region under discussion.

## Density

Two modes per deck, chosen once:

| Mode | Body size | Blocks per slide | For |
|---|---|---|---|
| Spoken | 36-40px | 1 claim, up to 3 supporting lines | a live talk where the speaker is the content |
| Read-alone | 32px | 1 claim, up to 6 lines or a small table | a deck sent to be read without narration |

Mixing the two within a deck is deliberate rhythm; drifting between them slide by slide is not. A
read-alone deck is the only case where a dense table is acceptable, and even there 8px gutters plus
24px captions are the limit before it should have been a document.

## Tokens the export path can read

Declare colours, sizes and spacing as custom properties on `:root`, never as literals inside
components. The export and QA steps read computed styles, so a token is inspectable — a hard-coded
`#7dd3fc` in three places is three independent chances to drift, and nothing can check it.

One accent, used for the single thing per slide that must be noticed. A second accent means neither
is one. Pair every accent with an explicit ink colour (`--accent-ink`) for text placed on it;
whichever literal you would have written fails on half the palettes.

Contrast ratios, colour-blind safety and dark-mode pairing are the `frontend-design` skill's
numbers — apply them, do not restate them here. The deck-specific addition: verify contrast on the
rendered PNG rather than on the token pair, because projection flattens the low end of the range and
a ratio that passes in a browser can vanish in a bright room.

## What the gate checks and what it cannot

`scripts/deck_qa.mjs` proves geometry: nothing crosses the frame, nothing is clipped, no text falls
below the floor. It cannot tell you that a slide is ugly, that the accent is on the wrong element,
or that a chart argues for the opposite conclusion. Read the rendered PNGs; the gate exists so that
what you read is the real layout rather than an optimistic mental one.

<!-- sources: event4u-html-deck, slidespeak-design, zarazhangrui-frontend-slides, carbon-grid, visual-cognition-slides -->
