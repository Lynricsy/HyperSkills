# Accessibility

Verified against: WCAG 2.2 (W3C Recommendation), read from <https://www.w3.org/TR/WCAG22/>.

Every number here comes from the specification text, not from a secondary source. Several widely
circulated skills and checklists state the wrong level or the wrong value for target size; when a
claim about accessibility is made, cite the criterion id and its level.

## Contents

- [The numbers that get quoted wrong](#the-numbers-that-get-quoted-wrong)
- [Criterion quick table](#criterion-quick-table)
- [Target size in practice](#target-size-in-practice)
- [Focus](#focus)
- [Keyboard](#keyboard)
- [Names, roles and semantics](#names-roles-and-semantics)
- [Live regions](#live-regions)
- [Motion and moving content](#motion-and-moving-content)
- [Text and zoom](#text-and-zoom)
- [Testing](#testing)
- [Checkable rules](#checkable-rules)

## The numbers that get quoted wrong

**Target size.** SC 2.5.8 Target Size (Minimum) is **Level AA** and requires the pointer target to
be **at least 24 by 24 CSS pixels**. SC 2.5.5 Target Size (Enhanced) is **Level AAA** and requires
**44 by 44 CSS pixels**. 44x44 is therefore not the AA floor. The 44 figure also appears as 44pt in
Apple's Human Interface Guidelines and as 48x48dp in Material Design; those are platform guidance,
not WCAG conformance. WCAG 2.1 contains no Level AA target-size criterion at all, so a checklist
titled "WCAG 2.1 AA" that demands 44x44 is wrong twice over.

Design-system advice that follows from this: ship two tokens, a `24px` hard floor that nothing may go
below, and a `44px` default target. Dropping to the floor is an exception that gets documented per
component and must also satisfy the spacing exception below.

Unit trap: CSS `44pt` is not `44px`. In CSS, 1pt = 4/3px, so `44pt` is about `58.67px`, and Apple's
pt is a UIKit logical point, unrelated to the CSS unit. On the web, always write `px`.

**Contrast.** 4.5:1 for text, 3:1 for large-scale text, 3:1 for non-text UI. 7:1 is the AAA level,
not the AA one.

## Criterion quick table

| SC | Name | Level | Requirement |
|---|---|---|---|
| 1.4.3 | Contrast (Minimum) | AA | Text 4.5:1; large-scale text and images of large text 3:1. Incidental, inactive-component, decorative and logotype text exempt |
| 1.4.4 | Resize Text | AA | Text resizable to 200% without loss of content or function |
| 1.4.6 | Contrast (Enhanced) | AAA | Text 7:1; large-scale text 4.5:1 |
| 1.4.10 | Reflow | AA | No two-dimensional scrolling at 320 CSS px width (or 256 CSS px height for horizontal-scrolling content) |
| 1.4.11 | Non-text Contrast | AA | UI component and state information, and meaningful parts of graphics, 3:1 against adjacent colors |
| 1.4.12 | Text Spacing | AA | No loss of content when line-height is set to 1.5x font size, paragraph spacing 2x, letter spacing 0.12x, word spacing 0.16x |
| 1.4.13 | Content on Hover or Focus | AA | Hover and focus content is dismissible, hoverable and persistent |
| 2.2.2 | Pause, Stop, Hide | A | Moving, blinking, scrolling or auto-updating content that lasts more than 5 seconds needs a control |
| 2.3.3 | Animation from Interactions | AAA | Motion animation triggered by interaction can be disabled unless essential |
| 2.4.7 | Focus Visible | AA | The keyboard focus indicator is visible |
| 2.4.11 | Focus Not Obscured (Minimum) | AA | The focused component is not entirely hidden by author-created content |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA | The focused component is not hidden at all |
| 2.4.13 | Focus Appearance | AAA | Indicator area at least equal to a 2 CSS px perimeter of the component, at 3:1 between focused and unfocused states |
| 2.5.5 | Target Size (Enhanced) | AAA | 44 by 44 CSS px |
| 2.5.7 | Dragging Movements | AA | Every dragging action has a single-pointer alternative unless essential |
| 2.5.8 | Target Size (Minimum) | AA | 24 by 24 CSS px, with five exceptions (below) |
| 3.2.6 | Consistent Help | A | Repeated help mechanisms appear in the same relative order across a page set |
| 3.3.7 | Redundant Entry | A | Information already entered in the same process is auto-populated or selectable |
| 3.3.8 | Accessible Authentication (Minimum) | AA | No cognitive function test required; allow paste and password managers |
| 3.3.9 | Accessible Authentication (Enhanced) | AAA | Stricter form of 3.3.8 |

## Target size in practice

The SC 2.5.8 exceptions, in the specification's own terms:

- **Spacing.** An undersized target passes if a 24 CSS px diameter circle centered on its bounding
  box does not intersect another target, or another undersized target's circle. In arithmetic: a
  20x20 icon button with 4px of clear space passes; the same buttons flush against each other fail.
- **Equivalent.** The same function is available through another control on the same page that does
  meet the size.
- **Inline.** The target is inside a sentence or block of text, or its size is constrained by the
  line-height of non-target text.
- **User Agent Control.** The browser determines the size and the author has not modified it (native
  date pickers, scrollbars).
- **Essential.** A particular presentation is essential, or legally required (map pins, dense data
  visualizations).

The requirement is independent of zoom: "the user can pinch to zoom" is not a defense. It also
applies to all pointer inputs, not only touch, so mouse users with tremor benefit too.

Inline links in prose are exempt from both 2.5.8 and 2.5.5. Forcing extra height on them damages
line rhythm; increasing line-height is the better response.

## Focus

- Every interactive element keeps a visible indicator. Use `:focus-visible`, not `:focus`, so a
  mouse click does not leave a ring behind.
- `outline: none` (or `outline-none`) is only acceptable when a replacement indicator is defined in
  the same rule set. Anything else is an SC 2.4.7 failure.
- Compound controls (an input with an adjacent button) show group focus with `:focus-within`.
- Sticky headers, footers, banners and overlays must not cover the focused element (SC 2.4.11). Add
  `scroll-margin-top` to headings and anchor targets so in-page navigation does not land behind
  fixed chrome.
- Move focus deliberately: into a dialog on open, back to the trigger on close, to the error summary
  after a failed submit, and to the main region after a client-side route change.
- Modals trap focus while open. Nothing else should.
- `tabindex` is `0` or `-1` only. A positive `tabindex` reorders the whole document.

## Keyboard

- Focus order follows visual order.
- `<button>` for actions, `<a>` or the router's link component for navigation. A `<div>` with a
  click handler is not focusable, has no role, and does not respond to Enter or Space.
- If a custom control is unavoidable it needs a role, `tabIndex={0}`, and key handling: Enter and
  Space to activate, Escape to dismiss, arrow keys where the role implies them.
- No keyboard traps: focus can always leave a component.
- A skip link to the main content, visible at least on focus.
- Every drag, swipe, pinch or path gesture has a single-pointer and keyboard alternative (SC 2.5.7),
  unless the gesture itself is essential.
- Do not override system or assistive-technology shortcuts.

## Names, roles and semantics

- Semantic HTML before ARIA. `<button>`, `<a>`, `<label>`, `<table>`, `<nav>`, `<dialog>` carry role,
  state and keyboard behavior for free; ARIA carries none of it.
- Icon-only controls need an accessible name (`aria-label`, or visually hidden text).
- Decorative icons and images: `aria-hidden="true"` and `alt=""`. A decorative icon that sits beside
  its own visible label should be hidden, not labelled twice.
- Images that carry meaning need `alt` describing the meaning, not the file.
- Form controls need a `<label>` (or `aria-label` when no visible label exists). A visible label is
  preferable; a placeholder is not a label.
- One `h1`, and heading levels never skipped.
- `<html lang>` set, and `lang` on any element in another language.
- Tables use `<th>` with `scope`. Sortable columns expose `aria-sort`.
- Brand names, code tokens and identifiers get `translate="no"` so machine translation does not
  mangle them.
- Media that conveys information needs captions, a transcript, or a description, and its controls
  need keyboard support.

## Live regions

| Mechanism | Behavior | Use for |
|---|---|---|
| `aria-live="polite"` | Announced at the next pause | Saved, updated, count changed |
| `role="status"` | Equivalent to polite | Status messages |
| `aria-live="assertive"` | Announced immediately, interrupting | Time-sensitive alerts |
| `role="alert"` | Equivalent to assertive | Errors |

Announce a change as a complete phrase ("3 items selected"), not as a bare number, and do not move
focus to do it. Use one region per concern; `aria-atomic` only where the whole message must be
re-read. Toasts announce politely and never steal focus.

## Motion and moving content

- Respect `prefers-reduced-motion`: fewer and gentler, not zero. Keep transitions that aid
  comprehension (opacity, color); remove movement and position change.
- Carousels and auto-updating content need pause, stop or hide controls, and stop on focus.
- Nothing flashes more than three times per second.

## Text and zoom

- Text resizes to 200% without loss of content or function (SC 1.4.4).
- The layout survives the SC 1.4.12 text-spacing overrides; a fixed-height row with vertically
  centered text is the usual failure.
- Never disable zoom. `user-scalable=no` and `maximum-scale=1` in the viewport meta tag are the
  canonical anti-pattern.
- Support the platform's text-size preference and avoid truncation as text grows.

## Testing

Automated tooling catches a subset. Treat a clean automated run as necessary, not sufficient.

```bash
npx axe-core            # programmatic; 4.8+ implements the WCAG 2.2 target-size rule
npx pa11y <url>         # CLI checker
```

- Lighthouse's tap-target audit uses an older 48px heuristic and is not a SC 2.5.8 verdict.
- Manual passes that find what tooling cannot: tab through the whole page; use it at 200% zoom and at
  320 CSS px width; toggle reduced motion; read it with a screen reader (VoiceOver, NVDA, Orca);
  check both color themes.

## Checkable rules

- Icon-only control with no accessible name.
- Form control with no label.
- `<div>` or `<span>` with a click handler.
- `outline: none` with no replacement.
- `:focus` used where `:focus-visible` is meant.
- Image with no `alt`, or decorative image without `alt=""`.
- Positive `tabindex`.
- Heading level skipped, or more than one `h1`.
- Async status change with no live region.
- Zoom disabled in the viewport meta tag.
- Target under 24x24 CSS px with no applicable exception.
- Gesture with no single-pointer alternative.
- Missing `<html lang>`.

<!-- sources: w3c-wcag22, vercel-wig, addy-frontend-ui, uiux-pro-max, wshobson-a11y -->
