# Export and QA: judge the render, not the source

A deck is accepted on evidence from a rendered page, never on reading the HTML.
This file explains what the numbers mean, where each measurement lies to you, and
which command to run when the packaged gate cannot reach the artefact.
`scripts/deck_qa.mjs` is the packaged form of the Playwright path below: it walks
the slides, measures them, screenshots them, and optionally exports a PDF.

## Contents

- [What to measure](#what-to-measure)
- [Making the render deterministic](#making-the-render-deterministic)
- [PDF that keeps its colours](#pdf-that-keeps-its-colours)
- [Command paths](#command-paths)
- [Gate policy](#gate-policy)

## What to measure

Three geometry layers exist. Each one is blind somewhere, so a gate built on any
single layer passes broken decks.

### Layer 0 — document scroll height is unusable

```js
document.documentElement.scrollHeight // 720 on the overflowing slide AND on the clean ones
```

Measured on a three-slide deck where slide 2 overflows badly: all three slides
report `scrollHeight === clientHeight === 720` [verified]. The stage sets
`overflow: hidden`, which swallows the overflow before it ever reaches the
document scrolling box. This is the most common wrong gate — it returns a number,
the number looks healthy, and nothing is checked.

### Layer 1 — element rects locate and quantify, but cannot judge visibility

Compare every descendant rect against the slide rect. This is the only layer that
can say *which* element and *by how much*:

```js
const overflowing = (slide) => {
  const s = slide.getBoundingClientRect();
  return [...slide.querySelectorAll('*')]
    .map((el) => [el, el.getBoundingClientRect()])
    .filter(([, r]) => r.width > 0 && r.height > 0 && (r.bottom > s.bottom + 1 || r.right > s.right + 1))
    .map(([el, r]) => ({ tag: el.tagName, over: +(r.bottom - s.bottom).toFixed(1) }));
};
```

On the test deck this returned the exact offenders: `UL` bottom 834.7 and
`LI` bottoms 725.9 / 780.3 / 834.7 against a stage bottom of 720, i.e. 114.7px of
list hanging below the slide [verified].

The blind spot: under `overflow: hidden` a rect still reports the *uncut*
geometry. The element is invisible on screen while its rect claims it occupies
space, and an element the author deliberately clipped looks identical to a bug.
Rects quantify overflow; they do not prove anything about what a viewer sees.

### Layer 2 — container scroll size is the only true "this got clipped" signal

```js
const clipped = (slide) => [...slide.querySelectorAll('*')]
  .filter((el) => el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
  .map((el) => ({ tag: el.tagName, id: el.id, scrollH: el.scrollHeight, clientH: el.clientHeight }));
```

Same deck: `DIV#box2` reported `scrollHeight 685 > clientHeight 592` [verified],
true even though an ancestor hides the overflow. That is real clipping, proven.
The blind spot is resolution: it names the container, never the paragraph or list
item that caused it.

### Therefore: alarm on the union

Layer 1 finds the culprit, layer 2 proves the damage. Report a slide as failing if
either fires, and print both payloads — the container id from layer 2 plus the
overflow amount from layer 1 is enough to fix a slide without opening a browser.

### Two more metrics worth automating

- **Type floor.** Any text node whose computed `font-size` is below 24px on the
  1080-high stage fails. Read it from `getComputedStyle`, not from the
  stylesheet — inherited and shorthand values are where the small type hides.
- **Void ratio.** Track the largest empty vertical band inside the content area
  and cap it at roughly a fifth of the stage height (~230px of 1080). A slide
  that passes overflow checks can still be one line stranded on an empty field.

```js
[...slide.querySelectorAll('*')]
  .filter((el) => el.textContent.trim() && !el.children.length)
  .filter((el) => parseFloat(getComputedStyle(el).fontSize) < 24)
```

Ordering trap, and the one that produces false passes rather than noise:
`getBoundingClientRect()` returns the *transformed* border box, while
`getComputedStyle().fontSize`, `scrollHeight` and `clientHeight` return
untransformed CSS px [official, CSSOM View]. Normalise each group with its own
factor — rects by `canvasHeight / frame.height`, layout values by
`canvasHeight / slide.offsetHeight` — or the two disagree by exactly the stage
scale. Measured on a 1920x1080 stage letterboxed into a 1280x720 viewport
(scale 0.667), a single shared factor turns an authored 16px caption into a
reported 24px and passes the floor it should fail [verified]. `deck_qa.mjs`
keeps the two factors separate and reports the same numbers at any viewport;
hand-rolled measurement has to do the same.

## Making the render deterministic

A gate that returns different numbers on two runs is worse than no gate: it
trains you to re-run until green.

### Fonts

`await document.fonts.ready` works, and you must await it before measuring type or
taking screenshots. Measured on the same page: status goes `loading` → `loaded`
and `document.fonts.check('700 64px Inter')` goes `false` → `true` [verified].
Fallback metrics are a different size, so measuring early produces bogus overflow
reports.

```js
await page.goto(url, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
const ok = await page.evaluate(() => document.fonts.check('700 64px Inter'));
```

Two traps make the obvious gates useless:

- Right after appending a font `<link>`, `document.fonts.status` already reads
  `loaded` [verified]. Awaiting `fonts.ready` at that instant can resolve before
  the new font has even started loading. Force layout first, or call
  `document.fonts.load('700 64px Inter')` and then poll `check()`.
- Most `FontFaceSet` entries stay `unloaded` forever. On one Google Fonts family,
  14 faces existed and only 2 were `loaded` [verified] — the service ships one
  face per `unicode-range` slice and the browser loads only the slices in use.
  Gating on "every face is loaded" never passes. Gate on
  `fonts.check('<weight> <size> <family>')` for the families the deck actually
  uses.

### Animation

`page.screenshot({ animations: 'disabled' })` freezes CSS animations and
transitions only. It does nothing to canvas or `requestAnimationFrame` work:
two consecutive screenshots of the same rAF canvas slide hashed
`6c9bca92278f03de` and `adc2096d1345406f` (sha256, first 16 hex) [verified], and
headless advanced 56 frames while measuring [verified].

Determinise on the page side instead:

```js
await context.addInitScript(() => {
  let seed = 1;
  Math.random = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
  const fixed = 1700000000000;
  Date.now = () => fixed;
});
```

Better, have the deck expose an explicit freeze hook (`window.__freeze()`) that
cancels its rAF loop and paints a final frame; a hook is honest about what it
stops, whereas clock patching can stall a loop that waits on elapsed time.

Do not pixel-diff canvas slides at all. Assert geometry and text there, and keep
visual baselines for static slides. WebGL was not tested in this round — no claim
is made about SwiftShader stability either way.

### Screenshot size

Pixel dimensions come from `viewport x deviceScaleFactor`, not from the deck's own
scaling: `1280x720` at `deviceScaleFactor: 2` produced `2560x1440` PNGs
[verified]. Choose the viewport to match the measurement space you picked above,
then raise `deviceScaleFactor` only for reviewer-facing images.

## PDF that keeps its colours

Background loss has two independent causes, and fixing one at random works often
enough to teach the wrong lesson. Fix both.

Sampled top-left pixel of page 1, deck background
`linear-gradient(135deg,#1b2140,#3a1d5c)`:

| Deck CSS | Export flag | Sampled pixel |
|---|---|---|
| no `print-color-adjust` | default (`printBackground` unset) | `(255,255,255)` — page is blank white [verified] |
| no `print-color-adjust` | `printBackground: true` | `(27,33,64)` [verified] |
| `print-color-adjust: exact` | default (`printBackground` unset) | `(27,33,64)` [verified] |
| `print-color-adjust: exact` | `printBackground: true` | `(27,33,64)` [verified] |

`printBackground` defaults to `false` [official]. The third row is the
counter-intuitive one: the page-side declaration alone was enough, which means a
deck that renders fine through one exporter can go white through another. Ship
both halves:

```css
html, body, .slide {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
```

```js
await page.pdf({ path: 'out/deck.pdf', printBackground: true, preferCSSPageSize: true });
```

### Paper size

`preferCSSPageSize` defaults to `false` [official], so by default the exporter
ignores the deck's own `@page` rule and scales the content to fit the paper
format — that is where "my 16:9 deck came out as portrait A4 with margins" comes
from. With `@page { size: 1280px 720px; margin: 0 }` plus
`preferCSSPageSize: true`, the output measured `960 x 540 pt` [verified]
(1280x720 CSS px at 96dpi = 960x540pt). Without any `@page` rule, the Chromium
CLI produced Letter `612 x 792 pt` [verified].

### Print media takes over

`page.pdf()` renders with the `print` CSS media type [official], and Puppeteer
documents the same behaviour for its own `Page.pdf()` [official]. Any
`@media print` branch in the deck becomes the export layout, so a print branch
written for handouts will quietly replace the deck you validated on screen.
Either keep the deck free of print branches, or call
`page.emulateMedia({ media: 'screen' })` before exporting and state which one the
gate measured.

## Command paths

### A. Any single-file deck — Playwright (default)

One dependency covers measurement, screenshots and PDF, so the gate and the
deliverable come out of the same render.

```bash
cd /work && npm i playwright && npx playwright install chromium
node -e '
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--no-sandbox"] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await p.goto("file:///work/deck.html", { waitUntil: "load" });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: "out/slide.001.png" });
  await p.pdf({ path: "out/deck.pdf", printBackground: true, preferCSSPageSize: true });
  await b.close();
})();'
```

Page navigation between slides has to come from the deck (a `window.deckGoto(i)`
style hook or a documented key binding); the browser has no concept of a slide.
If the deck needs runtime resources it must be served, because a `file://` page
cannot `fetch` at all:

```bash
(cd /path/to/deck && python3 -m http.server 8766 &) && sleep 1
```

If the source is a Marp project, use its own exporter rather than driving the
browser yourself: `npx -y @marp-team/marp-cli@latest --pdf --pdf-notes
--pdf-outlines --allow-local-files deck.md`, and `--images png` for per-slide
PNGs named `deck.001.png` upward. Local images and fonts are refused unless
`--allow-local-files` is passed, and the refusal is only a warning [official] —
the export still "succeeds" with pieces missing.

### B. A third-party deck project you will not modify — decktape

Use this when the artefact is an existing reveal.js / impress / bespoke project
and adding a hook is out of scope. It drives the deck by key press.

```bash
cd /out/dir && mkdir -p shots && npx -y decktape@latest \
  --chrome-path=/usr/bin/chromium --chrome-arg=--no-sandbox \
  -s 1280x720 --slides 1-12 --screenshots --screenshots-directory=shots \
  generic --key=ArrowRight file:///path/deck.html out.pdf
```

Three traps, all reproduced:

- Out of the box it downloads its own Chrome and fails when that cache is empty:
  `Could not find Chrome (ver. …) … /root/.cache/puppeteer` [verified] — the stack
  comes from `puppeteer-core`'s executable resolution. Point it at the system
  browser with `--chrome-path` and add `--chrome-arg=--no-sandbox` for root
  containers.
- `--screenshots-directory` is concatenated with the output file name. Give an
  absolute output path and you get a nested path that is never created:
  `ENOENT … open '/tmp/deck/dt-png/tmp/deck/decktape_1_1280x720.png'` [verified].
  Always `cd` into the output directory and pass a relative name.
- `generic` stops when a key press causes no further DOM mutation in `body`. A
  deck whose last slide rewrites a class to the same value still mutates an
  attribute, so it never stops — one run reached slide 17 of a 3-slide deck before
  being killed [verified]. Always pass `--slides 1-N` with the real slide count.

### C. No Node available — Chromium CLI

```bash
chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
  --virtual-time-budget=3000 --print-to-pdf=/out/deck.pdf file:///path/deck.html

chromium --headless --no-sandbox --disable-gpu --window-size=1280,720 \
  --virtual-time-budget=3000 --screenshot=/out/p1.png file:///path/deck.html
```

- As root, omitting `--no-sandbox` produces no file whatsoever: stderr says
  `Running as root without --no-sandbox is not supported` and the following `ls`
  fails [verified]. There is no partial output to notice, so a pipeline that does
  not check the exit code reports success on nothing.
- There is no page-size flag. Paper comes from the deck's
  `@page { size: 1280px 720px; margin: 0 }`; without it you get Letter, and
  `--screenshot` / `--print-to-pdf` capture only the currently active slide
  (1 page) [verified].
- Use `--virtual-time-budget=<ms>` to fast-forward timers and loading instead of
  sleeping a guessed number of seconds. It does not determinise canvas work — the
  page-side measures above still apply.

### Verifying an exported PDF without ImageMagick

```bash
pdftoppm -r 18 -f 1 -l 1 -singlefile out/deck.pdf out/page1
python3 -c "
d = open('out/page1.ppm','rb').read()
i = 0
for _ in range(3): i = d.index(b'\n', i) + 1
print(tuple(d[i:i+3]))"
```

`(255,255,255)` at the top-left of a dark deck means the background was dropped —
go back to the two-part fix above. Note that `-ppm` is not a valid poppler flag;
PPM is the default output format and passing the flag prints usage and exits
non-zero [verified].

## Gate policy

- Measure before you export. Rendering a PDF from a deck that fails the geometry
  gate produces an artefact that looks finished and is not; make the gate exit
  non-zero and let the export step depend on it.
- Cap automatic repair at three rounds, then stop and hand the measurement report
  to a human. Each round must change a layout input — cut content, step the type
  down one rung, switch the slide to a denser layout — never the threshold. If
  three rounds have not fixed it, the slide has more content than the stage holds
  and that is an editorial decision.
- Report per slide, not per deck. "Slide 7: `UL` 114.7px below the stage,
  `#box2` scrollHeight 685 > clientHeight 592" is actionable; "3 slides failed"
  is not.
- Keep a human read of the rendered PNGs as the second gate. Geometry checks
  cannot see that a chart contradicts its caption or that two slides make the same
  point.
- When the host has no browser, say so. Write "layout not verified: no browser in
  this environment" and list which layers ran. Never describe an export as clean
  when nothing rendered it — an unverified deck that is honestly labelled costs
  one review pass; a falsely cleared one is discovered on stage.

<!-- sources: playwright, decktape, chromium-headless, marp-cli, puppeteer, slidespeak-design, ohmyagent-oma-slide -->
