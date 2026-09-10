# Liquid Glass — the material

Verified against: iOS 26.6 / macOS 26.6 SDK; carried unchanged into iOS 27 RC.

Every rule below carries an availability floor and a confidence tag: `[verified]` (checked
against Apple documentation or the SDK interface), `[official]` (Apple states it), or
`[community]` (corroborated by practitioners, not by Apple).

**Scope.** SwiftUI first; UIKit and AppKit equivalents live in the interop reference.
**visionOS is excluded** — the SDK marks `glassEffect`, `GlassEffectContainer`,
`glassEffectID`/`Union`/`Transition`, the `Glass` type, the glass button styles, and
`scrollEdgeEffectStyle` as `@available(visionOS, unavailable)` `[verified]`. Apple's
rendered docs show "visionOS 1.0" for these symbols; where the docs and the SDK disagree,
the SDK wins. watchOS and tvOS are excluded here for a different reason: no reliable
source material exists, so do not improvise. Motion, morphing, and shaders have their own
reference.

## Contents

- [Adoption stance](#adoption-stance)
- [Twelve hard rules](#twelve-hard-rules)
- [Variants, tint, and shape](#variants-tint-and-shape)
- [Containers](#containers)
- [Toolbars and scroll edges](#toolbars-and-scroll-edges)
- [Availability floors people get wrong](#availability-floors-people-get-wrong)
- [APIs that do not exist](#apis-that-do-not-exist)
- [Migration hygiene](#migration-hygiene)

## Adoption stance

New iOS 26+ code gets Liquid Glass **through standard components**. Toolbars, tab bars,
sheets, search, and split-view sidebars adopt the material simply by recompiling against
the 26 SDK. Hand-rolling glass on those surfaces is work that will drift from the system.

Adding a **custom `glassEffect` surface to an existing app requires an explicit request
from the user.** Volunteering it changes the app's visual language, and a partial adoption
looks worse than none.

Every iOS 26+ API is `#available`-gated per platform with a real fallback.

## Twelve hard rules

1. **Gate per platform with each API's real floor, and provide a fallback.** The floor for
   glass is iOS 26.0 / macOS 26.0. An iOS-only guard silently strips glass from a Mac target
   that could render it. Put the split in one `ViewModifier`, `ButtonStyle`, or small `View`
   rather than scattering `#available` through call sites — the branch-per-call-site form
   duplicates the subtree and swaps view identity. `[verified]`
2. **Never wrap `glassEffect` in a `.if` conditional-modifier helper.** The two branches are
   different view types, so structural identity breaks, descendant `@State` resets, and
   animation degrades to remove-and-insert. Use `glassEffect(cond ? .regular : .identity)`
   or the `isEnabled:` parameter. The helper also stops compiling against the 27 SDK.
   `[verified]`
3. **Apply `glassEffect` after layout and appearance modifiers.** The effect needs final
   geometry: `.padding().frame(…).glassEffect(…)`, never the reverse. `[community]`
4. **Two or more glass surfaces near each other share one `GlassEffectContainer`.** Glass
   cannot sample glass, so every unparented sibling opens its own sampling region and the
   group renders inconsistently. This is visual correctness, not tuning — and it is the
   precondition for morphing. `[community]` (iOS 26.0+)
5. **`interactive()` only on surfaces that actually respond to input.** It installs
   continuous gesture tracking, so on an inert view it is pure cost. Buttons already have
   it. It is iOS 26.0 **and macOS 26.0** — the widely repeated "iOS only" claim is false and
   Apple tuned it for the Mac pointer, so do not strip it from a Mac build. `[verified]`
6. **Never set `opacity < 1` on a glass view or any ancestor.** Partial opacity forces the
   subtree into a separate composited layer and refraction silently collapses: it compiles,
   it renders, it just stops looking like glass. Glass materialises; it does not fade.
   `[community]`
7. **Glass needs something to refract.** Over a flat single-colour background — pure black
   is the worst case — it reads as a tinted rectangle. If the surface looks flat, the bug is
   in the layout behind it. Let content run edge-to-edge under floating chrome.
   `[community]`
8. **Never stack glass on glass.** Elements sitting *on* a glass surface get fills and
   vibrancy, not a second `glassEffect`. One dominant glass layer per region; a native
   blurred header with a custom glass child inside it is the same defect. `[community]`
9. **Custom-shape glass controls need `contentShape`.** `.frame()` sets layout size only;
   the hit area still follows the content's geometry, so only the glyph hit-tests.
   `[community]`
10. **Glass ignores `.allowsHitTesting(false)`** and keeps reacting visually. Only
    `.disabled(true)` makes it inert. `[verified]`
11. **Do not fight the accessibility adaptation.** The system frosts the material under
    Reduce Transparency and Increase Contrast. Do not remove glass manually where the system
    would have adapted it, and do not add custom shadows or borders — the system owns the
    edge treatment and adapts it; a hand-added stroke does not. `[community]`
12. **Dark, muddy glass over bright backgrounds in Dark Mode is by design.** Fix the
    background colours, not the glass. `[verified]`

Two more that follow from the same model: keep the glass shape in `glassEffect(_:in:)`
rather than a trailing `.clipShape` (clipping cuts the outer lensing and does nothing for
hit testing), and never apply `rotationEffect` to a glass view — it corrupts the geometry
and is unfixed. `[community]`

## Variants, tint, and shape

`.regular` is the default and correct for nearly all chrome: medium transparency, fully
adaptive. `.clear` is high transparency with *limited* adaptation — use it only for a small
floating control over media-rich content, and only with a dimming layer beneath. `.identity`
is "no glass" expressed as a value, which is how you toggle glass without an `if`.

Do not enforce "never mix `.regular` and `.clear`" as an absolute. Apple's guidance puts
`.clear` over media and `.regular` everywhere else, so real apps contain both. Flag
inconsistency *within a peer group* — two toolbars in one app disagreeing — not coexistence.

Tint only when the colour carries meaning: primary action, live state, alert. Tint is a
hierarchy signal, and tinting everything destroys it. `.tint(_:)` and `.interactive(_:)`
chain in either order; both build the same `Glass` value.

The default shape is a capsule. Pass `in:` for anything else. Inside a sheet, card, or
window corner, prefer concentric corners (`ConcentricRectangle`, or
`.rect(cornerRadius: .containerConcentric)`) over a guessed radius so inner and outer radii
stay parallel across device geometries. `ConcentricRectangle` is iOS 26.0+, macOS 26.0+, and
genuinely available on visionOS 26 — it is not a glass API, so the visionOS exclusion does
not apply. `[verified]`

`.buttonStyle(.glass)` is iOS 26.0. The configurable overload `.buttonStyle(.glass(_:))`
taking a `Glass` value is real, but the initialiser it calls is annotated 26.1 — pin it
there. `.glassProminent` has no configurable overload at all; tint it with `.tint(_:)` on
the button. `[verified]`

## Containers

```swift
GlassEffectContainer(spacing: 24) {
    HStack(spacing: 24) {
        ToolButton(symbol: "pencil")
        ToolButton(symbol: "eraser")
    }
}
```

`spacing:` is a **merge threshold**, not padding: it is the distance within which
neighbouring glass effects blend and morph. If the gap between two glass views exceeds it,
they never merge and a morph between them silently does nothing. It lays nothing out.
SwiftUI examples cluster at 20–40; treat that as a starting point to verify visually.

Constrain the container's *content*, never the container itself — sizing the container
fights the sampling region it establishes.

Do not scatter related glass elements across several containers; separate containers cannot
sample each other, which reproduces the inconsistency the container exists to remove.

On AppKit, `NSGlassEffectContainerView.spacing` deliberately defaults to 0 — shared sampling
without merging. Do not "fix" a Mac container by copying an iOS number into it. `[official]`

## Toolbars and scroll edges

- `ToolbarSpacer(.fixed)` and `(.flexible)` group toolbar items; grouping is how the glass
  capsules split visually. (iOS 26.0+)
- `sharedBackgroundVisibility(.hidden)` removes the shared glass background from one
  toolbar item. It is scoped to `ToolbarContent` — it is **not** a `View` modifier.
  (iOS 26.0+)
- `scrollEdgeEffectStyle(_:for:)` cases are `.automatic`, `.hard`, `.soft`. (iOS 26.0+)
- `tabBarMinimizeBehavior(_:)` (iOS 26.0) minimises the tab bar on scroll. Do not confuse
  it with `toolbarMinimizationBehavior(_:for:)`, which is the renamed *toolbar* API at
  iOS 27 (previously `toolbarMinimizeBehavior`). `[verified]`
- `backgroundExtensionEffect()` (iOS/macOS/visionOS 26.0) is the API for content extending
  under a sidebar or inspector. Apply it to exactly one background view; it clips itself to
  stop mirrored copies overlapping. `[verified]`

## Availability floors people get wrong

| Symbol | Real floor | Commonly misstated as |
|---|---|---|
| `Glass.interactive(_:)` | iOS 26.0, macOS 26.0, Mac Catalyst 26.0 | "iOS only" |
| `visibilityPriority(_:)` | **iOS 27 but macOS 26.1** | "iOS 27 / macOS 27" — a combined guard breaks macOS 26.1–26.2 |
| `appearsActive` | iOS 18 / macOS 10.15, back-deployed | "new in WWDC26" — gating it behind 27 disables working code |
| `matchedTransitionSource` / `navigationTransition(.zoom)` | iOS 18 | "iOS 26+" |
| `ForEach` as `ToolbarContent` | back-deploys to iOS 16 / macOS 13 | "iOS 27" |
| `sharedBackgroundVisibility(_:)` | iOS 26.0 | over-gated |
| `.buttonStyle(.glass(_:))` configurable overload | iOS 26.1 / macOS 26.1 | 26.0 |
| `.symbolEffect(.drawOn)` | modifier iOS 17, **effect 26.0** | guard placed on the modifier |

`UIDesignRequiresCompatibility` was **not removed**. Built against the iOS 26 SDK it still
works, and Apple's adoption guide still recommends it as a transition tool; built against
the iOS 27 SDK the system ignores it. State the SDK condition whenever you mention it.
Reject both "it's gone" and "it still opts you out on 27". `[verified]`

## APIs that do not exist

Never emit these; flag them on sight.

| Never emit | Reality |
|---|---|
| `scrollExtensionMode(.underSidebar)` | Fabricated. Real API: `backgroundExtensionEffect()`. It appears with a plausible code sample inside Xcode 27's own bundled model-context documentation, which is therefore not authoritative. `[verified]` |
| `.background(.secondaryBackground)` | No such `ShapeStyle`. Use `.background(.secondary)`, `Color(.secondarySystemBackground)` on iOS, or `.windowBackground` on macOS. |
| `DefaultGlassEffectShape` | Not a type. The default shape is a capsule — omit `in:`. |
| `ScrollEdgeEffectStyle.sharp` / `.subtle` | Cases are `.automatic` / `.hard` / `.soft`. `[verified]` |
| `.searchToolbarBehavior(.minimized)` | The case is `.minimize`. |
| `UIGlassEffect(glass:isInteractive:)` | Fabricated initialiser. Use `UIGlassEffect()` and set `isInteractive`. |
| `UIViewCornerConfiguration(corners:cornerRadius:)` | Not a type. Assign `UIView.cornerConfiguration` from a `UICornerConfiguration` factory. |
| `.glassBackgroundEffect(…)` on iOS or macOS | visionOS-only API, and glass is unavailable on visionOS — doubly misfiled. |
| `@Environment(\.accessibilityPrefersCrossFadeTransitions)` | No such environment value. Read `UIAccessibility.prefersCrossFadeTransitions`. |
| "13% battery on iOS 26 vs 1% on iOS 18" | Unsourced anecdote. Keep the qualitative claim — glass costs GPU, profile it — and drop the number. |
| A 44 pt minimum hit target on macOS | The iOS touch minimum applied to a pointer platform. Standard regular-size Mac controls are around 28 pt. |

## Migration hygiene

Deletion precedes addition. Before adding glass, remove the pre-26 survivors sitting under
it, each of which defeats the material: `toolbarBackground(…)` forcing an opaque bar,
`presentationBackground(Color.white)` on a sheet, `UITabBar.appearance()` and
`UINavigationBar.appearance()` global proxies, hand-rolled `.ultraThinMaterial` on chrome,
and legibility scrims the material now provides.

Never present Simulator rendering or exact screenshot pixels as evidence a glass change is
correct. The material renders differently on device, and screenshot comparison of glass is
not a reliable gate.

A glass review that only checks how glass was applied has done half the job. The
higher-value finding is usually a deletion: glass on the content layer (the most common
adoption defect), glass on scrolling rows, glass on static labels, glass as a full-screen
background, and glass hand-added where the system already provides it.

<!-- sources: yordi-liquid-glass, avdlee-swiftui, apple-docs, apple-xcode27 -->
