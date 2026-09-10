# Accessibility in Flutter

## Contents

- [What the framework gives you for free](#what-the-framework-gives-you-for-free)
- [Semantics](#semantics)
- [Text scaling](#text-scaling)
- [Targets, contrast and focus](#targets-contrast-and-focus)
- [Motion and timing](#motion-and-timing)
- [Automated checks](#automated-checks)
- [Manual verification](#manual-verification)
- [Failure catalogue](#failure-catalogue)

## What the framework gives you for free

Material and Cupertino widgets already publish semantics: `ElevatedButton`
announces its label and the button role, `TextField` announces its `labelText`,
`ListTile` merges its children into one node. Most accessibility bugs come from
replacing those widgets with a bare `GestureDetector` around a `Container`, or
from conveying meaning with colour or position only.

Prefer the semantic widget over a hand-rolled one; add `Semantics` only where a
custom widget has no built-in meaning.

## Semantics

```dart
Semantics(
  label: 'Play',                 // what a screen reader announces
  button: true,                  // role
  enabled: !isBusy,
  onTap: play,                   // action exposed to assistive tech
  child: const Icon(Icons.play_arrow),
)
```

| Situation | Do |
|---|---|
| Icon-only control | give the `IconButton` a `tooltip` (it becomes the semantic label) |
| Meaningful image | `Image(..., semanticLabel: 'Bar chart of monthly sales')` |
| Decorative image | `ExcludeSemantics` or `excludeFromSemantics: true` |
| Custom composite (avatar + name + badge) | `MergeSemantics` so it reads as one item |
| Live region (validation message, toast) | `Semantics(liveRegion: true, ...)` |
| Value that changes (slider, counter) | `Semantics(value: '$count items', ...)` |
| Purely visual duplicate of adjacent text | `ExcludeSemantics` to stop double reading |

Labels describe the action or content, not the widget: "Delete invoice", not
"trash icon button". Never put the same text in both a `Text` child and a
`Semantics(label:)` around it — it is announced twice.

Announce out-of-band changes explicitly:
`SemanticsService.announce('Item deleted', Directionality.of(context))`.

## Text scaling

- Never fix the height of a container that holds text; users set text scale far
  above 100%, and a fixed height clips or overflows.
- Use `Theme.of(context).textTheme` styles rather than hard-coded `fontSize`.
- Clamp only when a layout genuinely cannot cope, and clamp generously:

```dart
MediaQuery.withClampedTextScaling(
  maxScaleFactor: 1.6,
  child: child,
);
```

- Verify at scale in a widget test:

```dart
await tester.pumpWidget(MediaQuery(
  data: const MediaQueryData(textScaler: TextScaler.linear(2.0)),
  child: const MaterialApp(home: PriceTag()),
));
expect(tester.takeException(), isNull);       // no overflow
```

## Targets, contrast and focus

- Minimum interactive size is `kMinInteractiveDimension` (48 dp). A 24 dp icon
  needs padding or a `SizedBox`, not a smaller tap area.
- Contrast: 4.5:1 for body text, 3:1 for large text and meaningful icons. Colour
  alone never carries meaning — pair red with an icon or text.
- Keyboard and switch users need a visible focus indicator (`FocusableActionDetector`,
  or keep Material's default) and a traversal order that matches the visual one;
  fix mismatches with `FocusTraversalOrder`/`FocusTraversalGroup`.
- Dialogs and sheets should trap focus and restore it on dismiss; the Material
  ones do.

## Motion and timing

- Respect the platform reduce-motion setting:
  `MediaQuery.disableAnimationsOf(context)` (or `MediaQuery.of(context).disableAnimations`)
  → skip decorative transitions, keep state changes instant rather than removing
  feedback entirely.
- No auto-advancing carousels without a pause control; no timeouts that cannot be
  extended.
- Nothing flashes more than three times per second.

## Automated checks

```dart
testWidgets('meets accessibility guidelines', (tester) async {
  final handle = tester.ensureSemantics();
  await tester.pumpWidget(const MaterialApp(home: CheckoutPage()));

  await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  await expectLater(tester, meetsGuideline(iOSTapTargetGuideline));
  await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  await expectLater(tester, meetsGuideline(textContrastGuideline));

  handle.dispose();
});
```

These four guidelines from `flutter_test` catch the mechanical failures (tap
target size, missing labels, contrast) and cost one test per screen. They do not
catch a label that lies or a focus order that makes no sense.

Also useful: `flutter run` then the DevTools accessibility inspector, and
`SemanticsDebugger` wrapped around the app to see the semantics tree on screen.

## Manual verification

Run the flow three times: with TalkBack/VoiceOver only, with the keyboard only
(desktop/web), and with text scale at 200%. Every check that automation can do is
already in the test above; these three find the rest.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Screen reader says "button" with no name | `GestureDetector` around a bare `Container`; use a real button or `Semantics(label:)` |
| Everything read twice | text present both as a child and as a `Semantics` label |
| A card reads as six separate items | missing `MergeSemantics` |
| Overflow at large text scale | fixed-height box around text |
| Tap target guideline fails | icon smaller than 48 dp without padding |
| Contrast guideline fails | hard-coded colour instead of a theme colour pair |
| Error text never announced | validation message rendered without `liveRegion` |

<!-- sources: sgruhier-flutter, evanca-rules, flutter-docs -->
