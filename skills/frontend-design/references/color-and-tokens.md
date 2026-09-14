# Color and tokens

## Contents

- [Building the palette](#building-the-palette)
- [Semantic tokens](#semantic-tokens)
- [Dark mode](#dark-mode)
- [Contrast](#contrast)
- [Color is never the only signal](#color-is-never-the-only-signal)
- [Elevation and materiality](#elevation-and-materiality)
- [Checkable rules](#checkable-rules)

## Building the palette

Name 4-6 hex values with a role each, and derive them from the subject rather than from a palette
generator. A brief about brazed steel frames yields brass, paper, oxide; a brief about clinical
records yields something else entirely. That derivation is what makes a palette specific.

- **One accent.** Neutral base first, then one intentional accent. A second accent is almost always a
  decision nobody made. If a semantic color is needed (danger, success, warning), it is semantic, not
  a second brand accent.
- **Saturation under roughly 80%** unless the brand is genuinely loud.
- **One neutral temperature**, warm or cool, not both. Mixed neutrals make a page look slightly
  soiled in a way that is hard to diagnose.
- **Consistency lock.** Once the accent is chosen it applies across the whole page. A warm-grey page
  does not grow a blue CTA in section seven.
- **Off-black and off-white**, not `#000` and `#fff`. But note that near-black tinted values
  (`#0B0B0B`, `#111`) used *as* black, with a monospace label face and an acid accent, is itself one
  of the generated-look clusters. Off-black is a refinement, not a style.

## Semantic tokens

Components reference roles, never raw values. Raw hex in a component makes dark mode, theming and
rebranding impossible without a find-and-replace across the codebase.

```css
:root {
  /* Surfaces */
  --surface: #fbfbfa;
  --surface-raised: #ffffff;
  --border: rgb(0 0 0 / 0.10);

  /* Text */
  --text: #14120f;
  --text-muted: #5b5751;

  /* One accent, plus semantics */
  --accent: #1f3a34;
  --accent-contrast: #ffffff;
  --danger: #a6402a;

  /* Named layers, so no raw z-index appears in components */
  --z-header: 60;
  --z-popover: 70;
  --z-dialog: 100;
}
```

Rules that make a token system hold up:

- Name by role (`--surface-raised`, `--text-muted`), not by appearance (`--grey-100`). Appearance
  names stop being true the moment the theme changes.
- Name the z-index layers too. Raw `z-index` values in components are how stacking bugs are born.
- Spacing is a token scale as well: pick 4px or 8px increments and stay on it. `padding: 13px` is the
  signal that nobody is using the scale.
- Prefer `color-mix()` or relative color syntax over hand-mixed hover shades so states stay tied to
  their base token.

## Dark mode

Design both themes together. A dark theme is not an inverted light theme.

- Set `color-scheme: dark` (or `light dark`) on the root. Without it, native scrollbars, form
  controls and the browser's own UI stay light and look broken against a dark page.
- Set `<meta name="theme-color">` to match the page background so the mobile browser chrome does not
  clash.
- Native `<select>` needs explicit `background-color` and `color`; on Windows dark mode the option
  list otherwise renders unreadable.
- Dark surfaces use desaturated and lighter tonal variants of the brand color, not the same
  saturation on a dark ground. Highly saturated accents vibrate against dark backgrounds.
- Re-check contrast independently in each theme. A pair that passes on white frequently fails on
  `#111`.
- Image and media edges need a light outline in dark mode and a dark one in light mode, at low
  opacity, never a tinted neutral (which reads as dirt on the edge).
- **One theme per page.** Sections do not invert. A warm-paper section between two near-black
  sections reads as a styling mistake, not as a change of pace, and background tints within the same
  family (`zinc-950` beside `zinc-900`) are how the page varies instead. A full theme switch is
  allowed once per page where the brief asks for that device, and only if it spans the full bleed and
  carries a real transition. A light band constrained to the content container, with the dark ground
  showing either side, is the layer bug this rule exists to catch.
- Where a component system owns the theme, set it once at the page root and let no section override
  it.

## Contrast

Numbers are from WCAG 2.2. The criterion ids, levels and exceptions live in this skill's
accessibility reference, listed in the topic router.

| What | Ratio | Level |
|---|---|---|
| Body text | 4.5:1 | AA (SC 1.4.3) |
| Large text (18.66px bold, or 24px) | 3:1 | AA (SC 1.4.3) |
| UI component boundaries and state indicators, meaningful graphics | 3:1 | AA (SC 1.4.11) |
| Body text, enhanced | 7:1 | AAA (SC 1.4.6) |

Practical traps:

- A small label in the accent color on a light surface usually fails. Accent-on-white at 0.75rem is
  the single most common contrast defect in generated pages.
- White text on a gradient must pass against the **lightest** stop, not the average.
- Disabled controls are exempt from SC 1.4.3, but a disabled control nobody can read is still a
  usability defect. Use reduced opacity plus a semantic attribute, and keep the label legible.
- Placeholder text is content. If the form relies on it, it needs to pass.

## Color is never the only signal

Functional color always pairs with a second channel: an icon, a text label, a border weight, or a
pattern. This covers color-vision deficiency and also grayscale printing and low-quality displays.

- Required fields: a visible marker plus a programmatic one, not red alone.
- Error and success states: icon plus text plus color.
- Links inside prose: distinguishable without color (underline, weight).
- Charts: patterns or direct labels in addition to hue, and never a red/green-only pair.

## Elevation and materiality

- Use a card only when elevation communicates real hierarchy. Otherwise group with a `border-t`, a
  divider, or whitespace.
- Dense, structural or devtools-like surfaces read better flat with hairline borders. Genuinely
  floating surfaces (menus, popovers, marketing cards) read better with a layered, background-tinted
  shadow, because a shadow adapts to any background and a solid border does not.
- One shadow scale, tinted toward the background hue. The same `rgba(0,0,0,.1)` under every element
  is a generated-look tell and also costs paint time.
- Never animate `box-shadow` for hover depth across a long list; cross-fade a pseudo-element or swap
  opacity instead.
- Blur signals dismissible background (a sheet or modal is open). It is not decoration.

## Checkable rules

- Raw hex or `rgb()` inside a component.
- Raw `z-index` number in a component.
- Off-scale spacing value.
- A second brand accent that is not a semantic color.
- Missing `color-scheme` on a dark theme.
- Native `<select>` without explicit colors.
- `#000` or `#fff` used as the surface or text color.
- Required, error or success state expressed by color alone.
- A section whose theme is inverted relative to the page, with no brief asking for the switch.
- Contrast below the table above, checked in both themes.

<!-- sources: anthropic-frontend-design, vercel-wig, addy-frontend-ui, antfu-design, w3c-wcag22, uiux-pro-max -->
