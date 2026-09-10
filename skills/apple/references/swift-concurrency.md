# Swift concurrency

Verified against: Swift 6.2 / Xcode 26 toolchain.

Isolation, `Sendable`, structured concurrency, and Swift 6 migration. Diagnostics and
failure modes have their own reference.

## Contents

- [Read the build settings first](#read-the-build-settings-first)
- [Tool selection](#tool-selection)
- [Task entry isolation](#task-entry-isolation)
- [Actors](#actors)
- [Sendable](#sendable)
- [Swift 6.2 behaviour changes](#swift-62-behaviour-changes)
- [Migration loop](#migration-loop)
- [Escape hatches](#escape-hatches)

## Read the build settings first

Concurrency advice is wrong without the target's configuration. Read `Package.swift` or the
`.pbxproj` before proposing a fix — always, not only for migration work.

| Setting | SwiftPM | Xcode |
|---|---|---|
| Language mode | `swiftLanguageVersions` / `-swift-version` (the `// swift-tools-version:` line is not a proxy) | Swift Language Version |
| Strict concurrency | `.enableExperimentalFeature("StrictConcurrency=targeted")` | `SWIFT_STRICT_CONCURRENCY` |
| Default isolation | `.defaultIsolation(MainActor.self)` | `SWIFT_DEFAULT_ACTOR_ISOLATION` |
| Upcoming features | `.enableUpcomingFeature(...)` | `SWIFT_UPCOMING_FEATURE_*` |
| Approachable concurrency | individual upcoming features | `SWIFT_APPROACHABLE_CONCURRENCY` |

Projects created in Xcode 26 commonly start with `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`
and `SWIFT_APPROACHABLE_CONCURRENCY = YES`. Treat that as a likely default, not a confirmed
one — ask when the answer changes the advice. Under main-actor default isolation, a
`MainActor.run { }` or an added `@MainActor` may be a no-op, and neighbouring modules can
have different defaults.

## Tool selection

| Need | Tool | Note |
|---|---|---|
| One sequential async operation | `async`/`await` | default |
| Fixed, compile-time-known parallelism | `async let` | auto-cancelled on throw |
| Dynamic parallelism | `withTaskGroup` / `withThrowingTaskGroup` | children cancelled on scope exit |
| Sync → async bridge | `Task { }` | inherits actor context |
| Shared mutable state | `actor` | keep isolated sections small |
| UI-bound state | `@MainActor` | justify why it is UI-bound |
| Off-actor CPU work | `@concurrent` on an `async` function | not for ordinary I/O |

Prefer structured over unstructured. `Task { }` in a loop loses cancellation propagation,
error collection, and any way to await completion — that is a task group.

`Task.detached` is rarely correct. It sheds actor isolation *and* priority; usually the
author wanted `@concurrent` or a task group. Require a documented reason.

Never use Grand Central Dispatch in new app-level code. `DispatchQueue.main.async` is
`await MainActor.run { }` or main-actor isolation on the function. GCD remains legitimate in
low-level libraries, framework interop, and performance-critical synchronous sections where
a queue or lock is the right primitive — do not flag those.

Prefer `async`/`await` overloads over closure-based ones when an API offers both. Use
`Task.sleep(for:)`, never `Task.sleep(nanoseconds:)`.

## Task entry isolation

Match a `Task`'s entry isolation to its **synchronous prefix** — everything from `{` to the
first `await`.

```swift
// Prefix is empty; the first work hops away anyway.
Task { await loadOffMain() }

// Start off the main actor, hop back only for the UI mutation.
Task { @concurrent in
    let data = await loadOffMain()
    await MainActor.run { model.apply(data) }
}

// Prefix contains main-actor work — keep the inherited isolation.
Task {
    isLoading = true          // @MainActor, before any await
    await fetch()
}
```

A trivial non-main statement such as a `print` in the prefix is not a reason to add
`@concurrent`; the extra hop costs more than the line. For delayed retries and backoff,
separate the waiting from the UI mutation — the sleep usually belongs off the main actor
even when the final state update does not.

## Actors

- **Reentrancy is the default.** An actor method suspends at every `await`, and other calls
  run during that suspension. Any `check state → await → act on the check` sequence is a
  bug. Capture the awaited result into a local before writing, and deduplicate concurrent
  work by storing in-flight `Task` handles rather than by checking a cache twice.
- Force-unwrapping actor state after an `await` is a latent crash: another caller may have
  cleared it during the suspension.
- Keep isolated sections small. An actor whose methods do long synchronous work serialises
  every caller behind it.
- `@MainActor` is not a blanket fix. Justify why the type is genuinely UI-bound; otherwise
  the right boundary is a dedicated actor or a value type.
- Global-actor isolated conformances (Swift 6.2) let a `@MainActor` type satisfy a protocol
  while keeping the conformance actor-bound: `extension User: @MainActor Equatable`. Use it
  when the requirement really is main-actor-only; when the requirement must be callable from
  anywhere, remove the type isolation instead.
- A `deinit` on an actor-isolated class is **not** isolated by default, so touching isolated
  state from it is a compile error. Mark it `isolated deinit` when teardown must touch that
  state.
- `@Observable` cannot be applied to an `actor`. UI models are `@MainActor @Observable`
  classes.

## Sendable

`Sendable` describes what may cross an isolation boundary. Prefer, in order: immutable value
types; types whose stored properties are all `Sendable`; `actor`-protected state;
`sending` parameters that transfer ownership.

Region-based isolation often makes an explicit conformance unnecessary — if the sender
demonstrably stops using a value after passing it, the compiler accepts the transfer. Check
that before adding conformances.

`SendableMetatype` failures ("cannot satisfy conformance requirement for a 'Sendable' type
parameter") come from a conformance carrying global-actor isolation. Remove the isolation
from the conformance, or stop passing the metatype across the boundary.

## Swift 6.2 behaviour changes

- **`nonisolated` async functions stay on the caller's actor.** Calling a plain `async`
  helper from `@MainActor` code no longer hops off the main actor by itself. This removes a
  whole class of sending diagnostics — and it means "it's async, so it's in the background"
  is now false. Offload deliberately with `@concurrent`.
- **`@concurrent`** marks an `async` function that should leave the caller's actor for the
  concurrent pool. Use it for parsing, image processing, compression, large transforms. Do
  not use it for ordinary I/O, which already suspends.
- **Default main-actor isolation** can opt a whole module into `@MainActor`. Networking in
  other modules is unaffected — a common misunderstanding is that this puts URL loading on
  the main thread. It does not.
- **`Task.immediate`** runs the synchronous prefix before the caller continues instead of
  queueing. Task groups gained `addImmediateTask()`. Use only when that immediate start is
  the point.
- **Task names** (`Task(name:)`, `group.addTask(name:)`) are debugging aids that show up in
  Instruments and logs.
- **Priority escalation** is observable via `withTaskPriorityEscalationHandler`. Escalation
  is usually automatic; manual use is advanced coordination.

## Migration loop

Apply per change, never batched:

1. Build to surface diagnostics.
2. Fix **one category** at a time — all `Sendable` errors, then all isolation errors.
3. Rebuild and confirm the category is clear before moving on.
4. Run tests, especially actor-, lifetime-, and cancellation-sensitive ones.
5. Only then move to the next file or module.

If a fix introduces a new warning, resolve it before continuing. Optimise for the smallest
safe change; do not refactor unrelated architecture during a migration.

## Escape hatches

`@preconcurrency`, `@unchecked Sendable`, and `nonisolated(unsafe)` silence the compiler
without fixing anything. Each requires a documented safety invariant and a removal plan.

The only legitimate `@unchecked Sendable` is a type that is provably thread-safe through
internal locking or immutability. Applying it to a class with unsynchronised `var`
properties leaves the race in place and removes the diagnostic that would have found it.

Never use a semaphore or ad-hoc lock inside an async context to wait for async work; that
is how you deadlock the cooperative pool. Express ownership with an actor or `Mutex`.

<!-- sources: avdlee-concurrency, twostraws-concurrency, dimillian-skills, apple-docs -->
