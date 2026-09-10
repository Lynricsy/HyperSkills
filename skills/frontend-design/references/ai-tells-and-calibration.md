# Generated-look calibration

The traits below are what current models reach for when they try to "look designed". Each one is
legitimate for some brief. The problem is that they arrive as defaults rather than choices, and they
arrive whatever the subject is. Where the brief pins an axis down, follow the brief exactly, including
when it asks for one of these looks. Where the brief leaves an axis free, do not spend that freedom
on a default.

## Contents

- [The five clusters](#the-five-clusters)
- [Palette, radius and elevation tells](#palette-radius-and-elevation-tells)
- [Composition tells](#composition-tells)
- [Text and data tells](#text-and-data-tells)
- [Decoration tells](#decoration-tells)
- [Motion tells](#motion-tells)
- [The cliché gate](#the-cliche-gate)
- [Design read and dials](#design-read-and-dials)

## The five clusters

Whole looks, not single properties. If a plan matches a cluster on two or more axes, treat it as a
default until the brief justifies it.

1. **Warm cream editorial.** Background near `#F4F1EA`, high-contrast serif display face, terracotta
   or warm-clay accent near `#D97757`. That accent is a well-known assistant-interaction color, so on
   someone else's brief it reads as a fingerprint rather than a choice.
2. **Near-black with one acid accent.** Tinted near-black surface (`#0B0B0B`, `#111`) plus a single
   bright acid-green or vermilion highlight, applied to every interactive thing on the page.
3. **Broadsheet.** Hairline rules everywhere, zero border-radius, dense newspaper columns, all-caps
   section rules. Correct for a publication, arbitrary for a product.
4. **The card kit.** Content chopped into identically sized rounded cards, one radius on everything
   regardless of hierarchy, the same soft grey shadow (`rgba(0,0,0,.1)`) under each, gradient washes
   as decoration.
5. **Template chrome.** The set that appears whatever the subject: a tracked-out ALL-CAPS eyebrow
   above every heading, meta strings joined with middle dots (`A · B · C`), labels built as
   `WORD — fragment` with a spaced dash, tinted near-black standing in for black, a monospace face
   for small data labels, and `→` appended to link and button text.

## Palette, radius and elevation tells

| Trait | Why it is a tell | Instead |
|---|---|---|
| Purple, indigo or violet as the reflex accent | The "visually safe" default; every generated app lands here | One accent chosen from the subject's own materials or brand |
| Gradient as decoration (mesh, wash, gradient text on large headings) | Noise that carries no information and clashes with most systems | Flat surfaces; gradient only where it encodes something |
| Neon or outer glow | Reads as a demo, not a product | Inner border, or a shadow tinted toward the background hue |
| Pure `#000` or `#fff` | No real surface is either | Off-black and off-white |
| Two or more accents | Signals that nobody decided | One accent, saturation under roughly 80% unless the brand is loud |
| Warm and cool greys mixed | The page looks slightly dirty and nobody can say why | One neutral temperature |
| A single radius on everything (`rounded-2xl` everywhere) | Maximum rounding signals "friendly" and destroys the radius hierarchy real designs use | One radius scale; nested radii concentric (outer = inner + padding) |
| The same layered shadow under every card | Depth that competes with content and costs paint time on weak devices | Hairline borders on dense or structural surfaces, layered background-tinted shadows on genuinely floating ones |
| Pure-black drop shadows on light surfaces | Reads as grime rather than elevation | Tint the shadow toward the background hue |

## Composition tells

- **Centered hero over a dark gradient.** The single most common generated layout. Once variance is
  above about 4, reach for a split, a left-aligned block with an asset, or asymmetric whitespace.
  Centering is right for editorial or manifesto pages where the words are the design.
- **Three equal feature cards**, then the same left-image / right-text block repeated down the page.
  Vary the layout family per section instead.
- **Uniform card grids** as the default container. Grids ignore information priority. Group with a
  `border-t`, a divider, or whitespace when there is no real elevation to express. At high density,
  drop card containers entirely and separate rows with hairlines.
- **Oversized padding everywhere.** Equal generous padding removes hierarchy and wastes the viewport.
  Use one spacing scale and vary within it.
- **Numbered markers** (`01 / 02 / 03`) on content that is not a sequence. Check the content really
  is stepped or chronological before numbering it.
- **Structure as decoration.** Outlines, borders, eyebrows, dividers and labels should each encode
  something about the content. If removing one loses no information, remove it.
- **Oversized H1 as the only hierarchy device.** Control hierarchy with weight and color first; scale
  is the blunt instrument.
- **Fake product UI built from `<div>` rectangles** (mock terminals, mock dashboards, mock task
  lists). Use a real screenshot, a real component preview, or nothing.

## Text and data tells

- **Em dash (U+2014) and en dash (U+2013) in visible copy.** The most reliable single-character tell,
  and trivially checkable. Restructure instead: period, comma, parentheses, colon, line break, or a
  separate column. Ranges use a hyphen (`2018-2026`, `40-80k`).
- **Generic names.** `John Doe`, `Jane Doe`. Use plausible, locale-appropriate names.
- **Fake-perfect numbers.** `99.99%`, exactly `50%`, `1234567`. Use organic values, format them for
  the locale, or label the data as sample data. Do not claim engineering precision the product does
  not claim.
- **Startup-slop brand names.** `Acme`, `Nexus`, `SmartFlow`. Invent something contextual.
- **Filler verbs.** `Elevate`, `Seamless`, `Unleash`, `Next-Gen`, `Revolutionize`. Use concrete verbs
  that name the action.
- **Placeholder body copy.** Lorem-style text hides the wrapping, truncation and overflow problems
  real content exposes. Write realistic content at realistic lengths, including one very long case.
- **Straight quotes** where the copy is prose, and `...` where `…` belongs.
- **Accenting one word in a headline** by switching it to italic, bold, or another color. Emphasize
  with weight or italic of the same family; never splice a serif word into a sans headline.
- **All-caps labels** as the standard label treatment, and typographic labels stacked above content
  that already says what it is.

## Decoration tells

- Decorative status dots before every nav item, list row or badge. A colored dot is for real
  semantic state, used sparingly.
- Scroll cues (`Scroll`, `scroll to explore`, animated wheels). People know how to scroll.
- Section-number eyebrows (`00 / INDEX`, `001 Capabilities`).
- Version stamps on a marketing page (`v1.4.2`, `Build 0048`, `last sync 4s ago`). Those are
  devtools fixtures.
- Locale, time or weather strips (`Lisbon 14:23, 18C`) on pages that are not about place or time.
- The middle dot as the universal separator. At most one per metadata line.
- Custom mouse cursors.
- Generic avatar glyphs (the default user silhouette, the SVG "egg").

## Motion tells

- Fade-and-slide-up entrance on every section, and a hover transition on every card. Scattered
  effects read as generated; one orchestrated moment lands.
- Infinite decorative loops with no purpose.
- Motion that is not a response to an action. Motion answering a person's action (opening, expanding,
  confirming) is welcome because it shows what changed. Non-triggered motion needs a reason.

## The cliché gate

Run this before writing any component code, and again during self-critique.

1. Read the design plan back as if it were someone else's.
2. For every axis (palette, type, layout family, radius, elevation, motion, copy voice), ask: did the
   brief decide this, or did the default decide it?
3. For each axis the default decided, either revise it or write one sentence justifying it from the
   brief.
4. Ask whether a similar prompt with a different subject would have produced the same plan. If yes,
   the plan is a template.
5. Say what changed and why. The revision note is part of the deliverable, not internal monologue.
6. Then remove one accessory. There is almost always one element carrying no load.

## Design read and dials

The plan starts with one line:

```text
Reading this as: <kind> for <audience>, with a <vibe> language, leaning toward <aesthetic family>.
```

`kind` is one of: devtools panel, dashboard, app shell, landing page, portfolio, docs, editorial,
marketing section. `audience` decides the aesthetic, not personal taste: maintainers and power users
want dense and keyboard-first, first-time visitors want guided and spacious. Hard constraints
(accessibility-first audiences, public sector, regulated industries, trust-first commerce, products
for children) override aesthetic preference.

Then set three dials, 1 to 10:

| Dial | 1 | 10 |
|---|---|---|
| VARIANCE | perfectly symmetric | asymmetric and artsy |
| MOTION | static | cinematic, physics-driven |
| DENSITY | airy gallery | packed cockpit |

| Baseline | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| Tooling: devtools, dashboards, app shells | 2-3 | 2-3 | 7-9 |
| Marketing: landing, portfolio, product pages | 7-8 | 5-7 | 3-4 |

What the dials drive:

- VARIANCE 1-3 symmetric grids and equal padding; 4-7 offset headers and varied aspect ratios; 8-10
  asymmetric grids and large empty zones. High-variance layouts still collapse to one column on small
  screens.
- MOTION 1-3 hover and active states only; 4-7 CSS transitions on transform and opacity; 8-10
  scroll-driven choreography. Anything above 3 needs a `prefers-reduced-motion` variant.
- DENSITY 1-3 large section gaps; 4-7 standard app spacing; 8-10 tight padding, hairline separators,
  monospace with tabular figures for all numbers.

If the brief is genuinely ambiguous, ask exactly one question. If it can be inferred, state the read
and proceed.

<!-- sources: anthropic-frontend-design, addy-frontend-ui, antfu-design, leonx-taste, emil-animations -->
