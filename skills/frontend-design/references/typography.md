# Typography

Type carries most of an interface's personality, and most typographic defects are a handful of
repeatable mistakes rather than taste disagreements.

## Contents

- [Choosing families](#choosing-families)
- [Scale, weight and hierarchy](#scale-weight-and-hierarchy)
- [Measure, leading and wrapping](#measure-leading-and-wrapping)
- [Numbers and technical values](#numbers-and-technical-values)
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
- `...` where `…` belongs; straight quotes in prose.
- Loading state text that does not end in `…` (`Loading…`, `Saving…`).

<!-- sources: anthropic-frontend-design, vercel-wig, addy-frontend-ui, antfu-design, uiux-pro-max -->
