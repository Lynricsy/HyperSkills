# Animation

Verified against: iOS 26.6 SDK.

## Contents

- [Rules that are always bugs](#rules-that-are-always-bugs)
- [Implicit versus explicit](#implicit-versus-explicit)
- [Transitions](#transitions)
- [Animatable types](#animatable-types)
- [Phase and keyframe animation](#phase-and-keyframe-animation)
- [Reduce Motion](#reduce-motion)

## Rules that are always bugs

- `animation(_:)` without `value:` animates every change the view ever sees, including ones
  from unrelated ancestors. Always `.animation(.bouncy, value: score)`.
- One animation source per property. Mixing an implicit `.animation` with `withAnimation`
  and a scroll-driven update on the same property gives non-deterministic results, and an
  implicit modifier applied lower in the tree silently wins over the explicit one.
- The animation context must live **outside** the condition. `.animation()` written inside
  an `if` branch is destroyed along with the view, so removal never animates.
- Chain animations with the `completion:` closure on `withAnimation`, not with delayed
  second calls:

  ```swift
  withAnimation { scale = 2 } completion: { withAnimation { scale = 1 } }
  ```
- Do not animate structural identity. Toggling between two different view types replaces
  rather than animates; keep the same view and animate a property.

## Implicit versus explicit

`withAnimation` wraps the *state change* and animates every view that depends on it —
correct for a change that should ripple. `.animation(_:value:)` scopes the animation to one
subtree and one value — correct when only part of the hierarchy should react.

Animate in this order of cost: transforms first (`scaleEffect`, `offset`, `rotationEffect`),
then frames and layout, and identity changes last.

`Transaction` carries animation settings down the tree. `transaction { $0.animation = nil }`
disables animation for a subtree that should not follow the ambient one; `.transaction`
is also how you inspect whether a change arrived animated.

Springs are the default vocabulary: `.smooth`, `.snappy`, `.bouncy`, or
`spring(duration:bounce:)`. Prefer duration-and-bounce over stiffness-and-damping; the
former is the parameterisation Apple's own motion uses. Reach for `UnitCurve` only for a
custom easing that no spring expresses.

## Transitions

- `.transition(_:)` needs the view to be inserted or removed inside an animated change.
  Nothing happens if the containing view merely re-renders.
- Combine with `.combined(with:)`, and use `.asymmetric(insertion:removal:)` when the two
  directions differ.
- `matchedGeometryEffect(id:in:)` moves a view between two positions with a shared
  `@Namespace`. Exactly one of the pair is the source (`isSource: true`); both being source
  or neither being source produces a jump.
- `navigationTransition(.zoom(sourceID:in:))` plus `matchedTransitionSource(id:in:)`
  (iOS 18+) is the system zoom push. Gating this behind iOS 26 needlessly drops it for
  earlier releases.
- Custom `Transition` conformances get an `isIdentity` phase; forgetting to check it makes
  the transition apply to the settled state as well.

## Animatable types

Use the `@Animatable` macro (iOS 26+) instead of hand-writing `animatableData`. It
synthesises the conformance from the animatable stored properties; mark anything that
cannot interpolate — `Bool`, `Int` used as a discrete mode, a string — with
`@AnimatableIgnored`.

```swift
@Animatable
struct Wedge: Shape {
    var startAngle: Angle
    var endAngle: Angle
    @AnimatableIgnored var clockwise: Bool

    func path(in rect: CGRect) -> Path { … }
}
```

Below iOS 26, `animatableData` with `AnimatablePair` is still the mechanism. Do not keep
`AnimatablePair` in code whose floor is already 26.

## Phase and keyframe animation

- `PhaseAnimator` cycles a view through a sequence of discrete states. The content closure
  takes **two** parameters: `{ content, phase in }`. A single-parameter closure does not
  compile — a common hallucination.
- The trigger-based initialiser runs the sequence once per trigger change; the
  trigger-less one loops forever. Picking the wrong one is the usual cause of
  "it animates once" or "it never stops".
- `KeyframeAnimator` drives several properties on independent timelines. Each track needs
  its own `KeyframeTrack(\.property)`; keyframes within a track are cumulative in time.
- Symbol animation is `symbolEffect(_:options:isActive:)` (iOS 17+), but individual
  effects carry their own floors — `.drawOn` / `.drawOff` are iOS 26. Gate the **effect's**
  floor, not the modifier's. There is no `symbolVariableColor(value:)` modifier; variable
  colour is `.symbolEffect(.variableColor…)`.

## Reduce Motion

The system tones down its *own* motion. It does not gate your `withAnimation`.

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

withAnimation(reduceMotion ? .none : .bouncy) { isExpanded.toggle() }
```

Gate per animated component, not once at app level — a single top-level check is a review
finding, because it leaves every component free to animate.

The replacement for a large motion is a cross-fade or an instant change, not a slower
version of the same movement. Parallax, scale-from-zero, and slide-across-screen are the
transitions users with vestibular sensitivity report as the worst.

`UIAccessibility.prefersCrossFadeTransitions` (UIKit, iOS 14+) reports the separate
"Prefer Cross-Fade Transitions" setting. There is no SwiftUI environment value for it —
`accessibilityPrefersCrossFadeTransitions` does not exist.

<!-- sources: avdlee-swiftui, yordi-liquid-glass, apple-xcode27, twostraws-swiftui -->
