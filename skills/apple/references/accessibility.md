# Accessibility

Verified against: iOS 26.6 SDK; WCAG 2.2.

Accessibility is not deterministic: the same screen can be usable one way and unusable
another. Propose fixes in order of confidence with their trade-offs, and pair every code
change with a manual-testing step. A checklist is a floor, not the goal.

## Contents

- [Intake](#intake)
- [Anti-patterns](#anti-patterns)
- [VoiceOver](#voiceover)
- [Dynamic Type](#dynamic-type)
- [Voice Control](#voice-control)
- [Switch Control and Full Keyboard Access](#switch-control-and-full-keyboard-access)
- [Colour, contrast, and motion](#colour-contrast-and-motion)
- [Charts](#charts)
- [Testing, and what it cannot tell you](#testing-and-what-it-cannot-tell-you)

## Intake

Before advising, establish: SwiftUI, UIKit, or both; the deployment target (several APIs
below have floors); whether the project has a design system — if so, fix the component
there so the improvement propagates; whether accessibility strings are localised like every
other user-facing string (they must be); and whether any custom gesture lacks an accessible
alternative.

## Anti-patterns

- **Trait names inside labels.** "Close", not "Close button" — VoiceOver appends the trait.
- **`accessibilityHidden(true)` on an interactive element.** It becomes unreachable.
- **Fixed font sizes.** Text styles, always.
- **Hard-coded text colours.** Semantic colours adapt to Dark Mode and Increase Contrast.
- **Grouping without a combined label.** `accessibilityElement(children: .ignore)` with no
  `accessibilityLabel` produces a silent element.
- **Hints for things the label already says.** A hint is for non-obvious consequences only.
- **`onTapGesture` instead of `Button`.** If it is unavoidable, add
  `.accessibilityAddTraits(.isButton)` and a label.
- **Scaling chrome with Dynamic Type.** Navigation bars, toolbars, and tab bars should not
  grow; use the Large Content Viewer (`accessibilityShowsLargeContentViewer`, iOS 13+).

## VoiceOver

- Every tappable element is a `Button` with text, even when the text is not drawn:
  `Button("Add User", systemImage: "plus", action: addUser)` plus
  `.labelStyle(.iconOnly)` if it must stay visually icon-only. The same applies to `Menu`.
- An `Image` from an asset catalogue reads its asset name aloud. Decorative art gets
  `Image(decorative:)`; SF Symbols and other non-asset images get
  `.accessibilityHidden(true)`. An informative image gets an explicit
  `.accessibilityLabel`.
- Group a compound row so VoiceOver announces it once:
  `.accessibilityElement(children: .combine)` for automatic concatenation, or `.ignore`
  plus an explicit label, value, and traits when you want full control.
- Use `.accessibilityValue` for the changing part and `.accessibilityLabel` for the stable
  part, so the label does not have to be re-read on every update.
- State-driven traits go through `accessibilityAddTraits` / `accessibilityRemoveTraits`:
  `.accessibilityAddTraits(item.isSelected ? [.isSelected, .isButton] : .isButton)`.
- `.disabled(true)` makes VoiceOver announce "dimmed"; hiding a disabled control instead
  removes the user's ability to discover it exists.
- Custom controls need label, value, traits, *and* actions —
  `.accessibilityAction(named:)` for anything reachable only by gesture.
- `AccessibilityFocusState` (iOS 15+) moves VoiceOver focus after a state change, such as
  to a newly presented error.
- `.accessibilityRotor` (iOS 15+) gives fast navigation through a long list's key items.
- `.accessibilityRepresentation` (iOS 16+) lets a custom control borrow a standard
  control's accessibility semantics wholesale.
- Use the dedicated modifiers, never the legacy generic `accessibility(label:)` family.

## Dynamic Type

- Use text styles (`.body`, `.headline`, `.caption`) rather than point sizes.
- Custom faces still scale via `Font.custom(_:size:relativeTo:)`.
- Scale non-text metrics — padding, icon sizes, avatar frames — with `@ScaledMetric`, and
  pass `relativeTo:` when the value should track a specific style.
- (iOS 26+) `.font(.body.scaled(by:))` gives a scaled variant without a `@ScaledMetric`
  property.
- Layout must survive the accessibility sizes, not just the largest standard one. Fixed
  frames and single-line truncation are where it breaks. Test at AX5.
- Switch a horizontal row to a vertical stack past a threshold using
  `@Environment(\.dynamicTypeSize)` rather than truncating.

## Voice Control

Voice Control activates controls by **speaking their accessibility label**, so labels are an
input surface, not just an output one.

- The label must match the visible text. A button showing "Submit" labelled "Send" cannot be
  activated by what the user reads.
- Duplicate labels on one screen create ambiguity and force the user into numbered mode.
- When the visible text is volatile or unspeakable — a live share price rendered as
  "AAPL $271.68" — add alternatives with `.accessibilityInputLabels(["Apple", "AAPL"])`.
  This is the single highest-value Voice Control modifier and it is almost never used.

## Switch Control and Full Keyboard Access

Both scan the accessibility tree, so good VoiceOver support carries most of the way. The
additional work is about *cost per element*:

- Group related elements so scanning reaches the target in fewer steps. Every ungrouped
  decorative element is another switch press.
- Expose secondary operations as custom actions rather than as separate scan stops.
- Focus order follows accessibility order; set it explicitly with
  `.accessibilitySortPriority` where the visual order and the logical order differ.
- Full Keyboard Access needs a visible focus indicator and a sane Tab order. Test with a
  hardware keyboard on iPad — it is the platform where this matters most.

## Colour, contrast, and motion

- Contrast minimums are WCAG 2.2 AA: **4.5:1** for body text, **3:1** for large text
  (18 pt regular or 14 pt bold and above) and for meaningful UI components.
- Minimum target size under WCAG 2.2 AA (SC 2.5.8) is **24×24 CSS px**; Apple's own iOS
  guidance is stricter at **44×44 pt**, which is the number to enforce on touch. Neither
  applies to macOS pointer chrome, where standard controls are around 28 pt.
- Never carry meaning in colour alone. Honour
  `\.accessibilityDifferentiateWithoutColor` with an icon, pattern, stroke, or text.
- Honour `\.accessibilityReduceMotion` per animated component; the system gates its own
  motion, not yours. Replace large movement with a cross-fade, not a slower movement.
- `\.accessibilityReduceTransparency` and Increase Contrast are handled automatically for
  system materials including Liquid Glass. Do not remove the material by hand where the
  system would have frosted it.

## Charts

A chart is an image to VoiceOver unless you make it otherwise.

- Give each mark `.accessibilityLabel` and `.accessibilityValue` so the series can be
  traversed point by point.
- `.accessibilityChartDescriptor` enables the Audio Graph, which plays the series as tones.
- Always provide a non-visual fallback — a summary sentence stating trend and extremes, or
  a data table — because a plot with 500 points is not navigable one mark at a time.

## Testing, and what it cannot tell you

- Automated audits (`XCUIApplication.performAccessibilityAudit()`) catch missing labels,
  contrast failures, clipped text at large sizes, and undersized targets. They cannot judge
  whether a label is *useful*, whether the reading order makes sense, or whether a flow is
  completable.
- Manual passes that find what automation cannot: navigate the whole flow with VoiceOver
  and the screen curtain on; set Dynamic Type to AX5 and check nothing truncates or
  overlaps; complete a core task with Voice Control only; run the flow with Reduce Motion
  and Reduce Transparency enabled.
- Ship-blocking bar: every interactive element is reachable and correctly announced, and
  every core task is completable with VoiceOver alone.

<!-- sources: dadederk-a11y, twostraws-swiftui, avdlee-swiftui, yordi-liquid-glass, apple-docs -->
