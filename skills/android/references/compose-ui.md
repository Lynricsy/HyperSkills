# Compose UI

## Contents

- [Designing a composable API](#designing-a-composable-api)
- [Slots](#slots)
- [Previews](#previews)
- [Theming](#theming)
- [Adaptive layout](#adaptive-layout)
- [Accessibility](#accessibility)

## Designing a composable API

- Name UI-emitting composables as nouns in `PascalCase` (`ArticleRow`), and composables
  that return a value or run an effect as verbs in `camelCase`
  (`rememberScrollBehavior`). A composable that both emits UI and returns a value is doing
  two jobs.
- A `modifier: Modifier = Modifier` parameter comes first among the optional parameters,
  and is applied to the outermost layout node exactly once. Without it the caller cannot
  size, pad or position your component.
- Required parameters first, then `modifier`, then other optionals, then a trailing
  content lambda.
- Hoist state: take the value and an `on<Verb><Target>` lambda instead of owning the
  state, and provide a stateful wrapper when the common case wants defaults.
- Extract a composable when a piece is reused, independently previewable, or has its own
  state; do not extract a two-line block that exists only to shorten the parent.
- More than about six parameters means the component is really two components, or wants a
  small state class.

## Slots

A slot parameter (`content: @Composable () -> Unit`) lets the caller decide what goes
inside without you enumerating every variation:

```kotlin
@Composable
fun Banner(
    title: String,
    modifier: Modifier = Modifier,
    leading: (@Composable () -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) { … }
```

This replaces the `showIcon: Boolean`, `iconRes: Int`, `iconTint: Color` parameter
explosion, and keeps the component's layout responsibility separate from the caller's
content decisions. Scoped slots (`content: @Composable RowScope.() -> Unit`) expose
layout capabilities such as `weight` to the caller.

## Previews

Previews are the fastest feedback loop in Compose and the input to host-side screenshot
tests. Preview the **stateless** composable with literal data, never the route composable
that needs a ViewModel.

```kotlin
@PreviewLightDark
@PreviewFontScale
@Composable
private fun ArticleRowPreview() {
    AppTheme { ArticleRow(article = sampleArticle, onClick = {}) }
}
```

`@PreviewScreenSizes` covers the adaptive breakpoints. Define a composite annotation once
per project rather than stacking four annotations on every preview. Use
`@PreviewParameter` with a provider for the state matrix (loading / empty / error /
content) instead of writing four preview functions.

## Theming

- Everything visual comes from `MaterialTheme.colorScheme`, `.typography`, `.shapes`. A
  hardcoded `Color(0xFF...)` in a component breaks dark mode, dynamic colour and any
  future rebrand at once.
- Dynamic colour (`dynamicLightColorScheme` / `dynamicDarkColorScheme`) is available from
  Android 12 (API 31); provide a static fallback scheme for older versions.
- Brand values that Material does not model belong in your own theme object provided
  through a `staticCompositionLocalOf`, not scattered as top-level constants.
- Do not read `isSystemInDarkTheme()` inside components to branch colours; pick the scheme
  once at the theme root and let components read semantic roles.
- When migrating from XML, map the existing theme attributes onto the `ColorScheme` roles
  before touching any layout, so the two rendering paths look identical during the
  transition.

## Adaptive layout

Decide from the window, never from the device type:

- `WindowSizeClass` (compact / medium / expanded) for the top-level navigation decision:
  bottom bar → navigation rail → permanent drawer.
- `BoxWithConstraints` or the window size for a component's own layout.
- Never branch on `Build.MODEL`, "isTablet" booleans, or orientation alone. Apps run
  split-screen, on foldables, and in resizable desktop and ChromeOS windows where those
  answers are wrong.

For two-pane patterns (list-detail, supporting pane), use the Material adaptive scaffolds
rather than hand-rolling the pane logic; they already handle the expanded/compact
transitions, back behaviour and pane restoration. Multi-pane navigation integrates with
Navigation 3 scenes.

Edge-to-edge and window insets are a platform-runtime concern rather than a layout one,
and are covered separately.

## Accessibility

- Every non-decorative `Image`/`Icon` needs a `contentDescription`; purely decorative ones
  take `null` so the screen reader skips them rather than announcing a filename.
- Touch targets are at least 48×48 dp. `Modifier.size` on an icon shrinks the target too;
  use `Modifier.minimumInteractiveComponentSize()` or pad the clickable.
- Merge a composite row into one announcement with
  `Modifier.semantics(mergeDescendants = true) { }`; four separate announcements per list
  row make a list unusable with TalkBack.
- Express state through semantics (`stateDescription`, `Role.Checkbox`, `toggleable`,
  `selectable`) rather than only through colour, so the state survives both TalkBack and
  colour-blindness.
- Text must reflow at font scale 2.0. Fixed `height` on a text container clips at large
  scales — constrain with `heightIn(min = …)` instead.
- `testTag` is not an accessibility label. Tags are invisible to accessibility services;
  a tag is a fallback for tests only, after semantic matchers fail.

<!-- sources: aldefy-compose, android-official, silvermoon-android, android-docs -->
