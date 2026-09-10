# Widgets, layout and adaptive UI

## Contents

- [Widget rules](#widget-rules)
- [The constraint model](#the-constraint-model)
- [Layout error decoder](#layout-error-decoder)
- [Adaptive layout](#adaptive-layout)
- [Large screens](#large-screens)
- [Scrolling](#scrolling)
- [Debugging layout](#debugging-layout)
- [Failure catalogue](#failure-catalogue)

## Widget rules

1. `build` stays under ~40 lines. Longer means the screen wants sub-widgets.
2. Extract **widget classes**, never `Widget _buildHeader()` methods: a method
   cannot be `const`, rebuilds with its parent, and appears unnamed in DevTools.
3. `const` on every constructor the analyzer allows
   (`prefer_const_constructors`, `prefer_const_literals_to_create_immutables`).
4. `StatelessWidget` by default. `StatefulWidget` only for controllers
   (`TextEditingController`, `AnimationController`, `ScrollController`,
   `FocusNode`) and purely local UI state (expanded, hovered).
5. Prefer intent-revealing widgets over `Container`: `Padding`, `SizedBox`,
   `ColoredBox`, `DecoratedBox`, `Align`, `Center`. They are const-able and say
   what they do; `Container` earns its place only when combining several of them.
6. `Key` on every list item (`ValueKey(item.id)`) and on every widget a test
   taps. Without stable keys, reordering a list reuses the wrong state.
7. Theme values, not literals: `Theme.of(context).colorScheme.primary`,
   `textTheme.titleMedium`, spacing constants. A hard-coded `Color(0xFF...)`
   breaks dark mode silently.
8. At most ~6 constructor parameters; beyond that, group them into a value object.
9. Dispose in reverse creation order everything created in `initState`.
10. No `BuildContext` across an `await` without `if (!context.mounted) return;`.
11. Prefix widgets that return slivers with `Sliver` so misuse in a box context
    is visible at the call site.

## The constraint model

**Constraints go down. Sizes go up. The parent sets the position.**

A widget receives min/max width and height from its parent, chooses its size
within them, and the parent places it. Three consequences that explain most
layout bugs:

- A widget cannot be bigger than its constraints allow, no matter what you set.
  `SizedBox(width: 1000)` inside a 300px parent renders 300px wide.
- Unbounded constraints (inside a scrollable, a `Row`'s main axis, or an
  unconstrained `Column`) mean "as big as you want", and widgets that try to fill
  available space throw instead.
- `Expanded`/`Flexible` only work as direct children of `Row`/`Column`/`Flex`;
  `Positioned` only inside `Stack`.

## Layout error decoder

| Message | Cause | Fix |
|---|---|---|
| `A RenderFlex overflowed by N pixels` | child larger than the flex allows | wrap in `Expanded` (must fit) or `Flexible` (may shrink); for text add `overflow`/`maxLines` |
| `Vertical viewport was given unbounded height` | scrollable inside a `Column` | wrap in `Expanded`, give it a height, or turn the parent into a `CustomScrollView` |
| `An InputDecorator ... cannot have an unbounded width` | `TextField` directly in a `Row` | wrap in `Expanded`/`Flexible`/`SizedBox` |
| `Incorrect use of ParentDataWidget` | `Expanded`/`Positioned` not a direct child of its flex/stack | move it, or remove the intermediate widget |
| `RenderBox was not laid out` | cascade from an earlier constraint failure | fix the first error in the console, re-run |
| `setState() or markNeedsBuild() called during build` | state change or `showDialog` inside `build` | move it to a callback, or `WidgetsBinding.instance.addPostFrameCallback` |
| `The ScrollController is attached to multiple scroll views` | one controller shared by two scrollables | one controller per scrollable |
| `Duplicate GlobalKey detected` | the same `GlobalKey` in two live subtrees | use `ValueKey`/`ObjectKey` unless you genuinely need cross-tree identity |

Also: nesting `ListView` inside `Column` with `shrinkWrap: true` compiles and
"works", but lays out every child eagerly and disables lazy building — it is a
performance bug, not a fix. Use `Expanded`, or slivers.

## Adaptive layout

Measure the space, not the device:

- `LayoutBuilder` → `constraints.maxWidth` for decisions inside a subtree.
- `MediaQuery.sizeOf(context)` for the whole window (cheaper than
  `MediaQuery.of` — it only subscribes to size changes).
- Do **not** branch on `Platform.isAndroid`, "is tablet", or
  `MediaQuery.orientationOf`: apps run in split screen, free-form windows,
  foldables and picture-in-picture, where none of those track available space.
- Do not lock orientation. Locked apps get letterboxed on large-screen Android.

```dart
const largeScreenMinWidth = 600.0;   // Material's compact/medium boundary

LayoutBuilder(
  builder: (context, constraints) => constraints.maxWidth > largeScreenMinWidth
      ? const _TwoPaneLayout()
      : const _SinglePaneLayout(),
);
```

Also handle input diversity: hover states for pointers, `Shortcuts`/`Actions` for
keyboard, and focus traversal that follows the visual order.

## Large screens

- Constrain line length: `Center(child: ConstrainedBox(constraints: BoxConstraints(maxWidth: 800), child: ...))`.
  Full-width body text on a desktop window is unreadable.
- Turn long lists into responsive grids with
  `GridView.builder(gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent: 400))`,
  which changes column count with the window instead of hard-coding counts.
- Use `NavigationRail`/`NavigationDrawer` above the breakpoint and
  `NavigationBar` below it.
- Respect `SafeArea` and display cutouts; on desktop, respect the window's
  minimum size.

## Scrolling

- `ListView.builder`/`GridView.builder` for anything that can exceed one screen;
  `ListView(children: [...])` and `Column` build every child immediately.
- Mixed content that scrolls as one unit → `CustomScrollView` with
  `SliverAppBar`, `SliverList.builder`, `SliverToBoxAdapter`.
- `itemExtent` (or `prototypeItem`) on fixed-height lists lets the framework skip
  measuring every child, which is the cheapest scroll win available.
- Pagination: listen to a `ScrollController` and load ahead of the end, or use a
  sentinel item at the bottom of the builder.

## Debugging layout

```dart
import 'package:flutter/rendering.dart';
void main() {
  debugPaintSizeEnabled = true;   // temporary: paints layout bounds
  runApp(const MyApp());
}
```

- DevTools → Flutter Inspector → Layout Explorer shows the constraint each widget
  received and the size it chose; that answers "why is this 0 pixels wide".
- `debugDumpRenderTree()` from a breakpoint prints constraints and sizes as text.
- Hot reload preserves state; hot restart (`R`) resets it — a layout that only
  breaks after a hot reload is usually stale state, not a layout bug.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Widget ignores the size you set | parent's constraints are tighter; wrap in `UnconstrainedBox`, `Align`, or fix the parent |
| Everything rebuilds on a keystroke | one big `build` with no extracted widgets, or state held too high |
| List stutters while scrolling | eager `Column`, missing `itemExtent`, heavy work in `itemBuilder` |
| Row overflows only in one language | text length varies; use `Expanded` + `overflow`, never a fixed width |
| Layout breaks at 200% text scale | fixed-height containers around text |
| Bottom content hidden behind the keyboard | wrap the body in a scrollable, or use `resizeToAvoidBottomInset` correctly |

<!-- sources: flutter-official, sgruhier-flutter, evanca-rules -->
