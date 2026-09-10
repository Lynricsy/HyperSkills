---
name: apple
description: "Guides Apple platform development in Swift — SwiftUI views, data flow and @Observable, ForEach identity, navigation, animation, Liquid Glass (iOS 26+), Swift 6.x strict concurrency and actor isolation, SwiftData, accessibility (VoiceOver, Dynamic Type, Voice Control), localization, Swift Testing, UIKit/AppKit interop and scene lifecycle, and Instruments-based performance analysis of hangs and hitches. Covers iOS, iPadOS, macOS, watchOS, tvOS, visionOS and Xcode. Use when writing, reviewing, migrating or profiling Swift or SwiftUI code, when a build fails on a concurrency or availability diagnostic, or when adopting a new SDK. Do not use for Flutter or React Native apps, server-side Swift, or App Store submission and marketing."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.10"
  category: platform
---

Paths below are relative to this skill's directory.

## Scope

Swift and SwiftUI application code for iOS, iPadOS, macOS, watchOS, tvOS, and visionOS.
SwiftUI-first: UIKit and AppKit are covered where the two meet — hosting, representables,
scene lifecycle, macOS windows — not as an application architecture in their own right.

Default deployment target for new apps is **iOS 26** and its coordinated releases; Swift 6.2
or later with strict concurrency. iOS 27 is the newer SDK and its APIs are marked as such.

Not covered: server-side Swift, App Store submission, ASO, Core Data (SwiftData is the
default; say so rather than improvising), and cross-platform frameworks (`flutter`,
`react-native`).

Architecture is not prescribed. Do not push MVVM, VIPER, or Clean Architecture onto a
codebase. Encourage separating logic from views for testability without mandating how.
Performance work is a suggestion unless the user asked for a performance pass.

## Read first

`references/latest-apis.md`, at the start of every task. Soft-deprecated SwiftUI API
compiles without a warning, which is exactly why it survives in training data. That file is
the lookup table plus the rules for *when* to mention a soft-deprecated API you find.

## Core rules

Violations of these are bugs, not preferences.

1. `@State` is `private` and owned by the view that declares it. A value passed in by a
   parent is never `@State` or `@StateObject` — the property ignores every update after the
   first render.
2. `@StateObject` for view-created objects, `@ObservedObject` for injected ones; on iOS 17+
   prefer `@Observable` with `@State`, and `@Bindable` for an injected observable needing
   bindings.
3. `@Observable` classes are `@MainActor` unless the module sets main-actor default
   isolation, because views read them on the main actor during body evaluation.
4. `ForEach` identity is stable and unique: never `.indices`, `\.offset`, or an id derived
   from mutable content, and never an id minted inside `body`.
5. Each `ForEach` element produces a constant number of views, and `List` rows are unary.
6. Never store a closure in a custom `@Environment` or `@FocusedValue` key — closures cannot
   be compared, so every reader invalidates on every environment write.
7. `@Entry` defaults must be stable expressions; `Model()`, `Date()`, and `UUID()` re-evaluate
   on unrelated environment writes.
8. `.animation(_:value:)` always names the value it watches.
9. Never define or use an `.if(_:transform:)` view modifier: the branches are different view
   types, so structural identity breaks and descendant `@State` resets.
10. Factor sections into separate `View` structs, not computed properties — only a real type
    introduces a new invalidation boundary.
11. Keep `init` and `body` cheap; both run far more often than they look like they do.
12. Every tappable element is a `Button` with text, even when rendered icon-only.
13. iOS 26+ and iOS 27+ APIs are `#available`-gated **per platform** with a fallback, using
    each API's real floor rather than one combined guard.
14. New iOS 26 code gets Liquid Glass through standard components; adding a custom
    `glassEffect` surface to an existing app needs an explicit request from the user.
15. Two or more glass surfaces near each other share one `GlassEffectContainer` — glass
    cannot sample glass.
16. Never set `opacity < 1` on a glass view or any ancestor; refraction silently collapses.
17. Prefer structured concurrency. `Task { }` inside a loop is a task group; `Task.detached`
    needs a documented reason.
18. Any actor method that reads state, awaits, then acts on that read is a reentrancy bug —
    and force-unwrapping actor state after an `await` is a latent crash.
