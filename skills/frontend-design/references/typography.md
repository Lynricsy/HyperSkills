# Typography

Type carries most of an interface's personality, and most typographic defects are a handful of
repeatable mistakes rather than taste disagreements.

## Contents

- [Choosing families](#choosing-families)
- [Scale, weight and hierarchy](#scale-weight-and-hierarchy)
- [Measure, leading and wrapping](#measure-leading-and-wrapping)
- [Numbers and technical values](#numbers-and-technical-values)
- [CJK text](#cjk-text)
- [Loading and rendering](#loading-and-rendering)
- [Checkable rules](#checkable-rules)

## Choosing families

One family, or two that are clearly distinct. A display face and a body face from the same
superfamily read as one voice with two weights, which is usually the point; two unrelated sans faces
read as an accident.

Do not reach for the family you would reach for on any other project. Three faces have become reflex
defaults and now signal "generated" on their own: **Inter** as the sans, **Fraunces** and
**Instrument Serif** as the display serif. They are all good typefaces; the problem is that they get
chosen without a reason. Write one sentence of reason per family in the design plan, and if the only
reason is "it looks modern", choose again from the subject's own world (industrial, editorial,
scientific, civic, vernacular signage).

Serif discipline: serif is not the default for "creative" or "premium". Use one when the brand names
one, or when the aesthetic is genuinely editorial, luxury, or publication, and say which.

Monospace is for technical values (paths, hashes, counters, timestamps, percentages, geometry
tables), not for body text and not as a decorative label face. A monospace face on small data labels
is one of the template-chrome tells.

## Scale, weight and hierarchy

Set a scale and stay on it. A conventional set of steps is 12 / 14 / 16 / 18 / 24 / 32 / 48, but the
specific numbers matter less than having a fixed set. Off-scale values (`13px`, `2.3rem`) are the
signal that the scale is being improvised.

Control hierarchy with weight and color before scale:

- Headings: 600-700. Body: 400. Small labels: 500.
- One `h1` per page. Never skip heading levels, and never use a heading style for non-heading content.
- An enormous `h1` that only shouts is weaker than a moderate `h1` with real contrast against its
  surroundings.

Emphasis inside a headline uses italic or bold of the same family. Switching color, family, or style
for a single word is a tell.

Fluid type: prefer `clamp()` over fixed heading sizes so a `3.5rem` headline cannot force a
horizontal scrollbar at 320 CSS px.

## Measure, leading and wrapping

- Body measure under about 80 characters. Serif body text tolerates slightly longer lines; give it
  slightly more leading than a sans at the same size.
- Practical targets: 35-60 characters on small screens, 60-75 on desktop. `max-width: 65ch` is a
  reasonable default container for prose.
- Body line-height 1.5-1.75. Keep the platform's default letter-spacing on body text; tracked body
  copy is harder to read, and heavy tracking belongs to small all-caps labels only if you are using
  those at all.
- Minimum 16px body text on small screens. Below that, iOS zooms the viewport on focus.
- Headings: `text-wrap: balance` to prevent widows. Body: `text-wrap: pretty` to reduce orphans.
  Both degrade to normal wrapping where unsupported, so no fallback is needed. Do not force final
  words together with blanket non-breaking spaces.
- Non-breaking spaces belong in units and shortcuts that must not split: `10&nbsp;MB`, `⌘&nbsp;K`,
  two-word brand names.
- Prefer wrapping to truncation. When truncating, use an ellipsis and keep the full value reachable
  (a `title` attribute at minimum, better a tooltip or expand affordance that also works by
  keyboard).
- Long tokens (URLs, ids, user-generated strings) need `overflow-wrap: anywhere` and a shrinkable
  flex or grid text child. Do not apply `word-break: break-all` to normal prose. In flexbox, the text
  child also needs `min-w-0` (`min-width: 0`) or it refuses to shrink and overflows its parent.

## Numbers and technical values

- Any number that updates in place, and any column of numbers being compared, uses
  `font-variant-numeric: tabular-nums`. Proportional figures shift the layout on every tick.
- Pair `tabular-nums` with the monospace family for technical metadata; keep proportional figures in
  prose.
- Format with `Intl.NumberFormat`, never a hand-rolled pattern. `1234567` unformatted next to
  `99.99%` is both a locale bug and a placeholder tell.

## CJK text

Most of the rules above were written for Latin text. Chinese and Japanese pages break them in
specific ways, and the source rarely shows it: render at the target width with the fonts the
audience actually has.

- **Name a CJK family in the stack.** A Latin-only stack (`"Inter", Arial, sans-serif`) leaves every
  Han glyph to whatever each OS substitutes, so the page has a different Chinese face, weight and
  width on every platform. Latin face first so letters and figures use it, then CJK families matching
  the page `lang` (SC, TC, HK or JP variants), then the generic:
  `"Inter", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif`.
- **Check weights on a mixed line.** The browser picks the nearest weight each fallback face has, so a
  light Latin face can sit next to regular-weight Han glyphs. Look at one line mixing Chinese, figures
  and a Latin word, and compare stem weight and baseline.
- **Size and leading start higher** `[community]`. Han glyphs fill the em square, so Latin leading
  looks cramped. Starting points: reading pages 16-18px body, product UI 14-16px, dense all-day
  tools 13-14px; body line-height 1.6-1.75. Multi-line Chinese below about 1.4 reads as a block. These
  are starting points, not WCAG requirements.
- **Headings at 1.2-1.35, with content-driven height.** Display leading copied from Latin posters
  (0.9-1.0) makes Han lines touch, because there are no ascenders or descenders leaving room. Never fix
  a heading's height to its expected line count; it wraps differently per width and per font.
- **No tracking on Han text.** Adjacent Han characters are set solid `[official]` (W3C CLREQ).
  Negative letter-spacing collides glyphs; tracked body text stops reading as words.
- **Line breaks: body flows, display lines need hands.** Breaking between any two Han characters is
  the normal CJK line-break rule (`word-break: normal`), so ordinary body wrapping is not a defect.
  The care belongs to headings and short display lines: `text-wrap: balance` and `pretty` reduce a
  one- or two-character last line but do not remove it; keep a number with its unit (`38&nbsp;秒`, or
  a short `nowrap` span) and a fixed phrase whose split would misread together, and break at phrase
  boundaries, checked at every supported width.
- **Measure in characters.** Past about 45 Han characters per line, body text gets hard to track
  `[community]`.

## Loading and rendering

- `font-display: swap` avoids invisible text. Reserve the space so the swap does not shift layout.
- Preload only the faces used above the fold, and add `<link rel="preconnect">` for the font origin.
  Preloading every weight is slower than preloading none.
- Load the weights and styles actually used. Requesting `400;600;800` and then rendering
  `font-weight: 700` or `font-style: italic` makes the browser synthesize the face, which looks
  visibly wrong (smeared italics, wrong stem weights).
- Give buttons and inputs `font: inherit`. Without it they render in the user agent's default family
  at about 13.3px, which is the reason a hero CTA sometimes looks absurdly small next to its own
  padding.
- Apply font smoothing at the root only where it helps (macOS); do not scatter it per component.

## Checkable rules

These are the ones worth flagging in a review with a `path:line`:

- Off-scale font size or spacing value.
- More than two families, or a third family used once.
- Body measure over ~80 characters with no `max-width`.
- Body text below 16px on small screens.
- A heading level skipped, or more than one `h1`.
- A single word in a headline switched to another family or color.
- Updating numbers without `tabular-nums`.
- Button or input without `font: inherit`.
- A synthesized italic or weight (style used but not loaded).
- CJK page: no CJK family in the stack, Han body line-height under about 1.4, a fixed-height or
  sub-1.2-leading Chinese heading, letter-spacing on Han text, a number split from its unit in a
  heading or display line. Ordinary body wrapping between Han characters is not a finding.
- `...` where `…` belongs; straight quotes in prose.
- Loading state text that does not end in `…` (`Loading…`, `Saving…`).

<!-- sources: anthropic-frontend-design, vercel-wig, addy-frontend-ui, antfu-design, uiux-pro-max, oil-ui, w3c-clreq -->
