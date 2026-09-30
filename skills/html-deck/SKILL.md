---
name: html-deck
description: "Creates browser HTML slide decks. Do not load for editable PowerPoint files or responsive websites; those are the office and frontend-design skills."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.30"
  category: task
---

# html-deck

Paths below are relative to this skill's directory.

## Scope

Slides that a browser presents: a single self-contained HTML file by default, or a Marp, reveal.js
or Slidev project when the default stops paying. Covers the fixed presentation canvas, slide
layout and type, deck sequence and pacing, speaker notes and presenter mode, PDF and PNG export,
and the render-time measurement that decides whether the deck is deliverable.

Not covered — do not answer from this skill:

- Binary `.pptx`, `.potx`, pptxgenjs and python-pptx: the `office` skill. Exporting a PDF from an
  HTML deck is here, and so is a PowerPoint copy of a Slidev or Marp deck for someone to touch up
  wording: Slidev `--format pptx-editable` and Marp `--pptx --pptx-editable` rebuild text as native
  shapes, while plain `pptx` export is one picture per slide (`references/frameworks.md`). An
  editable PowerPoint file as the deliverable in its own right is `office`.
- Web interface visual direction, WCAG figures, palette and typography fundamentals, motion
  durations, Core Web Vitals: the `frontend-design` skill. Apply those conclusions on a fixed
  projected canvas; do not restate the numbers.
- Generating imagery with a model, provenance and synthetic-content disclosure: the
  `generative-media` skill. Image slots, ratios and text-over-image handling are here.
- Transcoding, cropping and stitching existing assets: the `media-processing` skill.
- READMEs, tutorials, reference pages, ADRs and changelogs: the `technical-writing` skill. The
  spoken narrative of a talk is here.
- Print posters, canvas design and brand identity systems.
- Hosted presentation services (Google Slides, Canva, Figma Slides) and their APIs.
- Recording the deck to video.

## Core rules

- Author on one fixed canvas (1920x1080 unless the venue says otherwise) and scale the whole stage
  with a single transform. Letterboxing is correct; reflow destroys the only stable geometry there is.
- Never use `vw`, `vh`, `vmin` or `clamp()` inside the stage. The stage already scales, and export
  runs at a different viewport, so viewport-relative type makes a passing review meaningless.
- Nothing renders below 24px on a 1080p canvas; body is 32-40px, slide titles 56-64px. Reaching for
  a smaller size means the slide holds more than one idea.
- Switch slides with `visibility`/`opacity`/`pointer-events`, never `display`. Layout classes and
  the print rules both need `display`, so a deck built on it needs an `!important` override to print.
- Keep everything inside the file: no runtime `fetch`. Chromium rejects `fetch()` of a `file:` URL
  outright, so a deck that loads its content cannot be double-clicked.
- Decide the type scale, layout families, palette and slide budget before writing markup, and
  record them at the top of the file. Retrofitting a layout system costs every slide.
- One claim per slide, and the title states the claim. A noun-phrase title makes the audience wait
  for the point instead of hearing it.
- Never invent a figure to fill a chart or table. Leave the slot visible, say what is missing, and
  carry the window and as-of date in a visible caption rather than in the notes.
- Measure the rendered deck before claiming anything: `uv`-free `node scripts/deck_qa.mjs <deck>`
  reports overflow, clipping and sub-floor type per slide and exits non-zero on failure.
- Element overflow and container clipping are different signals and both are needed.
  `getBoundingClientRect` finds what crosses the frame; only `scrollHeight > clientHeight` proves an
  `overflow: hidden` box is actually cutting content.
- Read the rendered PNGs. The gate proves geometry, not that the slide says anything.
- Wait for fonts before screenshotting (`document.fonts.ready`, then `fonts.check` for the face you
  render with). A screenshot taken on fallback metrics has line breaks the audience never sees.
- Export with `printBackground: true` *and* `print-color-adjust: exact` in the deck CSS. The flag
  defaults to false and the print pipeline optimises colour independently; either alone can ship a
  white PDF.
- Let the deck's `@page` decide paper size and pass `preferCSSPageSize`; otherwise the export
  silently rescales onto Letter.
- Check exported page count against slide count. A page short means a slide grew past one page and
  the screen render hid it.
- Repair at most three rounds against the gate, then hand the findings over. A fourth round is
  reshaping the content to please a measurement.
- Speaker notes never reach the audience surface, and never state anything the source material did
  not contain. Mark unknowns as unknown instead of writing a plausible sentence to read aloud.
- Pick the presenter transport by delivery: a double-clicked deck paints an `about:blank` child
  window it owns; a served deck may use a second window with `?view=`, which needs an HTTP server.
- Namespace anything persisted by deck path. Every local file shares the single `file://` origin, so
  an unnamespaced `localStorage` key is shared with every other deck on the machine.
- Animate inside `@media (prefers-reduced-motion: no-preference)` and keep a visible focus ring on
  every control. A deck is driven from the keyboard by definition.
- Budget about one slide per minute and cut rather than shrink. Most decks land at 8-15 slides.
- Escape to a framework when the requirement, not the taste, demands it, and then use its feature
  instead of rebuilding it by hand: Marp for one-command PDF from Markdown, Slidev for
  magic-move/Monaco/recording/hosting or an editable PowerPoint copy from the same source, reveal.js
  for a mature runtime. Read `references/frameworks.md` for what each route costs and how it
  exports.
