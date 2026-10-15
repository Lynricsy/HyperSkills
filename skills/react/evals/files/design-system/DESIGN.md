---
name: Ledgerline
colors:
  canvas: "#ffffff"
  ink: "#16181d"
  ink-muted: "#5b6170"
  primary: "#0f5bd8"
  primary-pressed: "#0a45a6"
  on-primary: "#ffffff"
  hairline: "#e4e6eb"
  band: "#f5f6f8"
  danger: "#c4321c"
typography:
  display-lg: { family: "Söhne (licensed) - substitute Inter", size: 48px, weight: 500, line-height: 1.1, tracking: -1px }
  title-md: { family: Inter, size: 20px, weight: 500, line-height: 1.3, tracking: -0.2px }
  body: { family: Inter, size: 15px, weight: 400, line-height: 1.55 }
  caption-upper: { family: Inter, size: 12px, weight: 500, tracking: 1.5px, transform: uppercase }
rounded:
  xs: 4px    # small accents, checkbox
  sm: 6px    # menu items
  md: 8px    # buttons, inputs, selects, tabs
  lg: 12px   # cards, dialogs
  xl: 16px   # hero containers, toasts
  pill: 9999px # badges
components:
  button-primary: { fill: primary, text: on-primary, height: 40px, radius: md }
  text-input: { height: 40px, border: hairline, radius: md }
---

# Ledgerline

## Elevation

Hairline-only. Surfaces are separated by 1px `hairline` borders. No drop shadows
on inputs, buttons or cards; only popovers and dialogs get
`0 1px 2px rgb(22 24 29 / 0.06), 0 8px 24px rgb(22 24 29 / 0.08)`.

## Do's and Don'ts

- Do keep every control (buttons, inputs, selects, toggles, tabs) at 40px.
- Do darken the primary button on press only; there is no hover color change.
- Don't use a radius outside the scale above.
- Don't set display type bold.
