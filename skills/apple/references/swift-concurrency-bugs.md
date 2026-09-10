# Concurrency failure modes and diagnostics

Verified against: Swift 6.2 / Xcode 26 toolchain.

What to grep for, what the compiler is actually telling you, and how to test async code.

## Contents

- [Grep targets](#grep-targets)
- [Failure modes](#failure-modes)
- [Compiler diagnostics](#compiler-diagnostics)
- [Testing async code](#testing-async-code)

## Grep targets

| Pattern | What to check |
|---|---|
| `DispatchQueue.` | App-level code has a Swift concurrency equivalent. Low-level libraries and framework interop may legitimately keep it. |
| `Task.detached` | Sheds isolation *and* priority. Usually `@concurrent` or a task group was meant. |
| `Task {` inside a `for` loop | Fire-and-forget with no cancellation, no error collection, no completion. Use a task group. |
| `withCheckedContinuation` | Every path must resume exactly once. |
| `AsyncStream { continuation in … }` | Prefer `AsyncStream.makeStream(of:)`; verify the continuation finishes on every cleanup path. |
| `@unchecked Sendable` | Should be very rare. Does the type actually synchronise? |
| `MainActor.run {` | Often a no-op under main-actor default isolation, or a sign the function should just be `@MainActor`. |
| `await` inside an actor method that then writes state | Reentrancy: the pre-`await` check is stale. |
| a force unwrap after an `await` on actor state | Latent crash. |
| `Task.sleep(nanoseconds:` | Use `Task.sleep(for:)`. |
| `.value` on a `Task` inside a lock or semaphore | Deadlock risk in the cooperative pool. |

## Failure modes

**Actor reentrancy: check-then-act across `await`.**

```swift
// Bug: two callers both see nil and both download; a third clearing the cache
// during the suspension turns the force unwrap into a crash.
actor Cache {
    var data: [String: Data] = [:]
    func load(_ key: String) async throws -> Data {
        if data[key] == nil { data[key] = try await download(key) }
        return data[key]!
    }
}

// Fix: capture into a local, and deduplicate with in-flight task handles.
actor Cache {
    private var tasks: [String: Task<Data, Error>] = [:]
    func load(_ key: String) async throws -> Data {
        if let existing = tasks[key] { return try await existing.value }
        let task = Task { try await download(key) }
        tasks[key] = task
        return try await task.value
    }
}
```

**Continuation resumed zero times.** The callback never fires — the object deallocated, the
request timed out silently, an early return skipped handler registration. The caller hangs
forever with no diagnostic. Audit every path; add a timeout when the underlying API can drop
its callback. Always use the *checked* variant so misuse surfaces.

**Continuation resumed twice.** A success handler and a cancellation handler both resume.
`CheckedContinuation` traps at runtime; `UnsafeContinuation` is undefined behaviour.
Restructure so only one path reaches the continuation.

**Unstructured tasks in a loop.** No cancellation propagation, no error collection, no
completion signal. `withThrowingTaskGroup` gives all three.

**Swallowed errors in `Task` closures.** `Task { try await risky() }` drops the error
silently — the user sees nothing and the operation simply did not happen. Catch inside the
closure and surface the failure.

**Ignoring `CancellationError`.** Retrying or showing an alert for a cancellation treats a
normal lifecycle event (the view disappeared) as a failure. Check it first:

```swift
do { try await load() }
catch is CancellationError { }
catch { model.errorMessage = error.localizedDescription }
```

**Blocking the main actor with synchronous work.** More likely since Swift 6.2, because
`nonisolated` async functions now stay on the caller's executor. Offload with `@concurrent`.

**Unbounded `AsyncStream` buffer.** A producer faster than its consumer grows memory without
limit under the default `.unbounded` policy. Specify `.bufferingNewest(n)` or
`.bufferingOldest(n)`.

**`@unchecked Sendable` hiding a real race.** Applied to a class with unsynchronised `var`
properties, it removes the diagnostic and keeps the race.

**Retain cycles in long-lived tasks.** A `Task` stored on an object that captures `self`
strongly keeps the object alive until the task finishes. Cancel in `deinit` or capture
weakly at the boundary.

**`Thread.current` in async code.** Unavailable from async contexts, and the wrong mental
model: reason about isolation, not threads.

## Compiler diagnostics

**"Sending 'x' risks causing data races"** — a value crosses an isolation boundary while the
sender could still touch it. In order: check whether region isolation already accepts it
(often the sender simply stops using the value); mark the parameter `sending`; make the type
`Sendable` if it genuinely is; check whether `nonisolated(nonsending)` removes the hop
entirely. `@unchecked Sendable` last, and only with internal locking.

**"Static property 'x' is not concurrency-safe"** — a global reachable from several
isolation domains. Annotate the declaration `@MainActor`, or make it a `let` of a `Sendable`
type. `nonisolated(unsafe)` is for genuinely immutable state the compiler cannot prove, such
as C interop constants.

**"Capture of 'x' with non-sendable type in a `@Sendable` closure"** — pass the needed data
as a value rather than closing over the object (`let id = object.id; Task { use(id) }`),
make the captured type `Sendable`, or keep the work on the caller's actor.

**"Conformance of 'X' to protocol 'Y' crosses into main actor-isolated code"** — the type
and the protocol disagree about the call boundary. Either the type isolation is incidental
(remove it) or the conformance really is main-actor-only
(`extension X: @MainActor Y {}`). These are different choices, not interchangeable
suppressions.

**"Main actor-isolated conformance of 'X' to 'Y' cannot be used in nonisolated context"** —
move the use site onto the same actor, or drop the isolation from the conformance if the
requirements do not touch protected state.

**"Expression is 'async' but is not marked with 'await'"** — add `await`. Wrapping in
`Task { }` to avoid making the caller `async` is usually the wrong fix.

**SwiftLint `async_without_await`** — remove the `async`, or suppress narrowly with a
rationale when a protocol, an override, or `@concurrent` requires it. Never add a fake
`await` to satisfy the rule.

**Core Data warnings** — `NSManagedObject` must not cross contexts or actors. Pass an
`NSManagedObjectID` and re-fetch, or map to a `Sendable` value type. The same rule holds for
SwiftData's `ModelContext` and model instances.

## Testing async code

- Write async tests with Swift Testing; `@Test func` methods can be `async` and `throws`
  directly, and the suite `init()` can be too.
- Never assert by sleeping. Replace `Task.sleep` waits with a condition you can await:
  `confirmation` for "this callback fires N times", an `AsyncStream` you consume, or a
  continuation resumed by the code under test.
- `confirmation(expectedCount:)` is the Swift Testing equivalent of an XCTest expectation
  and fails if the count is wrong in either direction.
- Attach `.timeLimit(...)` to tests that could hang on a never-resumed continuation; a hung
  test is much harder to diagnose than a failed one.
- Swift Testing runs tests in parallel by default. Shared mutable fixtures need isolation —
  give each test its own instance via the suite `init()`, or use `.serialized` on the suite
  when the resource genuinely cannot be shared.
- Race detection: run the suite under the Thread Sanitizer in CI. Strict concurrency catches
  what it can prove; TSan catches the rest.
- Test cancellation explicitly. Start the operation, cancel the task, and assert that the
  effect did not land — cancellation bugs do not surface any other way.

<!-- sources: twostraws-concurrency, avdlee-concurrency, twostraws-testing, apple-docs -->
