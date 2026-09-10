# Design and Human Interface Guidelines

Verified against: iOS 26.6 SDK.

Design decisions that are also correctness decisions: the ones that break on a different
device size, a larger Dynamic Type setting, another locale, or a pointer platform.

## Contents

- [Consistency](#consistency)
- [Layout that survives](#layout-that-survives)
- [Use the system component](#use-the-system-component)
- [Typography and weight](#typography-and-weight)
- [Colour](#colour)
- [Motion feel](#motion-feel)
- [Platform differences](#platform-differences)

## Consistency

Put fonts, sizes, colours, stack spacing, padding, corner radii, and animation timings in a
shared namespace of constants so every view draws from the same vocabulary and the app can
be retuned in one place. If the project already has a design system, propose the change
inside the design system rather than per feature — the improvement then propagates.

## Layout that survives

- Never read available space from `UIScreen.main.bounds`. It is wrong in split view, in
  Slide Over, on external displays, and in any resizable window. Use
  `containerRelativeFrame(_:)`, `visualEffect { }`, or `GeometryReader` when layout truly
  depends on measured geometry.
- Avoid fixed frames unless the content genuinely fits inside them at every Dynamic Type
  size. Give frames flexibility — `minWidth`, `idealHeight`, ranges — rather than a single
  number.
- Avoid hard-coded padding and stack spacing unless asked. The defaults adapt to platform
  and size class; a literal does not.
- The minimum tap target on iOS is 44×44 pt, enforced strictly. On macOS this number is
  wrong: standard regular-size controls are around 28 pt, and copying the touch minimum
  produces oversized, non-native chrome.
- Design for the smallest supported width first, then let content expand. Views should be
  context-agnostic — a row that hard-codes its own width cannot be reused in a sidebar.

## Use the system component

Building a custom version of something the system provides costs the free adaptations:
Dynamic Type, VoiceOver, Reduce Motion, high contrast, RTL, pointer support, and Liquid
Glass.

- `ContentUnavailableView` for empty and error states. With `searchable()`, use
  `ContentUnavailableView.search` — it inserts the user's search term automatically, so
  passing `text:` yourself is redundant.
- `Label` rather than an `HStack` of icon and text; it adapts its own layout to context.
- `LabeledContent` to pair a title with a control or value — required inside `Form` to lay
  a `Slider` out correctly, and useful outside it. A custom `LabeledContentStyle` keeps the
  pairing consistent across screens.
- `RoundedRectangle`'s default corner style is already `.continuous`; specifying it is noise.
  Inside a sheet, card, or window corner, prefer concentric corners so radii stay parallel.
- Prefer hierarchical styles (`.secondary`, `.tertiary`) to manual opacity so the system can
  adapt them per context and per accessibility setting.

## Typography and weight

- Use `bold()` rather than `fontWeight(.bold)`; it lets the system pick the correct weight
  for the current context and accessibility settings.
- Reserve `fontWeight()` for weights other than bold, and only with a reason. Scattered
  `.medium` and `.semibold` flatten the hierarchy rather than creating it.
- `.caption2` is extremely small and generally best avoided; `.caption` needs care.
- Custom fonts must still scale: `Font.custom(_:size:relativeTo:)` binds the custom face to
  a text style. A fixed-size custom font on primary content is a Dynamic Type failure.

## Colour

- Use SwiftUI `Color` and asset-catalogue colours, never `UIColor` inside SwiftUI code.
- Semantic colours (`.primary`, `.secondary`, `Color(.systemBackground)`) adapt to Dark Mode
  and Increase Contrast; hard-coded hex values do not.
- Never let colour be the only carrier of meaning. Respect
  `\.accessibilityDifferentiateWithoutColor` by adding an icon, a pattern, a stroke, or text.
- Reference asset-catalogue images through the generated symbol API — `Image(.avatar)`, not
  `Image("avatar")` — when the project has generated symbols enabled.

## Motion feel

Apple's motion vocabulary is springs, not eased durations. Reach for `.smooth`, `.snappy`,
and `.bouncy` before writing a curve, and parameterise custom springs by duration and
bounce rather than stiffness and damping.

Motion should be quick and interruptible. An animation the user cannot cancel by touching
the screen reads as unresponsive regardless of its curve. Prefer animations that track the
gesture over animations that play on a fixed timeline.

Motion earns its place by explaining a spatial relationship — where something came from,
where it went. Decorative motion is the first thing to cut, and the first thing that becomes
a Reduce Motion liability.

## Platform differences

Do not assume iPhone. The same SwiftUI view compiled for another platform inherits different
conventions:

- **iPadOS**: multitasking means the window is resizable at any moment; size classes, not
  device checks. Pointer and keyboard support are expected, not optional.
- **macOS**: menu bar commands, multiple windows, `Settings` scene, hover states, smaller
  control metrics, and no assumption that a view is ever full-screen.
- **watchOS**: extremely short interactions, Digital Crown input, no Liquid Glass.
- **tvOS**: focus-driven, no touch, distance viewing — text and targets are much larger.
- **visionOS**: depth and ornaments instead of chrome; Liquid Glass is unavailable, and
  `glassBackgroundEffect` is the platform's own material API.

When a design decision differs per platform, branch on the platform's own idiom rather than
replicating the iPhone layout everywhere.

<!-- sources: twostraws-swiftui, yordi-liquid-glass, avdlee-swiftui, apple-docs -->
