# SwiftUI performance and Instruments traces

Verified against: iOS 26.6 SDK, Xcode 26 Instruments schemas.

Two halves: rules that reduce invalidation, and how to read a recorded
`.trace`. Present optimisations as suggestions unless the user asked for a
performance pass — most SwiftUI code is fast enough, and speculative
restructuring costs readability.

## Contents

- [Reducing invalidation](#reducing-invalidation)
- [Body and init cost](#body-and-init-cost)
- [Equatable and POD views](#equatable-and-pod-views)
- [Images](#images)
- [Recording a trace](#recording-a-trace)
- [Reading the analysis](#reading-the-analysis)
- [main_running_coverage_pct](#main_running_coverage_pct)
- [The cause graph](#the-cause-graph)
- [Prioritising findings](#prioritising-findings)

## Reducing invalidation

- **Structural identity beats branching.** A ternary in a modifier argument keeps the same
  view; an `if`/`else` in the body produces `_ConditionalContent` and recreates the
  underlying platform view.
- **Extract real `View` structs**, not computed properties — only a separate type
  introduces a new invalidation boundary.
- **Pass fields, not aggregates.** A view handed a whole config object depends on every
  field of it.
- **Guard redundant writes.** SwiftUI does not compare before invalidating on `@State`
  assignment. In a hot path (scroll offsets, gesture updates, publisher output), compare
  first and assign only on a real change — especially for thresholds:
  `if shouldShow != shouldShowTitle { shouldShowTitle = shouldShow }`.
- **Make `@Observable` property types `Equatable`** so the generated setter can skip
  no-op writes.
- **Avoid `AnyView`.** It erases the type SwiftUI diffs on. Use `@ViewBuilder`, `Group`,
  or generics.
- **`LazyVStack` / `LazyHStack`** for long content inside a `ScrollView`. `List` is already
  lazy.
- **`task(_:)` over `onAppear`** for async work — it is cancelled when the view disappears.
- **`scrollContentBackground(.visible)`** when a `ScrollView` sits on an opaque static
  background; it lets the system take the cheaper scroll-edge path.
- **Store built views, not escaping `@ViewBuilder` closures**, on custom containers.

## Body and init cost

Assume `body` and `init` run constantly. Move sorting, filtering, decoding, and formatting
out of both. Derive with a `let` from the source of truth, or precompute on the model.
Caching a derived collection in `@State` means you now own invalidation, and stale UI is
the failure mode.

Do not create formatters as stored properties. `Text(value, format: …)` is cached by the
framework and locale-aware.

`_logChanges()` on a view prints which dependency triggered each update — the fastest way
to answer "why did this re-render" without a trace.

## Equatable and POD views

A view whose stored properties are all simple value types with no property wrappers is
"plain old data" and diffs with `memcmp` — the fastest path. Adding `@State` takes a view
off that path, so an expensive leaf can be wrapped: a POD outer struct that forwards to a
private inner view holding the state. The outer comparison then short-circuits most
updates.

For an expensive body whose real dependency is narrower than its stored properties,
conform to `Equatable` and apply `.equatable()`. This is a maintenance liability: adding a
stored property without updating `==` produces a view that stops updating. Use it only
where a trace shows the body is genuinely hot.

## Images

Decode cost, not download cost, is usually the problem. Downsample at load time rather than
handing a full-resolution `UIImage` to a small frame — `.resizable().frame(...)` scales at
draw time and keeps the full bitmap in memory. Flag `UIImage(data:)` in a view path and
suggest downsampling through `CGImageSourceCreateThumbnailAtIndex`. `AsyncImage` applies
standard HTTP caching; use its `URLRequest` initialiser (iOS 27+) when you need a different
policy.

## Recording a trace

**macOS only** — `xcrun xctrace` ships with Xcode. Paths below are relative to this skill's
directory.

```bash
# Discover targets first; the "kind" field decides the template.
python3 scripts/record_trace.py --list-devices

# Attach to a running app on a real device.
python3 scripts/record_trace.py --device "<name|udid>" --attach "<AppName>" \
    --output ~/Desktop/session.trace
```

Template rule: the `SwiftUI` template (the default) only populates the SwiftUI lane on a
**real device** — a physical iOS/iPadOS device or the host Mac. On the iOS Simulator the
lane comes back empty; pass `--template "Time Profiler"` there, which still yields Time
Profiler, Hangs, and Animation Hitches. Check `--list-devices`: `kind: simulators` means
Time Profiler, `kind: devices` means the default is fine, `kind: devices offline` means ask
the user to connect and unlock the device.

For agent-driven sessions where the user says "tell me when you're done", pass
`--stop-file /tmp/stop-trace` and `touch` that path when they finish. The script sends
SIGINT to `xctrace` and waits for finalisation. `--time-limit 30s` self-stops instead.

`--all-processes` captures unrelated applications. Explain that scope, get explicit
approval, then pass `--allow-system-wide-recording` to record the acknowledgement.

## Reading the analysis

```bash
# Whole trace.
python3 scripts/analyze_trace.py --trace <path> --json-only --top 10

# Narrow to a slice discovered from a log line or signpost.
python3 scripts/analyze_trace.py --trace <path> --list-logs \
    --log-message-contains "loaded feed" --log-limit 5
python3 scripts/analyze_trace.py --trace <path> --list-signposts \
    --signpost-name-contains "ImageDecode"
python3 scripts/analyze_trace.py --trace <path> --json-only --window 10400:11700
```

`--window START_MS:END_MS` scopes every lane and correlation. Multi-run traces need
`--run N`; `--list-runs` prints the available ones.

Five lanes are analysed: `time-profiler`, `hangs`, `hitches`, `swiftui` (per-view update
cost and severity), and `swiftui-causes` (the attribute-graph edges). A lane reports
`available: false` when the template did not record it — that is information, not an error.

## main_running_coverage_pct

Each hang and each of the worst hitches gets a correlation entry. Time Profiler samples the
main thread about every 1 ms, so a window of N ms should yield roughly N main-thread
samples if main were running the whole time. Coverage is observed over expected.

| Coverage | Meaning | Where the fix is |
|---|---|---|
| < 25% | Main thread **blocked** — I/O, a lock, a synchronous XPC call, waiting on an actor | The listed `hot_symbols` are the moments main *was* running; look for the code that *starts* the blocking work and move it off the main actor |
| 25–75% | Mixed compute and blocking | Report both; usually a body doing work plus intermittent I/O |
| ≥ 75% | Main thread **CPU-bound** | `hot_symbols` point straight at the expensive code — hoist it out of bodies, cache it, or debounce the trigger |

System frames (`swift_`, `objc_`, `dyld`, `CA*`, `CF*`, `NS*`, `__open`) tell you *what* was
happening; the user-code frame one level up is what to change.

## The cause graph

The `swiftui` lane says what is expensive; `swiftui-causes` says why it keeps happening.
Signatures worth recognising in `top_sources`:

- `closure #1 in UserDefaultObserver.…send()` with thousands of edges — an `@AppStorage` /
  `UserDefaults` write fanning out to every reader. Read each key once high in the tree and
  pass values down, or move settings into one `@Observable`.
- `EnvironmentWriter: …` with a very high edge count — a modifier applied far too widely and
  reinstalled on every layout pass.
- `View Creation / Reuse` as the top source — the hierarchy is replacing children instead of
  mutating them. Look for unstable `ForEach` identity, `AnyView`, or conditional structure
  swaps.

Once a view shows up as expensive, ask who invalidates it:

```bash
python3 scripts/analyze_trace.py --trace <path> --fanin-for "<view name>"
```

## Prioritising findings

1. Hangs with coverage < 25% — blocking work on the main actor; almost always fixable.
2. Hangs with coverage ≥ 75% — CPU-bound main-thread work; fix the top symbols.
3. `swiftui-causes` sources with roughly a thousand edges or more — structural invalidation.
   One fix here often collapses many downstream hot views.
4. Hitches whose narrative is "Potentially expensive app update(s)", cross-referenced with
   `swiftui_overlapping_updates` to name the views rendering when the frame dropped.
5. High-severity SwiftUI events over ~16 ms: `onChange`, `Gesture`, `Action Callback`.
6. Heaviest views by total body time, even without a hitch.

Report each finding with its evidence — coverage percentage, hot symbol, overlapping view,
edge count — then a specific edit. Do not change code unless the user asked for edits.

<!-- sources: avdlee-swiftui, yordi-liquid-glass, twostraws-swiftui, dimillian-skills, apple-xcode27 -->
