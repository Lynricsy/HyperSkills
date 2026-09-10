# Modern API index

Verified against: iOS 26.6 SDK (shipping), iOS 27 RC SDK.

Read this before writing or reviewing any SwiftUI code. Model training data is dense with
API shapes that still compile but are soft-deprecated, and this file is the fastest way to
avoid emitting them.

A **soft-deprecated** API is marked deprecated in the SDK headers with a placeholder
deprecation version (`100000.0`). It compiles without a warning. That is why it survives in
training data and why it needs a lookup table rather than a compiler.

## Contents

- [Behaviour rules for soft-deprecated API](#behaviour-rules-for-soft-deprecated-api)
- [Replacement table](#replacement-table)
- [iOS 26 additions worth knowing](#ios-26-additions-worth-knowing)
- [iOS 27 additions and breakages](#ios-27-additions-and-breakages)
- [Old patterns](#old-patterns)

## Behaviour rules for soft-deprecated API

Scope every observation to the code you were asked to touch.

- Writing new code: never emit anything in the left column of the table below.
- Asked to review, modernise, or clean up: report soft-deprecated API in the reviewed code
  and give the replacement.
- Asked to add a feature or fix a bug: keep the existing API as-is in your diff, then offer
  migration as a separate step in one sentence. Silently swapping API the user did not ask
  about produces unexpected diffs and hides the real change.
- A *different* view in the same file uses old API: say nothing about it. Volunteering
  unrelated migration work is noise, and it pressures the user into a refactor they did not
  request.

## Replacement table

| Do not emit | Emit instead | Floor |
|---|---|---|
| `navigationBarTitle(_:)` | `navigationTitle(_:)` | iOS 15 |
| `navigationBarItems(...)` | `toolbar { ToolbarItem(...) }` | iOS 15 |
| `navigationBarHidden(_:)` | `toolbarVisibility(.hidden, for: .navigationBar)` | iOS 15 |
| `.navigationBarLeading` / `.navigationBarTrailing` | `.topBarLeading` / `.topBarTrailing` | iOS 15 |
| `edgesIgnoringSafeArea(_:)` | `ignoresSafeArea(_:edges:)` | iOS 15 |
| `colorScheme(_:)` | `preferredColorScheme(_:)` | iOS 15 |
| `foregroundColor(_:)` | `foregroundStyle(_:)` | iOS 15 |
| `cornerRadius(_:)` | `clipShape(.rect(cornerRadius:))` | iOS 15 |
| `actionSheet(...)` | `confirmationDialog(_:isPresented:actions:message:)` | iOS 15 |
| `alert(isPresented:content:)` | `alert(_:isPresented:actions:message:)` | iOS 15 |
| `autocapitalization(_:)` | `textInputAutocapitalization(_:)` (`.never`, not `.none`) | iOS 15 |
| `accessibility(label:)` and friends | `accessibilityLabel()`, `accessibilityValue()`, … | iOS 15 |
| `TextField` `onCommit:` / `onEditingChanged:` | `onSubmit { }` + `focused(_:)` | iOS 15 |
| `animation(_:)` with no value | `animation(_:value:)` | back-deploys |
| `Section(header:content:)` positional form | `Section { } header: { }` | back-deploys |
| manual `EnvironmentKey` conformance | `@Entry` macro | Xcode 16 |
| `overlay(_:alignment:)` | `overlay(alignment:content:)` trailing closure | iOS 15 |
| `NavigationView` | `NavigationStack` / `NavigationSplitView` | iOS 16 |
| `accentColor(_:)` | `tint(_:)` | iOS 16 |
| `disableAutocorrection(_:)` | `autocorrectionDisabled(_:)` | iOS 16 |
| `onChange(of:perform:)` single-parameter closure | `onChange(of:) { }` or `onChange(of:) { old, new in }` | iOS 17 |
| `UIImpactFeedbackGenerator` and siblings, in a view | `sensoryFeedback(_:trigger:)` | iOS 17 |
| `MagnificationGesture` / `RotationGesture` | `MagnifyGesture` / `RotateGesture` | iOS 17 |
| `coordinateSpace(name:)` | `coordinateSpace(.named(…))` | iOS 17 |
| `ObservableObject` + `@Published` | `@Observable` | iOS 17 |
| `tabItem(_:)` | `Tab(_:systemImage:value:)` | iOS 18 |
| `PreviewProvider` | `#Preview` macro | iOS 17 |
| manual `animatableData` | `@Animatable` macro | iOS 26 |
| `toolbarBackground(_:for:)` | `toolbarBackgroundVisibility(_:for:)` | iOS 18 |
| `Task.sleep(nanoseconds:)` | `Task.sleep(for:)` | iOS 16 |
| `String(format: "%.2f", x)` | `Text(x, format: .number.precision(.fractionLength(2)))` | any |
| `UIScreen.main.bounds` for available space | `containerRelativeFrame()`, `visualEffect`, or `GeometryReader` | any |

`GeometryReader` is not deprecated. Reach for `containerRelativeFrame(_:)`,
`visualEffect { }`, `onGeometryChange(for:of:action:)`, or the `Layout` protocol first;
`GeometryReader` is still correct when layout itself depends on measured geometry.

## iOS 26 additions worth knowing

Each is gated on `#available(iOS 26.0, *)` unless noted. Liquid Glass API is intentionally
excluded here; the material has its own reference.

- `scrollEdgeEffectStyle(_:for:)` — cases are `.automatic`, `.hard`, `.soft`. `.sharp` and
  `.subtle` do not exist. `[verified]`
- `backgroundExtensionEffect()` — mirrors and blurs a background beyond the safe area so
  artwork stays visible under a sidebar or inspector. Apply it to exactly one background
  view; it clips itself to stop mirrored copies overlapping. Also available on visionOS 26.
- `tabBarMinimizeBehavior(_:)` — tab bar minimisation on scroll. Distinct from the toolbar
  API below; do not confuse the two names.
- `tabViewBottomAccessory { }` plus the `tabViewBottomAccessoryPlacement` environment value.
- `Tab(role: .search)` — a search tab that separates and morphs into a search field.
- `ToolbarSpacer(.fixed)` / `(.flexible)` for grouping toolbar items.
- `sharedBackgroundVisibility(_:)` — scoped to `ToolbarContent`, not a `View` modifier.
- `searchToolbarBehavior(.minimize)` — the case is `.minimize`, not `.minimized`.
- `@Animatable` / `@AnimatableIgnored` macros on `Shape` and other animatable types.
- `controlSize(.extraLarge)`; `.rect(cornerRadius:style: .concentric)`.
- `Slider` tick marks (`ticks:` builder with `SliderTick`) and `sliderNeutralValue(_:)`.
- `TextEditor` bound to an `AttributedString` for rich text.
- `WebView` / `WebPage` (`import WebKit`) replaces hand-wrapped `WKWebView` in
  `UIViewRepresentable` for almost all uses.
- `dragContainer(for:)` + `DragConfiguration` + `onDragSessionUpdated` for multi-item drag.
- `Font` scaling: `.font(.body.scaled(by:))` complements `@ScaledMetric`.
- `navigationTransitionSource(id:namespace:)` / `navigationTransitionDestination(id:namespace:)`
  to morph a sheet out of the control that presented it.
- SwiftData model class inheritance (see the SwiftData reference for the `@available`
  requirement, which applies even when the deployment target is already 26).

Availability floors that are **older than commonly assumed** — gating these needlessly
disables working code: `appearsActive` is iOS 18 / macOS 10.15; `matchedTransitionSource`
and `navigationTransition(.zoom)` are iOS 18; `ForEach` as `ToolbarContent` back-deploys to
iOS 16. `[verified]`

## iOS 27 additions and breakages

iOS 27 is the newer SDK; iOS 26 remains the default deployment target for new apps. Gate
everything here and keep an iOS 26 path.

- `@State` became a **macro**. Views that compiled before can now fail with "variable used
  before being initialized", "invalid redeclaration of synthesized property", or "extraneous
  argument label". Reordering assignments in `init` is *not* the fix and produces wrong
  runtime behaviour — follow the migration diagnostics instead. `[official]`
- `@ViewBuilder` is unified under `@ContentBuilder`; `TupleContent` replaces `TupleView`.
  Consequence: `.overlay(Color.blue.opacity(0.7))` stops compiling with "ambiguous use of
  'opacity'". Use the trailing-closure form `.overlay { Color.blue.opacity(0.7) }`. `[official]`
- `toolbarMinimizeBehavior` was renamed to `toolbarMinimizationBehavior(_:for:)`. Most
  published write-ups still show the old spelling. `[verified]`
- `visibilityPriority(_:)` on toolbar content is **iOS 27 but macOS 26.1**. A combined
  `#available(iOS 27, macOS 27, *)` wrongly suppresses it on macOS 26.1 and 26.2. `[verified]`
- `ToolbarOverflowMenu` / `.toolbarOverflowMenu` are iOS 27 and visionOS 27 only — no macOS.
- `.reorderable()` on `ForEach` plus `.reorderContainer(for:)` gives drag-to-reorder in any
  container. iOS/macOS/watchOS/visionOS 27; unavailable on tvOS.
- `swipeActionsContainer()` extends swipe actions to any scrollable container, not just
  `List`. iOS/macOS/watchOS/visionOS 27; unavailable on tvOS.
- `confirmationDialog` and `alert` gained `item: Binding<T?>` overloads matching the
  `sheet(item:)` shape.
- `AsyncImage(request:)` takes a `URLRequest` for a per-request cache policy;
  `asyncImageURLSession(_:)` supplies a custom session.
- `ReadableDocument` / `WritableDocument` replace `FileDocument` /
  `ReferenceFileDocument` for new document apps targeting 27+.
- Inside sheets and popovers, `controlSize`, `buttonSizing`, `buttonRepeatBehavior`,
  `menuIndicatorVisibility`, and `ButtonBorderShape` reset to defaults when built against
  the 27 SDK. Buttons in sheets can silently change size after an SDK bump. `[verified]`

Sourcing rule: Xcode's bundled model-context documentation is **not** authoritative. It has
shipped at least one fully fabricated API (`scrollExtensionMode(.underSidebar)`) with a
plausible code sample. Verify against developer.apple.com or the SDK interface. `[verified]`

## Old patterns

<details>
<summary>Patterns that were correct on earlier SDKs and should not be reintroduced</summary>

- Wrapping a `Shape` fill and stroke in an `overlay` to get both. Since iOS 17 you can chain
  `.fill()` and `.stroke()` directly.
- `Array(items.enumerated())` before `ForEach`. Since Swift 6.1 `enumerated()` conditionally
  conforms to `RandomAccessCollection`, so `ForEach(items.enumerated(), id: \.element.id)`
  works without the eager copy.
- `import Combine` being implied by `import SwiftUI`. It no longer is; a file that still
  uses `ObservableObject` or a publisher needs the explicit import.
- `showsIndicators: false` in a `ScrollView` initialiser. Use `.scrollIndicators(.hidden)`.
- `Text("a") + Text("b")` concatenation. Build the parts as `Text` values and interpolate:
  `Text("\(red)\(blue)")`.
- `UIGraphicsImageRenderer` to rasterise a SwiftUI view. Use `ImageRenderer`.
- `presentationBackground(_:)` used to force a sheet material. iOS 26 sheets carry the
  system material by default; setting a background defeats it.

</details>

<!-- sources: avdlee-swiftui, avdlee-update-apis, twostraws-swiftui, apple-xcode27, yordi-liquid-glass, apple-docs -->
