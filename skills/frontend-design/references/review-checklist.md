# UI review checklist

Terse by design. Each line is meant to be decidable by reading code, so a review can produce a
`path:line` for it. Walk the categories in order; the later ones (content handling, locale, touch)
are where the defects nobody looked for live.

Skip anything the project's own tooling already enforces, and say once that it was skipped.

## Contents

- [1. Accessibility](#1-accessibility)
- [2. Focus](#2-focus)
- [3. Forms](#3-forms)
- [4. Animation](#4-animation)
- [5. Typography](#5-typography)
- [6. Content handling](#6-content-handling)
- [7. Images and media](#7-images-and-media)
- [8. Performance](#8-performance)
- [9. Navigation and state](#9-navigation-and-state)
- [10. Touch and pointer](#10-touch-and-pointer)
- [11. Safe areas and layout](#11-safe-areas-and-layout)
- [12. Dark mode and theming](#12-dark-mode-and-theming)
- [13. Locale](#13-locale)
- [14. Hydration and client state](#14-hydration-and-client-state)
- [15. Hover and interactive states](#15-hover-and-interactive-states)
- [16. Copy](#16-copy)
- [Anti-patterns to flag on sight](#anti-patterns-to-flag-on-sight)

## 1. Accessibility

- Icon-only buttons carry `aria-label` or visually hidden text.
- Form controls have a `<label>` or `aria-label`.
- `<button>` for actions, `<a>` or the router link for navigation. Never `<div onClick>`.
- Custom interactive elements have keyboard handlers as well as a role and `tabIndex`.
- Images have `alt`, or `alt=""` when decorative.
- Decorative icons are `aria-hidden="true"`.
- Async updates (toasts, validation results, counts) land in a live region: `aria-live="polite"` or
  `role="status"`, `role="alert"` for errors.
- Semantic HTML before ARIA.
- Headings are hierarchical, one `h1`, no skipped levels; a skip link reaches the main content.
- Heading and anchor targets have `scroll-margin-top` so fixed chrome does not cover them.
- Meaningful media has captions, a transcript or a description; media controls work by keyboard;
  decorative media is hidden from assistive technology.
- `<html lang>` is set.
- Pointer targets are at least 24x24 CSS px, or satisfy a documented SC 2.5.8 exception.

## 2. Focus

- Every interactive element has a visible focus indicator.
- No `outline: none` or `outline-none` without a replacement in the same rule set.
- `:focus-visible` rather than `:focus`, so clicking does not leave a ring.
- Compound controls show group focus with `:focus-within`.
- Sticky headers, footers and overlays cannot cover the focused element.
- Focus moves into a dialog on open and returns to the trigger on close.
- No positive `tabindex`.

## 3. Forms

- Inputs have `autocomplete` and a meaningful `name`.
- Correct `type` (`email`, `tel`, `url`, `number`, `search`) and `inputmode` where needed.
- Paste is never blocked.
- Labels are clickable (`htmlFor`, or wrapping the control).
- `spellcheck={false}` on emails, codes, usernames and identifiers.
- Checkbox and radio share one hit target with their label, with no dead zone.
- Submit stays enabled until the request starts, then shows progress in place.
- Errors appear inline next to their field, connected by `aria-describedby`, with `aria-invalid` set.
- Focus moves to the error summary, or the first invalid field, after a failed submit.
- Placeholders show the expected pattern and end with `…`.
- `autocomplete="off"` only where a password manager would be wrong, never on auth fields.
- Unsaved changes warn before navigation.

## 4. Animation

- `prefers-reduced-motion` has a reduced variant, not just a disabled one.
- `transform` and `opacity` only.
- Never `transition: all`; properties are listed.
- `transform-origin` is set deliberately. SVG transforms go on a `<g>` with
  `transform-box: fill-box; transform-origin: center`.
- Animations are interruptible and respond to input mid-flight.
- Autoplaying motion over five seconds alongside other content has pause, stop or hide controls.
- Muted decorative loops stop under reduced motion.
- Hover motion is gated behind `(hover: hover) and (pointer: fine)`.

## 5. Typography

- `…` not `...`.
- Curly quotes in prose, not straight quotes.
- Non-breaking spaces in units, shortcuts and multi-word brand names: `10&nbsp;MB`, `⌘&nbsp;K`.
- Loading states end with `…`.
- `font-variant-numeric: tabular-nums` on number columns and updating values.
- `text-wrap: balance` on headings, `text-wrap: pretty` on body, to avoid widows and orphans.
- Buttons and inputs have `font: inherit`.
- Only loaded weights and styles are used; nothing relies on a synthesized italic or weight.

## 6. Content handling

- Text containers handle long content: truncation, line clamping, or `break-words`.
- Flex children that must truncate have `min-w-0`.
- Empty states are handled; an empty array or string never renders broken chrome.
- User-generated content is exercised at short, average and very long lengths.
- Long tokens use `overflow-wrap: anywhere`, not `word-break: break-all` on prose.
- Truncated values remain reachable in full, by pointer and by keyboard.

## 7. Images and media

- `<img>` has explicit `width` and `height`, or `aspect-ratio`.
- Below-fold images are `loading="lazy"`.
- The above-fold critical image has `fetchpriority="high"` and is not lazy-loaded.
- Compressed video instead of animated GIF, with a still fallback.
- `max-width: 100%` so an image cannot break its container.

## 8. Performance

- Lists over about 50 items are virtualized, or use `content-visibility: auto`.
- No layout reads during render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`,
  `scrollTop`).
- DOM reads and writes are batched, not interleaved.
- Uncontrolled inputs preferred; controlled ones are cheap per keystroke.
- `preconnect` to CDN and asset origins on the critical path.
- Critical fonts preloaded with `font-display: swap`.
- Third-party scripts are `async` or `defer`.
- High-frequency events are debounced or throttled.

## 9. Navigation and state

- The URL reflects state: filters, tabs, pagination, expanded panels.
- Links are real links, so modifier-click and middle-click work.
- Stateful UI is deep-linkable.
- Destructive actions have confirmation or an undo window, never immediate execution.
- Back navigation restores scroll position, filters and entered values.
- Focus moves to the main region after a client-side route change.
- The current location is visibly marked in navigation.

## 10. Touch and pointer

- `touch-action: manipulation` to remove the double-tap zoom delay.
- `-webkit-tap-highlight-color` set deliberately rather than left at the default.
- `overscroll-behavior: contain` in modals, drawers and sheets.
- During a drag: text selection disabled, dragged elements `inert`.
- Drag, swipe, pinch and path gestures have tap or click and keyboard alternatives.
- `autoFocus` sparingly: desktop only, one primary input, never on small screens.
- Adjacent targets have enough clear space that the 24 CSS px spacing test passes.

## 11. Safe areas and layout

- Full-bleed layouts use `env(safe-area-inset-*)`.
- No unwanted scrollbars: the overflowing content is fixed rather than hidden on an ancestor.
- Flex and grid do the layout, not JavaScript measurement.
- Content reflows at 320 CSS px with no two-dimensional scrolling.
- `100dvh` rather than `100vh` on mobile layouts.
- Fixed and sticky chrome reserves space for the content beneath it.

## 12. Dark mode and theming

- `color-scheme` on `<html>` so native controls and scrollbars follow the theme.
- `<meta name="theme-color">` matches the page background.
- Native `<select>` has explicit `background-color` and `color`.
- Contrast is checked independently in both themes.
- No raw hex or raw `z-index` in components.

## 13. Locale

- Dates and times through `Intl.DateTimeFormat`, never a hardcoded pattern.
- Numbers and currency through `Intl.NumberFormat`.
- Language detected from `Accept-Language` or `navigator.languages`, not from IP.
- Brand names, code tokens and identifiers wrapped in `translate="no"`.
- Layout survives strings roughly 40% longer than the English source.

## 14. Hydration and client state

- An input with `value` has `onChange`; otherwise use `defaultValue`.
- Date and time rendering is guarded against a server-client mismatch.
- `suppressHydrationWarning` appears only where it is genuinely unavoidable.

## 15. Hover and interactive states

- Buttons and links have a hover state on pointer devices.
- Hover, active and focus each read as more prominent than rest; disabled reads as less.
- Nothing is discoverable by hover alone.
- Disabled controls keep a legible label.
- Read-only is visually and semantically distinct from disabled.

## 16. Copy

- Active voice: "Install the CLI", not "The CLI will be installed".
- Consistent heading and button casing across the product.
- Numerals for counts: "8 deployments".
- Specific button labels: "Save API key", not "Continue".
- Error messages include the fix or the next step.
- Second person; avoid first person.
- No em dash or en dash in visible copy.
- No `→` appended to link or button text.
- No placeholder residue: `John Doe`, `Acme`, lorem text, `99.99%`.

## Anti-patterns to flag on sight

- `user-scalable=no` or `maximum-scale=1` in the viewport meta tag.
- `onPaste` with `preventDefault`.
- `transition: all`.
- `outline: none` with no `:focus-visible` replacement.
- Click-to-navigate without a real link element.
- `<div>` or `<span>` with a click handler.
- Images with no dimensions.
- Large arrays mapped with no virtualization.
- Form inputs with no label.
- Icon buttons with no accessible name.
- Hardcoded date or number formats.
- `autoFocus` with no justification.
- Animated GIF where compressed video is suitable.
- A gesture with no pointer and keyboard alternative.
- Positive `tabindex`.
- A single radius value used on every element.
- The same shadow under every card.

<!-- sources: vercel-wig, addy-frontend-ui, uiux-pro-max, w3c-wcag22, antfu-design, emil-animations -->
