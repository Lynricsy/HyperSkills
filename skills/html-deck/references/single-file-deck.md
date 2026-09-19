# The single-file deck contract

A deck that survives being emailed, double-clicked and projected is one HTML file with no runtime
dependencies. Everything below is what that costs and where it silently fails.

## Contents

- [The stage](#the-stage)
- [Switching slides](#switching-slides)
- [Navigation and addressing](#navigation-and-addressing)
- [Staying self-contained](#staying-self-contained)
- [Print shape](#print-shape)
- [State that outlives the deck](#state-that-outlives-the-deck)
- [Things that look fine until they render](#things-that-look-fine-until-they-render)
- [Handing it over](#handing-it-over)

## The stage

Author on one fixed canvas, 1920x1080 unless the venue dictates otherwise, and scale the whole
stage with a single transform:

```css
#stage { width: 1920px; height: 1080px; transform: translate(-50%, -50%) scale(var(--scale, 1)); }
```

```js
const fit = () => document.documentElement.style.setProperty(
  '--scale', Math.min(innerWidth / 1920, innerHeight / 1080));
addEventListener('resize', fit); fit();
```

Every size inside the stage is a px on that canvas. No `vw`, `vh`, `vmin`, `clamp()` or media
queries below `#stage`. Two reasons, and the second is the one that bites:

- The stage already scales, so a viewport unit inside it scales twice. A heading tuned at
  1280x720 is a different size on a 1920x1080 projector.
- The QA render and the export use their own viewport. With viewport-based type, the sizes measured
  in review are not the sizes that ship, so a clean gate proves nothing. Fixed px is what makes
  "measured once, correct everywhere" true.

Letterboxing is the intended outcome: black bars on a 16:10 projector, never reflow. A deck that
reflows has no stable geometry, and no measurement of it means anything.

Keep a safe area — 96px on a 1920 canvas — and let nothing cross it. Projectors overscan, and the
first thing lost is whatever sits in the last few percent of the frame.

## Switching slides

Toggle `visibility`, `opacity` and `pointer-events`. Do not toggle `display`:

```css
.slide            { position: absolute; inset: 0; display: flex; visibility: hidden; opacity: 0; }
.slide.is-current { visibility: visible; opacity: 1; }
```

`display` is already carrying the layout (`flex`, `grid`), and the print rules need it again to
un-stack the deck onto pages. A deck built on `.slide { display: none }` needs a third override with
`!important` the moment it is printed, and any layout class that sets `display` later in the cascade
makes every slide visible at once.

Absolutely positioned slides all occupy the same box, so the stage height stays exactly one canvas
whatever the slide count.

## Navigation and addressing

Bind the whole set, because people use all of it and presentation remotes emit `PageUp`/`PageDown`:
`ArrowRight`, `Space`, `PageDown` forward; `ArrowLeft`, `PageUp` back; `Home`, `End`; `F` for
fullscreen if you add it. Call `preventDefault()` only on keys you handled.

Mirror the slide index into the hash with `history.replaceState`, so a URL points at a slide and a
reload lands where the presenter was. `pushState` per slide buries the back button under one entry
per keypress.

Expose a navigation contract for the QA tooling:

```js
globalThis.deck = { get count() { return slides.length; }, get index() { return index; }, goto };
```

Without it, an external renderer walks the deck by sending `ArrowRight` and hoping the runtime kept
up; a deck with click-steps or transitions desynchronises from that walk and the screenshots stop
matching the slides.

## Staying self-contained

`fetch()` of a `file:` URL is rejected outright by Chromium — the scheme is unsupported, and it is
not a CORS setting anyone can relax [verified]. Consequences:

- Slide content, notes and data live in the document. No `slides.json`, no `notes.md`.
- Images are data URIs, or the deck ships as a folder and stops being a single file. Choose one and
  say which.
- Fonts: a metric-stable system stack (Arial, Helvetica, Georgia, Times New Roman) or a base64
  `@font-face`. A remote font fails in a room with no network, and the fallback metrics reflow every
  line you checked.
- A local HTTP server (`python3 -m http.server 8000`) removes all of the above restrictions, but a
  deck that needs one is no longer a file you can send.

Third-party scripts from a CDN have the same failure mode as remote fonts, one tier worse: a chart
library that does not load leaves an empty box where the evidence was.

## Print shape

Exported pages render in `print` media, so the stacked-slide layout has to be undone there or the
PDF holds exactly one page:

```css
@media print {
  @page { size: 1920px 1080px; margin: 0; }
  #stage { position: static; transform: none; overflow: visible; }
  .slide { position: relative; visibility: visible; opacity: 1;
           width: 1920px; height: 1080px; break-after: page; }
  .slide:last-of-type { break-after: auto; }
}
```

Put `print-color-adjust: exact` (with the `-webkit-` prefix) on `body`. Without it the print
pipeline may drop backgrounds even when the exporter asks for background graphics.

Check the exported page count against the slide count. A mismatch means a slide grew past one page
height, which the screen render hides because the stage clips it.

## State that outlives the deck

Under `file://` every local document shares the single origin `file://`, so `localStorage` is shared
across every deck on the machine [verified]. A key like `slide` collides between two decks and the
second one opens on the first one's page. Namespace anything you persist with the deck's
`location.pathname` plus a deck id, or persist nothing — for a talk, nothing is usually right.

## Things that look fine until they render

- SVG `<text>` does not wrap. A label longer than its shape silently overruns the diagram; size the
  shape for the longest label or put the text in a `foreignObject`.
- `position: sticky` inside an absolutely positioned slide has no scroll container to stick to, so
  it behaves as `relative` and quietly lands somewhere else.
- A CSS function cannot be negated by prefixing a minus sign; `-clamp(...)` is dropped as invalid.
  Write `calc(-1 * clamp(...))`.
- Content set from data at runtime (dates, counts) changes length between the review render and the
  talk. Render the real strings into the file.
- Animations belong inside `@media (prefers-reduced-motion: no-preference)`, and any control you add
  keeps a visible focus ring — a deck is driven from the keyboard by definition.

## Handing it over

State the three things the recipient cannot infer from the file: how to open it (double-click, or
serve the folder), which keys drive it, and what was verified — slide count, the render the
screenshots came from, and whether the PDF was produced and checked.

<!-- sources: zarazhangrui-frontend-slides, event4u-html-deck, flabs-slideshow-deck, lewislulu-html-ppt -->
