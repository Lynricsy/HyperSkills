# Liquid Glass motion

Verified against: iOS 26.6 / macOS 26.6 SDK; unchanged in iOS 27 RC.

Morphing, glass transitions, scroll-driven chrome, and Metal shaders around glass. Every
symbol here is iOS 26.0+ / macOS 26.0+ and unavailable on visionOS. Same confidence tags as
the material reference: `[verified]`, `[official]`, `[community]`.

## Contents

- [The physical model](#the-physical-model)
- [The four morph ingredients](#the-four-morph-ingredients)
- [glassEffectUnion](#glasseffectunion)
- [glassEffectTransition](#glasseffecttransition)
- [Scroll-driven chrome](#scroll-driven-chrome)
- [Reduce Motion](#reduce-motion)
- [Metal shaders](#metal-shaders)
- [Profiling glass](#profiling-glass)

## The physical model

Glass does not fade in. It **materialises**: the system ramps how strongly the surface bends
and scatters what is behind it, so the element resolves out of the backdrop instead of
cross-dissolving over it. `[official]`

Size is part of the material. A larger glass surface reads as *thicker* glass — deeper
shadow, more lensing at the edges, a different specular response. A change in size is a
change in material, not a change in a `frame` value. `[official]`

Two consequences:

- **Never fake a morph.** `.opacity`, a cross-fade, `matchedGeometryEffect` on a
  material-backed view, or animating `frame` on a glass view all move geometry while the
  material stays fixed. The result slides and then snaps. Only the system morph re-derives
  lensing and shadow per frame. `[community]`
- **Never set `opacity < 1` on a glass view or an ancestor**, in motion or at rest. It
  composites the material as a flat image. `[community]`

The interactive "squish" is one boolean, `.interactive()`. No public spring, damping, or
stiffness knobs exist for it — do not promise tunable jelly. `[community]`

## The four morph ingredients

All four must hold at once. Miss one and there is no error, no warning, and no morph.

1. Both elements live in the **same `GlassEffectContainer`**.
2. Each carries **`glassEffectID(_:in:)` with one shared `@Namespace`**. The id must be
   `Hashable & Sendable` — never a model object, never a fresh `UUID()` per render.
   `[verified]`
3. The trigger is **insertion or removal from the hierarchy** — an `if`, a `switch`, a
   `ForEach` element appearing. A value change on an always-present view is not a morph
   trigger.
4. The mutation happens **inside an animation context**: `withAnimation { … }` at the
   mutation site, or `.animation(_:value:)` on the container.

Plus geometry: the nearest edges must fall within the container's `spacing`, or the effects
never merge.

```swift
@Namespace private var toolCluster
@State private var showsBrush = false

GlassEffectContainer(spacing: 24) {
    HStack(spacing: 24) {
        if showsBrush {
            Image(systemName: "paintbrush.fill")
                .frame(width: 56, height: 56)
                .glassEffect()
                .glassEffectID("brush", in: toolCluster)
        }
        Image(systemName: "slider.horizontal.3")
            .frame(width: 56, height: 56)
            .glassEffect()
            .glassEffectID("adjust", in: toolCluster)
    }
}

Button("Brush") { withAnimation(.snappy) { showsBrush.toggle() } }
    .buttonStyle(.glass)
```

`glassEffectID` names an *existing* glass effect. Putting one on a view that has neither
`glassEffect()` nor a glass button style names nothing and morphs nothing — a common silent
failure in review. `[verified]`

Keep every element in one morph on the same `Glass` variant and the same tint; mixed
variants morph inconsistently. `[community]`

## glassEffectUnion

`glassEffectUnion(id:namespace:)` fuses several glass views into one continuous surface
regardless of their spacing — the correct tool for a segmented cluster that should read as a
single pill. It is a grouping instruction, not an animation: views in a union still need the
morph ingredients above to animate.

## glassEffectTransition

`glassEffectTransition(_:)` selects how a glass view enters and leaves.
`.matchedGeometry` morphs it from a sibling; `.materialize` is the sanctioned fade-like
option that ramps lensing instead of alpha. These are the only approved substitutes for
`.opacity` on glass.

## Scroll-driven chrome

Prefer renderer-side motion over plumbing scroll offsets through observable state.
`scrollTransition { content, phase in }` and `visualEffect { content, geometry in }` run in
the render pass and never invalidate a body; an observable offset invalidates on every
frame of a scroll.

Scroll-edge behaviour under floating glass chrome is `scrollEdgeEffectStyle(_:for:)` with
`.automatic` / `.hard` / `.soft`, and tab-bar minimisation is `tabBarMinimizeBehavior(_:)`.
Neither needs a hand-rolled offset observer.

## Reduce Motion

**The system tones down its own glass motion. It does not touch yours.** Not handled, ever:
every `withAnimation` you write (including the one driving a morph), `.animation(_:value:)`,
`PhaseAnimator`, `KeyframeAnimator`, `.repeatForever` loops, scroll-driven parallax, custom
`Transition` types, and `matchedGeometryEffect`.

Gate **per animated component**. A single check at app level is a review finding, because it
leaves every component free to animate.

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

withAnimation(reduceMotion ? .none : .snappy) { showsBrush.toggle() }
```

Four APIs need no gate — the system adapts them: `.contentTransition(.numericText(…))`
(iOS 16+), `.symbolEffect(…)` (iOS 17+), `.navigationTransition(.zoom(sourceID:in:))`
(iOS 18+), `.sensoryFeedback(_:trigger:)` (iOS 17+). Standard navigation pushes, sheets, and
tab switches adapt too — the strongest argument for using system motion rather than
rebuilding it.

Assume any glass animation sample you find — blog post, published skill, generated code — is
ungated, and gate it as you adopt it. Reduce-motion users have reported the default glass
morph as flickering. `[community]`

## Metal shaders

`colorEffect`, `distortionEffect`, and `layerEffect` take a `[[stitchable]]` Metal function
and run per pixel on the rendered view.

- A `distortionEffect` or `layerEffect` that samples outside the view's bounds needs
  `maxSampleOffset:`; without it the result is clipped at the edges, which is the usual
  cause of "my shader has a hard border".
- Shaders run **below** the glass sampling region. A shader cannot read the glass output, so
  do not try to build a custom glass from one — build the backdrop the glass will refract.
- Animate a shader by passing time as a uniform driven by `TimelineView`, not by rebuilding
  the `Shader` value each frame.
- Shaders are a GPU cost on every frame they are visible. Gate them behind Reduce Motion and
  Low Power Mode where they are decorative.

## Profiling glass

Glass costs GPU time; the honest statement is "profile it", not a viral battery figure.
Record with the SwiftUI template on a real device — the Simulator's SwiftUI lane is empty —
and read animation hitches alongside main-thread coverage. The recording and analysis
workflow lives in the performance reference.

<!-- sources: yordi-liquid-glass, avdlee-swiftui, apple-docs -->