19. Never reach for `@unchecked Sendable`, `nonisolated(unsafe)`, or `@preconcurrency` to
    clear a diagnostic; each needs a documented invariant and a removal plan.
20. `ModelContext` and SwiftData model instances never cross actor boundaries — send a
    `PersistentIdentifier` and re-fetch.
21. Every SwiftData relationship gets an explicit delete rule and an explicit inverse.
22. Respect the user's settings: Dynamic Type over fixed sizes, semantic colours, never
    colour alone as a signal, and gate your own animations on `accessibilityReduceMotion`
    per component.
23. One type per file, folders grouped by feature.
24. Do not introduce a third-party framework without asking.
25. Report only genuine problems. Do not nitpick or invent issues.

## Workflows

### implement

- [ ] Read `references/latest-apis.md`.
- [ ] Design the data flow first: what this view owns versus what is injected
      (`references/swiftui-data-flow.md`).
- [ ] Structure the hierarchy for diffing — one `View` struct per section, narrow inputs
      (`references/swiftui-views-modifiers.md`).
- [ ] Pick navigation and presentation containers (`references/swiftui-navigation.md`).
- [ ] Gate every version-specific API with `#available` and write the fallback branch.
- [ ] Localise every user-facing string as a literal, with a translator comment where it
      interpolates (`references/swiftui-localization.md`).
- [ ] Give every control a label and check the layout at AX5
      (`references/accessibility.md`).
- [ ] **Gate — builds clean:** the target compiles with no new warnings, and previews are
      self-contained (no live services, no network).

### review

Run the steps in order, loading only the references the code touches. Report findings in the
output format below.

- [ ] Deprecated and soft-deprecated API (`references/latest-apis.md`).
- [ ] View structure, modifiers, and buttons (`references/swiftui-views-modifiers.md`).
- [ ] Data flow, ownership, observation granularity, bindings
      (`references/swiftui-data-flow.md`).
- [ ] `ForEach`, `List`, and `Table` identity (`references/swiftui-lists-foreach.md`).
- [ ] Navigation, presentation, focus, scrolling (`references/swiftui-navigation.md`).
- [ ] Animation correctness (`references/swiftui-animation.md`).
- [ ] Liquid Glass, if the code uses it (`references/liquid-glass.md`, and
      `references/liquid-glass-motion.md` when it animates). Say where glass should be
      *removed*, not only how it was applied.
- [ ] Design and layout resilience (`references/design-hig.md`).
- [ ] Accessibility (`references/accessibility.md`).
- [ ] Concurrency (`references/swift-concurrency.md`,
      `references/swift-concurrency-bugs.md`).
- [ ] SwiftData, if present (`references/swiftdata.md`).
- [ ] Tests (`references/testing.md`).
- [ ] **Gate — every finding is actionable:** each carries a file, a line, the rule it
      breaks, and a before/after. Findings without a fix are deleted.

### performance-trace

macOS only; `xcrun xctrace` ships with Xcode. Full interpretation guide in
`references/swiftui-performance.md`.

- [ ] **Run** `python3 scripts/record_trace.py --list-devices` and read the `kind` field.
      `simulators` means `--template "Time Profiler"`; the SwiftUI lane is empty on the
      Simulator.
- [ ] **Run** `python3 scripts/record_trace.py --device "<name|udid>" --attach "<App>"
      --stop-file /tmp/stop-trace --output ~/Desktop/session.trace`, then `touch` the
      stop-file when the user says they are done.
- [ ] Narrow the window if the user scoped the request: `scripts/analyze_trace.py`
      with `--list-logs` or `--list-signposts`, then `--window START_MS:END_MS`.
- [ ] **Run** `python3 scripts/analyze_trace.py --trace <path> --json-only --top 10`.
- [ ] Read `main_running_coverage_pct` per correlation: below 25% the main thread was
      blocked, at or above 75% it was CPU-bound.
- [ ] Ask who is invalidating a hot view:
      `python3 scripts/analyze_trace.py --trace <path> --fanin-for "<view>"`.
- [ ] **Gate — every recommendation cites evidence:** coverage percentage, hot symbol,
      overlapping view, or edge count. No evidence, no recommendation.

### migrate-to-swift6

- [ ] Read the target's language mode, strict-concurrency level, and default isolation
      before proposing anything (`references/swift-concurrency.md`).
