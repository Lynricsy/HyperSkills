# Layout, density and motion

## Contents

- [Layout](#layout)
- [Section budgets](#section-budgets)
- [Density](#density)
- [Micro-detail that decides whether a UI feels made](#micro-detail-that-decides-whether-a-ui-feels-made)
- [Should it animate at all](#should-it-animate-at-all)
- [Easing](#easing)
- [Duration](#duration)
- [Physicality](#physicality)
- [Interruptibility](#interruptibility)
- [Stagger and orchestration](#stagger-and-orchestration)
- [Reduced motion](#reduced-motion)
- [Motion performance](#motion-performance)
- [Pattern vocabulary](#pattern-vocabulary)
- [Checkable rules](#checkable-rules)

## Layout

- Use CSS Grid for column layouts. Flexbox percentage arithmetic is how gutters end up inconsistent.
- Vary the layout family per section. Repeating three-equal-cards, then left-image / right-text, then
  three-equal-cards again is the generated page's rhythm.
- Content reflows without two-dimensional scrolling at 320 CSS px width (WCAG 2.2 SC 1.4.10 Reflow,
  Level AA). The usual culprits are a fixed heading size, a `max-width` without
  `box-sizing: border-box`, an unwrapped flex row, and an image without `max-width: 100%`.
- Fixed and sticky elements reserve space for the content beneath them, and must not cover the
  element that has keyboard focus (SC 2.4.11).
- Full-bleed layouts account for device notches with `env(safe-area-inset-*)`.
- Prefer `100dvh` to `100vh` on mobile; `100vh` is measured against the largest viewport and gets cut
  off by the browser chrome.
- Avoid nested scroll regions that compete with the page scroll. Where one is unavoidable, set
  `overscroll-behavior: contain` so the gesture does not chain to the page.
- Keep one consistent desktop container width rather than a per-section maximum.
- Avoid unwanted horizontal scrollbars by fixing the overflowing content, not by hiding overflow on
  an ancestor.

## Section budgets

These are counts, not preferences. A page can satisfy every rule above and still read as generated,
because the same device recurs at every scroll position. Count, then cut.

| Budget | Ceiling | How it is counted |
|---|---|---|
| Eyebrows: small uppercase tracked labels above a heading | `ceil(sections / 3)`, hero included | Count the `uppercase` plus `tracking` labels sitting above headings. One per section is the most reliable template signature there is. |
| Consecutive sections sharing the image-and-text split | 2 | The third consecutive split is where a reader stops seeing sections and starts seeing a loop. |
| Reuse of any one layout family | Once | Eight sections need at least four distinct families. "Selected work" must not be built like "What we do". |
| Marquees per page | 1 | A second marquee is decoration rather than rhythm. |
| Grid cells against items | Exactly equal | Five items means five cells. An empty trailing or middle cell means the grid was picked before the content was counted. |
| Text elements in a hero | 4 | Eyebrow or brand strip (zero or one), headline, subtext, CTAs. A tagline under the CTAs, a trust micro-strip, a pricing teaser or an avatar row each belong in their own section below. |

The remaining layout counts:

- Hero subtext stays around 20 words and under four lines; the headline stays under two lines at
  desktop. A four-line hero headline is a font-scale error rather than a copy-length error, so plan
  type size and asset size together.
- Hero top padding stays at or under about 6rem at desktop. More than that reads as content floating
  halfway down the viewport, which registers as a layout bug rather than as deliberate space.
- Desktop navigation renders on one line and stays at or under about 80px tall. Where the items do
  not fit, shorten the labels, drop the secondary ones, or collapse to a menu; a wrapped desktop nav
  is not a responsive win.
- A multi-cell grid needs real visual variation in two or three of its cells: an image, a tint, a
  pattern, a gradient that belongs to the brand. Six white cards containing only text is the default
  even when the rest of the page is not.
- A section header built as a large left headline plus a small explainer paragraph floating in the
  opposite corner is not a default. Stack the two vertically within about 65 characters of measure.
  Reach for the split only where the second column carries a visual or interactive element rather
  than filler prose.
- Every multi-column section declares its own sub-768px fallback where it declares the columns.

## Density

Density is a dial, not a constant. Pick it from the design read set out in this skill's
calibration reference, then be consistent.

- Low density (1-3): large section gaps, generous measure, one idea per viewport.
- Mid density (4-7): standard application spacing.
- High density (8-9): tight padding, hairline separators, monospace with tabular figures for every
  number, and no card containers at all.

Equal generous padding on everything is not "spacious", it is undifferentiated. Vary within the
spacing scale so grouping carries meaning.

Length is a component choice, not a scroll problem:

- Past about five items, a default bulleted list or a row-per-item divider stack is the wrong
  component. Group into two or three labelled clusters, or move to a card grid, tabs, an accordion,
  scroll-snap pills, or a featured-few plus a disclosure for the rest.
- A specification or comparison table carrying a hairline under every row is the laziest available
  layout. Tidying the borders does not fix it: the row-per-fact shape is what fails once there are
  ten facts.
- A twenty-row data dump on a page whose job is a first impression belongs on its own page, with the
  top three to five surfaced where it was.

## Micro-detail that decides whether a UI feels made

- **Concentric radius.** Outer radius = inner radius + padding. A `rounded-2xl` card with `p-2`
  holds a `rounded-lg` child. Mismatched nested radii is the most common reason a card looks subtly
  wrong.
- **Optical over geometric alignment.** Play triangles, single glyphs in round buttons and asymmetric
  icons usually need a 1px nudge or a corrected SVG viewBox. Geometric centering can be visibly off.
- **Hit area is not visual area.** A 16px icon stays 16px and gets its target size from padding or a
  pseudo-element. Do not enlarge the glyph to satisfy a target-size rule, and do not let two hit
  areas overlap.
- **Baseline alignment between adjacent controls.** Two buttons of different heights sitting in the
  text flow will be misaligned; put them in a flex row with an explicit gap rather than relying on
  whitespace between tags.
- **Interactive states escalate.** Hover, active and focus each read as more prominent than rest, and
  disabled reads as less. A hover state that only changes cursor is not feedback.
- **Every clickable thing has a hover state** on pointer devices, and none of them rely on hover
  alone to be discoverable.

## Should it animate at all

Ask this before asking how. Frequency decides.

| How often a person sees it | Decision |
|---|---|
| 100+ times a day (command palette, keyboard shortcut, toggle) | No animation, ever |
| Tens of times a day (hover, list navigation) | Remove or reduce drastically |
| Occasional (modal, drawer, toast) | Standard animation |
| Rare or first-time (onboarding, completion, celebration) | Delight is allowed |

Never animate a keyboard-initiated action. It repeats hundreds of times a day and the animation makes
the tool feel slow and disconnected.

Valid purposes for motion: spatial continuity, state indication, explanation, feedback, and softening
an otherwise jarring change. "It looks cool" is not a purpose for something seen constantly.

One orchestrated moment beats scattered effects. A fade-and-slide-up on every section plus a
transition on every card is the generated default.

## Easing

Decision order:

- Entering or exiting: `ease-out`. Starts fast, so it feels responsive.
- Moving or morphing on screen: `ease-in-out`.
- Hover and color change: `ease`.
- Constant-rate motion (marquee, indeterminate progress, rotation): `linear`.
- When unsure: `ease-out`.

Never `ease-in` for UI. It starts slow and delays exactly the moment the person is watching; an
`ease-out` at 200ms feels faster than an `ease-in` at 200ms.

The built-in CSS keywords are weak. Use stronger curves:

```css
:root {
  /* Strong ease-out for entering and exiting UI. */
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  /* Strong ease-in-out for movement between two on-screen positions. */
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  /* Sheet and drawer curve: long tail, settles without bounce. */
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
}
```

## Duration

| Element | Duration |
|---|---|
| Button press feedback | 100-160ms |
| Tooltip, small popover | 125-200ms |
| Dropdown, select | 150-250ms |
| Modal, drawer | 200-500ms |
| Marketing or explanatory motion | Can be longer |

UI animation stays under 300ms. A 180ms dropdown feels more responsive than a 400ms one, and a faster
spinner makes the same wait feel shorter. Exit is shorter than enter (roughly 60-70%), because the
person has already decided.

Asymmetric timing is a tool: slow where the person is deciding, fast where the system responds. A
hold-to-confirm overlay can fill over two seconds and release in 200ms.

## Physicality

- **Never `scale(0)`.** Start from `scale(0.9)` to `scale(0.97)` plus `opacity: 0`. Nothing appears
  from nothing.
- **Origin-aware popovers.** Scale from the trigger by setting `transform-origin` to the trigger
  side. Modals are the exception: they appear centered in the viewport, so keep
  `transform-origin: center`.
- **Press feedback.** `transform: scale(0.97)` on `:active` with a 160ms `ease-out`. Stay in
  0.95-0.98; below 0.95 looks exaggerated.
- **Percentage translates** are relative to the element's own size, so `translateY(100%)` moves an
  element by exactly its own height whatever that turns out to be. Prefer them to hardcoded pixels
  for sheets and toasts.
- **Springs** simulate physics and have no fixed duration; they maintain velocity when interrupted,
  which makes them right for drag, momentum and gestures a person may reverse mid-motion. Keep bounce
  subtle (0.1-0.3) and reserve visible bounce for drag-to-dismiss and deliberately playful surfaces.
- **`clip-path: inset(t r b l)`** is an underused animation primitive: reveal-on-scroll, hold-to-act
  overlays, seamless tab color transitions (duplicate the label and clip the active copy), comparison
  sliders.
- **Masking an imperfect crossfade**: when two states remain visible through each other despite
  tuning, a `filter: blur(2px)` during the transition blends them into one perceived change. Keep
  blur well under 20px; large blurs are expensive, especially in Safari.

## Interruptibility

CSS **transitions** can be interrupted and retargeted mid-flight. CSS **keyframes** restart from
zero. Anything a person can trigger rapidly (toggles, toasts being added, rapid tab switching) uses
transitions.

```css
/* Interruptible: correct for dynamic state. */
.toast { transition: transform 400ms var(--ease-out), opacity 400ms var(--ease-out); }
```

For an entrance without JavaScript, use `@starting-style` rather than a keyframe:

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 400ms var(--ease-out), transform 400ms var(--ease-out);
  @starting-style { opacity: 0; transform: translateY(100%); }
}
```

Rapid state changes must cancel and replace the prior micro-interaction, set the new final state
explicitly, and never depend on an animation-end event for correctness. And never block input while
an animation plays.

## Stagger and orchestration

- Stagger group entrances by 30-80ms per item. Longer feels sluggish, and a long stagger on a long
  list is worse than no stagger.
- Split the content into chunks and stagger those; animating one container is not orchestration.
- Do not replay entrance animations on the first render of a returning view.
- Stagger is decorative, so it never blocks interaction while it plays.
- Icon swaps cross-fade rather than toggle visibility: scale 0.25 to 1, opacity 0 to 1, blur 4px to
  0, with both icons in the DOM and one absolutely positioned.

## Reduced motion

`prefers-reduced-motion: reduce` means fewer and gentler, not none. Keep transitions that aid
comprehension (opacity, color); remove movement and position change.

```css
@media (prefers-reduced-motion: reduce) {
  .panel { animation: fade 200ms ease; transform: none; }
}
/* Gate hover motion: touch devices fire a false hover on tap. */
@media (hover: hover) and (pointer: fine) {
  .card:hover { transform: scale(1.02); }
}
```

Autoplaying motion longer than five seconds alongside other content needs pause, stop or hide
controls (SC 2.2.2). Muted decorative loops stop entirely under reduced motion.

## Motion performance

- Animate `transform` and `opacity` only. `width`, `height`, `top`, `left`, `padding` and `margin`
  trigger layout, paint and composite on every frame.
- List transition properties explicitly. `transition: all` sweeps in layout properties and makes
  every future property addition an accidental animation.
- Set `transform-origin` deliberately. For SVG, put the transform on a `<g>` wrapper with
  `transform-box: fill-box; transform-origin: center`.
- Do not drive child transforms from a CSS custom property on the parent; that recalculates styles
  for every child. Set `transform` on the element that moves.
- `will-change` only on elements that actually animate, only for `transform`, `opacity` or `filter`,
  and only after observing first-frame stutter. Never `will-change: all`.
- CSS animation runs off the main thread and survives load spikes; request-animation-frame loops
  stutter while the page is parsing or painting. Use CSS for predetermined motion and JavaScript only
  for dynamic or interruptible motion. The Web Animations API gives JavaScript control at CSS
  performance.
- Animations must not cause reflow. Anything that changes position uses `transform`.

## Pattern vocabulary

Names worth knowing so the right pattern can be reached for deliberately. This is a vocabulary, not
a shopping list: most tooling surfaces need none of it.

- Hero: asymmetric split, editorial manifesto, media-mask, scroll-pinned.
- Navigation: dock magnification, magnetic button, morphing status pill, mega-menu reveal.
- Layout: bento grid, masonry, split-screen scroll, sticky-stack sections.
- Cards: parallax tilt, spotlight border, glass panel, morphing modal (the trigger expands into its
  own dialog).
- Scroll: sticky scroll stack, horizontal scroll hijack, zoom parallax, scroll progress path.
- Media: coverflow carousel, drag-to-pan grid, hover image trail, accordion slider.
- Typography: kinetic marquee, text-mask reveal, text scramble, gradient stroke.

Do not mix two animation engines in one component tree; they compete for frames. Use a scroll library
only for genuine scroll choreography, isolated in one leaf with cleanup.

## Checkable rules

- `transition: all`.
- Animating `width`, `height`, `top`, `left`, `margin` or `padding`.
- `scale(0)` as an entrance start state.
- Animation or transform with no `prefers-reduced-motion` variant.
- Hover-only motion not gated behind `(hover: hover)`.
- Keyframes used for a rapidly retriggered state change.
- Autoplaying motion over five seconds with no pause control.
- Missing `overscroll-behavior: contain` in a modal, drawer or sheet.
- Fixed or sticky chrome that can cover the focused element.
- `100vh` on a mobile layout.
- A flex row of variable-height items with no `gap` and no `flex-wrap`.
- More eyebrow labels than `ceil(sections / 3)`.
- Three or more consecutive sections built as the same image-and-text split.
- A grid declaring more cells than there are items.
- A wrapped desktop navigation, or one taller than about 80px.
- A section header built as a big headline plus a small paragraph floating in the opposite corner.
- A default `<ul>` or divider stack carrying more than about five items.

<!-- sources: anthropic-frontend-design, vercel-wig, antfu-design, emil-animations, uiux-pro-max, w3c-wcag22, leonx-taste -->
