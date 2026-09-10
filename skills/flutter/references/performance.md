# Performance: rebuilds, jank, memory

## Contents

- [Measure first](#measure-first)
- [Reading the numbers](#reading-the-numbers)
- [Rebuild cost](#rebuild-cost)
- [Raster cost](#raster-cost)
- [Lists](#lists)
- [Images](#images)
- [Isolates and heavy work](#isolates-and-heavy-work)
- [Memory and leaks](#memory-and-leaks)
- [Startup and app size](#startup-and-app-size)
- [Checklist](#checklist)

## Measure first

Profile-mode numbers are the only honest ones: debug mode runs unoptimised Dart
and is several times slower, so "it janks in debug" is not a finding.

```bash
flutter run --profile          # then open DevTools from the printed URL
flutter build apk --analyze-size --target-platform android-arm64
```

In DevTools: **Performance** (frame timeline, jank frames), **CPU profiler**
(where the time goes), **Memory** (allocations, leaks), **Widget rebuild stats**
(which widgets rebuild per frame).

## Reading the numbers

- Budget: 16.7 ms per frame at 60 Hz, 8.3 ms at 120 Hz. Each frame is split into
  a **UI** phase (Dart: build + layout + paint recording) and a **raster** phase
  (GPU: executing the display list).
- Long UI phase → your Dart code: too many rebuilds, expensive `build`, sync IO,
  JSON parsing on the main isolate.
- Long raster phase → the GPU: heavy clips, opacity layers, shadows, blurs,
  saveLayer, huge images.
- Shader jank on first run of an animation is a known iOS/Android startup effect;
  check whether the same animation is smooth the second time before optimising
  anything else.

## Rebuild cost

- `const` constructors let the framework skip the whole subtree during rebuild —
  the highest ratio of benefit to effort in Flutter.
- Rebuild the smallest widget that changes: extract a leaf widget and let it
  watch/select the one field it renders.
  - Riverpod: `ref.watch(p.select((s) => s.field))`
  - Bloc: `BlocSelector` or `context.select`
  - Provider: `Consumer`/`context.select`
- Hoist invariant subtrees into the `child:` parameter of `AnimatedBuilder`,
  `ListenableBuilder` or `ValueListenableBuilder`; the builder runs per tick, the
  `child` is built once.
- Do not allocate in `build`: no `DateFormat(...)`, no sorting, no regex
  compilation, no `Random()`. Hoist to a field or a provider.
- `setState` at the top of a screen for a change that affects one row is a rebuild
  of the whole screen; move the state down.

## Raster cost

- `RepaintBoundary` around a subtree that animates independently of its
  neighbours stops the rest from repainting. Check the "repaint rainbow" in
  DevTools before and after — a boundary in the wrong place adds a layer and
  costs more.
- Prefer `FadeTransition`/`AnimatedOpacity` over rebuilding with `Opacity`, and
  avoid `Opacity` on a large or animating subtree — it forces a `saveLayer`.
- `ClipRRect` on a scrolling list is expensive; use a `BoxDecoration` with
  `borderRadius` where possible.
- `BackdropFilter` and large `BoxShadow` blurs are the most expensive common
  widgets; limit their area.

## Lists

- `ListView.builder` with `itemCount`; never a `Column` of N children in a
  `SingleChildScrollView` for unbounded data.
- Give a fixed `itemExtent` or a `prototypeItem` when rows have uniform height:
  the viewport then computes scroll offsets without laying out children.
- `addAutomaticKeepAlives: false` and `addRepaintBoundaries: false` are
  micro-optimisations that usually hurt; measure before touching them.
- Keep `itemBuilder` cheap — no decoding, no formatting-heavy work; precompute in
  the state layer.
- `shrinkWrap: true` disables laziness. Use slivers instead when a list must live
  inside another scrollable.

## Images

```dart
Image.network(url, cacheWidth: 400)         // decode at display size
```

- Decoding a 4000×3000 photo into a 400px thumbnail costs ~48 MB of RAM per
  image. `cacheWidth`/`cacheHeight` (or `ResizeImage`) decode at the size you
  actually draw.
- `precacheImage(...)` in `didChangeDependencies` for hero/above-the-fold images
  so the first frame does not stall.
- `cached_network_image` adds disk caching and placeholders; plain
  `Image.network` caches only in memory for the session.
- Ship raster assets at the resolutions you declare (`2.0x`, `3.0x`); a single
  huge asset scaled down wastes both memory and bandwidth.

## Isolates and heavy work

```dart
final photos = await compute(parsePhotos, response.body);
```

- Anything that would take more than ~8 ms belongs off the UI isolate:
  `compute` for one-shot work, `Isolate.run` for the same in pure Dart, a
  long-lived isolate with a `SendPort` for repeated work.
- The function passed to `compute` must be a top-level or static function, and
  its argument and result must be sendable (no closures, no `BuildContext`).
- Plugin calls from a background isolate need
  `BackgroundIsolateBinaryMessenger.ensureInitialized(rootIsolateToken)` first.

## Memory and leaks

- Every controller, `AnimationController`, `StreamSubscription`, `Timer` and
  `FocusNode` created must be cancelled/disposed. The leak usually shows up as a
  `setState() called after dispose()` crash, not as memory pressure.
- Riverpod: `ref.onDispose`; Bloc: `close()`; widgets: `dispose()`.
- Watch the DevTools memory graph across a navigation loop (push → pop ×10):
  a staircase that never drops is a retained tree, most often a subscription or
  a static cache holding a widget/context.
- Do not cache `BuildContext`, widgets, or state objects in globals or singletons.

## Startup and app size

- Defer non-critical initialisation past the first frame
  (`WidgetsBinding.instance.addPostFrameCallback`) rather than awaiting it in
  `main`.
- Split rarely used assets into deferred components/loaded-on-demand data.
- `flutter build --analyze-size` shows what actually ships; large fonts and
  unreferenced assets declared with a directory wildcard are the usual surprises.
- `--split-debug-info` and `--obfuscate` shrink release binaries; keep the symbol
  files to decode crash reports.

## Checklist

| Symptom | First thing to check |
|---|---|
| Whole screen rebuilds on every keystroke | missing `const`, state held too high, no `select` |
| Scroll stutters | eager list, no `itemExtent`, heavy `itemBuilder` |
| Jank only during an animation | raster phase: opacity/clip/shadow layers, missing `RepaintBoundary` |
| Freeze on data load | JSON parsed on the UI isolate; move to `compute` |
| Memory climbs across navigation | undisposed subscription/controller, cached context |
| Slow cold start | synchronous work in `main`, oversized initial route |
| Huge APK/IPA | unused assets, uncompressed images, missing `--split-debug-info` |

<!-- sources: jeffallan-flutter, sgruhier-flutter, evanca-rules, flutter-official -->
