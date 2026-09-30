# Escaping to a framework

The hand-written single-file stage stops paying for itself at a few specific
requirements. This file names those requirements, and — once you have escaped —
gives the four facts per framework that decide whether a deck ships: size model,
overflow behaviour, speaker notes, export.

## Contents

- [Escape triggers](#escape-triggers)
- [Per-framework facts](#per-framework-facts)
  - [reveal.js](#revealjs)
  - [Slidev](#slidev)
  - [Marp](#marp)
- [Traps that cost a rebuild](#traps-that-cost-a-rebuild)
- [What stays yours after escaping](#what-stays-yours-after-escaping)

## Escape triggers

Escape when a requirement is structural, not when a slide is hard to style. Each
row costs something; read the third column before you switch.

| Requirement that triggers the escape | Escape to | What it costs |
|---|---|---|
| Markdown is the single source of truth, and one command has to produce PDF + speaker notes | Marp | Layout freedom collapses to CSS on `section`; one slide size per theme; nothing handles vertical overflow |
| Magic-move code diffs, Monaco editing, recording, remote control, hosting the deck as a web app, or an editable PowerPoint copy from the same source | Slidev | The artifact is a Vite SPA — it cannot be double-clicked open, needs Node plus `playwright-chromium` to export, and needs an HTTP host with SPA rewrites |
| A mature presentation runtime — fragments, speaker view, scroll view — and you accept a multi-file artifact | reveal.js | `dist/` plus `plugin/` files travel with the deck; PDF comes out of the browser print dialog, confirmed only in Chrome/Chromium |
| Non-linear zooming canvas instead of a page sequence | impress.js | No slide-size contract, no speaker notes, no export path of its own; steps are absolute canvas coordinates (`data-x/y/z`, px, measured at the step's centre) and PDF requires an external key-walking exporter |
| The PDF page size must equal a non-16:9 paper size | Marp | The theme's `width`/`height` is the PDF page size, so a second paper size means a second theme |
| Readers browse on their own instead of watching you present | reveal.js | Scroll view (`view: 'scroll'`, reveal.js 5+) turns the deck into a scrollable document, which invalidates any per-slide visual proof you captured in slide mode |

Do not escape for: a long heading (fit the text), one dense slide (split it), or
PDF background loss (that is an export flag plus a CSS property, not a framework
defect).

## Per-framework facts

**PowerPoint output.** reveal.js has no `.pptx` exporter. Marp `--pptx` and
Slidev `--format pptx` put one rendered picture on each slide, so nothing in the
file can be edited. Both also ship an editable mode that rebuilds the slide as
native shapes, and both are approximations of the browser deck:

- Slidev `--format pptx-editable` (52.20+). SVG (so Mermaid diagrams and icons),
  `<canvas>`, iframes, video, KaTeX, CSS gradients, `filter`, blend modes and
  `clip-path` stay pictures; a slide it cannot rebuild falls back to a picture on
  its own; `::before`/`::after` decorations in flow are dropped (code-block line
  numbers among them); fonts are named, not embedded, and text may wrap
  differently in PowerPoint. The export prints what it dropped and which fonts
  the recipient needs — read that output.
- Marp `--pptx --pptx-editable` is experimental, needs LibreOffice Impress next
  to the browser, drops speaker notes, and may error or come out incomplete on a
  theme with complex styles.

Verify before sending — count text runs per slide; 0 means that slide is a picture
(`grep -c` would count lines, and slide XML is one line):

```bash
for s in $(unzip -Z1 deck.pptx 'ppt/slides/slide*.xml'); do
  echo "$s $(unzip -p deck.pptx "$s" | grep -o '<a:t>' | wc -l)"; done
```

Use these modes for "someone touches up wording in a copy". When an editable
PowerPoint file is the deliverable in its own right, that is the `office` skill,
not an export from here.

### reveal.js

**Size and scaling model.** Config defaults are `width: 960`, `height: 700`,
`margin: 0.04`, `minScale: 0.2`, `maxScale: 2.0` [official]. The deck is scaled
uniformly to the viewport within those bounds; content is authored against the
configured pixel size, so set `width: 1920, height: 1080` if you are porting a
hand-built 1080p stage and want the type scale to carry over unchanged. Pass
`center: false` to stop vertical centring of each slide. `disableLayout: true`
hands sizing entirely to your own CSS — and then reveal no longer re-lays out on
resize, so you must call `Reveal.layout()` yourself [official].

**Overflow behaviour.** Nothing shrinks to fit. Scaling is computed from
`width`/`height` alone, never from content height, so an overfull slide simply
spills past the canvas. The three governors, in order of preference: `r-fit-text`
on a heading (fitty-driven, text only, no vertical budget awareness);
`r-stretch` on one media element per slide — it must be a direct child of the
`<section>`; `view: 'scroll'` (reveal.js 5+) for reading rather than presenting,
which also self-activates below `scrollActivationWidth`. In PDF, an overlong
slide is silently split across several pages unless you set
`pdfMaxPagesPerSlide: 1` [official].

**Speaker notes.** Write `<aside class="notes">…</aside>` inside the section, or
`data-notes="…"` on it; in Markdown decks use `data-separator-notes="^Note:"`.
`S` opens the speaker window. Run locally, that window requires a local HTTP
server [official] — the same constraint that external Markdown files have. A
`file://` copy presents and exports fine and has no speaker view.

**Export.** Append `?print-pdf` to the URL, then print: Destination *Save as
PDF*, Layout *Landscape*, Margins *None*, Background graphics *on*. Confirmed
only in Chrome and Chromium [official]; treat other browsers as unsupported
rather than untested. Notes reach the PDF only with `showNotes: true` (overlaid)
or `showNotes: 'separate-page'`. Fragment steps each become a page unless you
set `pdfSeparateFragments: false`. For an unattended run, drive the same deck
through decktape with an explicit page bound instead of the print dialog.

### Slidev

**Size and scaling model.** The canvas is declared in headmatter with
`canvasWidth` (px) and `aspectRatio`; the documented worked example is
`canvasWidth: 980` with `aspectRatio: 16/9`, giving a 980x551 px canvas. At
runtime `packages/client/internals/SlideContainer.vue` computes
`scale = min(containerWidth / canvasWidth, containerHeight / canvasHeight)` and
publishes it as the CSS variable `--slidev-slide-scale` [official]. The UI
offers *Fit* versus *1:1*; print mode ignores that toggle, so a deck that only
looks right at 1:1 will not export right.

**Overflow behaviour.** Hard clip, silently. `.slidev-slide-content` is a fixed
`canvasWidth x canvasWidth/aspectRatio` px box with `overflow-hidden`, and the
outer `.slidev-slide-container` hides overflow too [official]. Because the scale
factor depends only on canvas versus container, adding content never shrinks
anything — the extra rows are simply cut off with no scrollbar and no warning.
The only fixes are manual: `zoom: 0.8` in the slide frontmatter, or wrap the
block in `<Transform :scale="0.8">`.

**Speaker notes.** Notes are the **last** HTML comment block of the slide. A
comment placed between two paragraphs is not notes and is dropped from the
presenter view [official] — this fails silently and is the single most common
Slidev notes bug. Presenter mode lives at `http://localhost:<port>/presenter`,
batch note editing at `/notes-edit`, and `slidev build --without-notes` strips
notes from a public build.

**Export.** `slidev export` writes `./slides-export.pdf` and requires
`playwright-chromium` installed inside the project — it is not bundled. Defaults
to one page per slide with click animations disabled; `--with-clicks` gives one
page per click step. Useful flags: `--range 1,6-8,10`, `--with-toc`, `--dark`,
`--omit-background`, and for content that arrives late `--wait <ms>` or
`--wait-until domcontentloaded|none` (the looser value returns before the page
is complete, so re-check the output). A browser-driven exporter is also served
at `http://localhost:<port>/export`.

### Marp

**Size and scaling model.** Slide size is a theme property: `width` and `height`
on the root `section` (or `:root`), in absolute units only — cm, in, mm, pc, pt,
px, Q — defaulting to 1280x720 [official]. It is one size per theme: inline
style, a custom class, or a CSS variable cannot change the size of a single
slide. That same size becomes the PDF page size, so the theme is also the paper
setup. From Markdown you select a theme's size preset with the global `size:`
directive (for example `size: 4:3`). Note that `rem` inside a Marpit theme is
converted to resolve against the parent `section`, not the `html` root
[official].

**Overflow behaviour.** Auto-scaling is horizontal only; content can still
overflow the bottom of the slide [official]. It is also off by default: a theme
must declare `@auto-scaling true` (or a subset such as
`@auto-scaling code,math,fittingHeader`) in a CSS comment, and the bundled
themes already do. `<!-- fit -->` applies to headings only and scales them to
the slide width. The only vertical governor is a `max-height` on the
`::part(auto-scaling)` hook; past that, cut content.

**Speaker notes.** Notes are Marpit presenter notes written as HTML comments.
The bespoke template binds `p` to open the presenter window, but
`src/templates/bespoke/presenter/normal-view.ts` registers that key only when
`storage.available` — localStorage must be usable [official]. Synchronisation
runs through `bespoke-marp-sync-<key>`, the presenter page is
`?view=presenter&sync=<key>`, and the next-slide preview is an
`<iframe src="?view=next">` driven by postMessage. So a single-file HTML opened
over `file://` in a browser that blocks storage has no presenter view at all —
that is the mechanism, not a vague recommendation. Non-interactive routes:
`marp --notes deck.md` for a plain-text notes file, `--pdf-notes` for PDF
annotations.

**Export.** `marp --pdf deck.md`, or `marp deck.md -o deck.pdf`; a local Chrome,
Edge, or Firefox must be installed. Add `--pdf-notes` to carry speaker notes in
as PDF annotations and `--pdf-outlines` for bookmarks (it generates both page
and heading outlines; `--pdf-outlines.headings=false` keeps only pages). For a
self-contained single file, `marp deck.md -o deck.html` inlines the theme CSS
and the bespoke runtime into one document via the `style!= css` and
`script!= bespoke.js` template slots [official]. Browser-backed conversions
refuse to read local files by default: you get a warning and an incomplete
artifact with missing images. `--allow-local-files` lifts that, but it grants
the Markdown read access to the local filesystem, so use it only on Markdown you
wrote. Server mode exposes the same conversion as
`GET http://localhost:8080/deck.md?pdf`.

## Traps that cost a rebuild

- Slidev frontmatter with a relative asset path (`background: ./cover.png`)
  renders in dev and 404s after `slidev build` — Vite cannot statically analyse
  it. Put the file in `public/` and reference it absolutely as `/cover.png`
  [official].
- `slidev build --base` must begin and end with `/` [official], so a relative
  `./` base is impossible and the built SPA cannot be opened from `file://`. If
  the deliverable is "a file I can email", Slidev is the wrong route.
- Marp auto-scaling depends on `inlineSVG`; disable it and `<!-- fit -->` and
  auto-shrinking blocks stop working entirely, rendering at base size with no
  error [official].
- reveal `r-stretch` allows one element per slide and it must be a direct child
  of the `<section>`. Wrap it in a layout `div` and it quietly stops stretching
  [official].
- reveal PDF export is confirmed only in Chrome/Chromium [official]. A PDF
  produced by another browser's print path is not a checked artifact.
- In Marpit themes `rem` is rewritten to be relative to the parent `section`
  rather than the `html` root font size [official], so a type scale copied from
  a website silently changes magnitude.
- A Marpit theme without the `@theme` metadata comment does not register; with
  minified Sass output write it as a preserved comment (`/*! … */`) or the
  minifier deletes it [official].
- Marpit drops the entire `content` declaration on `section::after` unless it
  includes `attr(data-marpit-pagination)` — page numbers vanish with no CSS
  error [official].
- decktape ships plugins for reveal.js, impress.js, bespoke and others but none
  for Slidev [official]; use `slidev export` there instead of reaching for a
  generic exporter.

## What stays yours after escaping

A framework takes over exactly two things: the presentation runtime and the
export pipeline. Content pacing, the type floor, and the rendered-geometry gate
stay your responsibility, because none of the three frameworks measures whether
a slide actually fits.

Carry the type floor across by ratio rather than by pixel value, since the
canvases differ. The floor is 24 px on a 1080-high canvas (2.2% of canvas
height); on Marp's default 720-high canvas that is 16 px, body text 21–27 px,
slide titles 37–43 px, statement slides 53–72 px. Recompute once per canvas and
write the numbers into the theme, rather than re-deriving them per slide.

Keep the geometry gate too, pointed at whatever the framework renders: the
`?print-pdf` page for reveal, `slidev export --format png`, `marp -o deck.png`.
Run the deck QA script (`scripts/deck_qa.mjs`) against those renders exactly as
you would against a hand-built deck. Escaping changes who owns the runtime; it
does not add a safety net for overflow.

<!-- sources: revealjs, slidev, marp-cli, marp-core, marpit, impress-js -->