- [ ] Build to collect diagnostics; map each to a fix
      (`references/swift-concurrency-bugs.md`).
- [ ] Fix **one category at a time** — all `Sendable` errors, then all isolation errors.
- [ ] Rebuild after each category; resolve any new warning before continuing.
- [ ] Prefer the smallest safe change. Do not refactor architecture during a migration.
- [ ] **Gate — clean build plus tests:** the target builds with strict concurrency and no
      remaining escape hatches, and the actor-, lifetime-, and cancellation-sensitive tests
      pass.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Deprecated API, iOS 26/27 additions | Always, first | `references/latest-apis.md` |
| View structure, modifiers, buttons, text | Building or reviewing a hierarchy | `references/swiftui-views-modifiers.md` |
| State, `@Observable`, environment, bindings | Data enters or leaves a view | `references/swiftui-data-flow.md` |
| `ForEach`, `List`, `Table` identity | Any data-driven container | `references/swiftui-lists-foreach.md` |
| Navigation, sheets, focus, scrolling | Screens connect or present | `references/swiftui-navigation.md` |
| Animation, transitions, phase/keyframe | Anything moves | `references/swiftui-animation.md` |
| Invalidation cost, Instruments traces | Profiling, hangs, hitches | `references/swiftui-performance.md` |
| String Catalogs, formatting, RTL | User-facing text | `references/swiftui-localization.md` |
| Liquid Glass material | `glassEffect`, toolbars, iOS 26 adoption | `references/liquid-glass.md` |
| Glass morphing, shaders, Reduce Motion | Glass animates | `references/liquid-glass-motion.md` |
| Layout resilience, HIG, platform idioms | Design decisions | `references/design-hig.md` |
| Isolation, `Sendable`, task structure | Concurrency code or Swift 6 migration | `references/swift-concurrency.md` |
| Concurrency diagnostics and failure modes | A build error or a race | `references/swift-concurrency-bugs.md` |
| `@Model`, `@Query`, predicates, CloudKit | SwiftData | `references/swiftdata.md` |
| VoiceOver, Dynamic Type, Voice Control | Accessibility work or review | `references/accessibility.md` |
| Swift Testing, XCTest migration, UI tests | Writing or reviewing tests | `references/testing.md` |
| Hosting, representables, scenes, macOS windows | UIKit or AppKit is involved | `references/uikit-appkit-interop.md` |

## Output format

Use exactly this shape for review workflows. Group by file, skip files with no findings, and
end with a prioritised summary.

### ContentView.swift

**Line 12: Use `foregroundStyle()` instead of `foregroundColor()`.**

```swift
// Before
Text("Hello").foregroundColor(.red)

// After
Text("Hello").foregroundStyle(.red)
```

**Line 24: Icon-only button is invisible to VoiceOver — give it a text label.**

```swift
// Before
Button(action: addUser) { Image(systemName: "plus") }

// After
Button("Add User", systemImage: "plus", action: addUser)
```

**Line 31: A value passed in by the parent must not be `@State` — updates are ignored.**

```swift
// Before
struct Row: View { @State var item: Item }

// After
struct Row: View { let item: Item }
```

### Summary

1. **Data flow (high):** `Row` on line 31 silently ignores every update after first render.
2. **Accessibility (high):** the add button on line 24 has no VoiceOver label.
3. **Deprecated API (medium):** `foregroundColor()` on line 12.

When the user asked for changes rather than a review, apply the same rules and edit the
files directly instead of returning a report.

## Environment

- Building, running, and previewing require **Xcode on macOS**. Nothing in this skill
  substitutes for a compile; state clearly when a claim was not verified by a build.
- `scripts/record_trace.py` and `scripts/analyze_trace.py` need `xctrace`, which ships with
  Xcode. They are **macOS only** and exit with an actionable message elsewhere. Both use
  only the Python 3.11+ standard library; run them with `python3` or `uv run`.
- Recording without `--attach` or `--launch` captures every process on the target. Explain
  that scope to the user and get approval before passing
  `--allow-system-wide-recording`.
- If the project has an Xcode MCP server configured, prefer its tools over generic ones —
  `Xcode:RenderPreview` for preview screenshots, `Xcode:DocumentationSearch` for current
  API documentation.