- Say what was verified and what was not. "Exported cleanly" without a render is a claim, not a result.

## Workflows

### build-deck

- [ ] Establish the brief: live or read alone, audience, length, whether the numbers exist, hard
      constraints. Missing answers change the layout, not just the words.
- [ ] Write the outline — one line per slide, each stating its claim — and confirm it before markup.
- [ ] Copy `assets/deck-shell.html` and set the canvas, type scale, palette tokens and layout
      families at the top of the file.
- [ ] Build slides against the budget, reusing layout families rather than composing each slide.
- [ ] Add speaker notes per slide inside the slide markup.
- [ ] Run `node scripts/deck_qa.mjs deck.html --out qa`.
- [ ] Read every PNG in `qa/`.
- [ ] Gate: **the gate exits 0, the PNG count equals the slide count, and each slide was read.**

### verify-and-export

- [ ] Run the gate first: exporting a deck that fails measurement just produces a broken PDF.
- [ ] Export with `node scripts/deck_qa.mjs deck.html --out qa --pdf`.
- [ ] Confirm the PDF page count equals the slide count.
- [ ] Sample the exported background (`pdftoppm -r 18 -f 1 -l 1 -singlefile deck.pdf page1`), since
      a white page is the signature failure.
- [ ] For a deck you cannot modify, export with decktape and an explicit slide bound.
- [ ] Gate: **page count matches, sampled pixels show the deck's own background, and every reported
      finding is either fixed or stated in the handover.**

### presenter-mode

- [ ] Choose the transport from how the deck is delivered, then implement only that one.
- [ ] Put notes in a container the audience path never renders, and keep the presenter preview
      rendering the same DOM as the deck.
- [ ] Write per-slide notes: purpose, two or three talking points, transition, planned duration.
- [ ] Add the live controls the room needs: timer, slide position, audience-window status, blackout.
- [ ] Rehearse once against the real windows, including closing the audience window and recovering.
- [ ] State in the handover which way the deck opens: a child-window transport presents from a
      double-click, a `?view=` second window needs the local server. The recipient cannot infer it.
- [ ] Gate: **notes are absent from the audience DOM, both windows agree on the current slide,
      closing the audience window is visible and recoverable on the presenter side, and the
      handover names the opening method the implemented transport actually supports.**

### adopt-existing-deck

- [ ] Render and measure before editing, so "what changed" has a baseline.
- [ ] Identify the runtime: a hand-written file, a Marp/Slidev/reveal project, or an export from
      somewhere else. The fix differs per runtime and guessing wastes a rebuild.
- [ ] Fix the failures the gate reports, not the ones you suspect.
- [ ] Re-measure and diff against the baseline render.
- [ ] Gate: **the reported findings are cleared, no previously clean slide regressed, and the deck
      still opens the way its owner opens it.**

## Topic router

| Topic | Read when | File |
|---|---|---|
| Stage, slide switching, self-containment, print shape | Building or repairing any single-file deck | `references/single-file-deck.md` |
| Canvas grid, type scale, layout families, image slots, density | Deciding or auditing how a slide looks | `references/layout-and-type.md` |
| Page budget, slide types, sequence, titles, what to cut | Turning source material into an outline | `references/deck-narrative.md` |
| Two-window transports, notes, timing, live recovery | Adding presenter mode or writing notes | `references/presenter-mode.md` |
| Measurement layers, determinism, PDF colour and paper, command paths | Verifying or exporting anything | `references/export-and-qa.md` |
| Marp, Slidev, reveal.js: sizing, overflow, notes, export | Choosing to leave the single-file route | `references/frameworks.md` |

## Output format

Report the artifact, what was measured, and what a reader still has to decide:

```
deck.html — 11 slides, 1920x1080
  verified: deck_qa.mjs 0 errors; 11/11 PNGs read; PDF 11 pages, background sampled #0b1020
  assumptions: Q3 figures from ci-metrics.csv, window 2026-07-01..2026-09-30
  open: slide 7 has no owner for the Windows runner item; placeholder left visible
  delivery: double-click deck.html; arrows or space to advance; P opens the presenter window
```

When a gate fails, name the gate and the finding instead of delivering with a caveat:

```
deck.html — NOT delivered
  gate: deck_qa.mjs
  failure: slide 4 list overflows the frame by 118px; slide 9 caption renders at 20px (floor 24px)
```

When the host cannot render, say so rather than implying verification:

```
deck.html — 9 slides, layout NOT verified (no browser available in this environment)
```

## Environment

```bash
cd <deck directory>                   # where deck.html lives, never inside this skill
npm install playwright                # or: copy scripts/package.json here, then npm install
npx playwright install chromium       # once per machine
```

`scripts/package.json` declares the dependency; install it beside the deck. `playwright-core`
ships its own `SKILL.md` files, so a `node_modules` inside a skill directory registers them as
extra skills in recursive scanners. `scripts/deck_qa.mjs` resolves playwright from the working
directory for that reason.

Optional: `poppler-utils` for `pdfinfo`/`pdftoppm`, `python3` for `python3 -m http.server`, and
`chromium` for the no-Node export fallback.

| File | Mode | Purpose |
|---|---|---|
| `scripts/deck_qa.mjs` | Run | Per-slide geometry measurement, per-slide PNG, optional PDF; non-zero exit on failure |
| `assets/deck-shell.html` | Run | Starting deck with the stage, switching, navigation, notes and print rules already correct |
