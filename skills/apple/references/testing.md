# Testing

Verified against: Swift 6.2 / Xcode 26 toolchain.

Swift Testing for unit and integration tests; XCTest for UI tests, because Swift Testing
does not support them.

## Contents

- [Core conventions](#core-conventions)
- [Expectations](#expectations)
- [Parameterised tests](#parameterised-tests)
- [Traits and tags](#traits-and-tags)
- [Async and confirmations](#async-and-confirmations)
- [What to test in a SwiftUI app](#what-to-test-in-a-swiftui-app)
- [Structure](#structure)
- [XCTest migration](#xctest-migration)
- [UI tests](#ui-tests)

## Core conventions

- Suites are **structs**. Use a class only when you need subclassing or a `deinit`.
- `@Suite` is unnecessary on a type that merely contains `@Test` methods — the type is
  already a suite. Add it only to name the suite or attach traits.
- Setup is `init()`, teardown is `deinit` (classes only). There is no `setUp`/`tearDown`.
  The initialiser may be `async` and `throws`.
- Every suite must be constructible with no arguments, because it is reinstantiated per
  test. Stored properties need defaults or a custom `init()`.
- Test methods do not need a `test` prefix: `userCanLogOut()`, not `testUserCanLogOut`.
- Tests run in **parallel and in random order** by default. Any ordering dependency or
  shared mutable fixture is a bug. `.serialized` on a suite is the escape hatch, not the
  default.
- A test that reaches no `#expect` or `#require` passes. An "empty" test is a silent
  false positive.
- `@available` works on individual tests but **not** on suites. A suite of iOS 26 tests
  needs the attribute on each test.

## Expectations

- `#expect(condition)` records a failure and continues; `try #require(condition)` throws and
  stops the test. Use `#require` for preconditions whose failure makes the rest meaningless.
- **Never negate with a leading bang inside an expectation.** `#expect(!isLoggedIn)` defeats
  the macro's expansion and produces an unhelpful failure message. Write
  `#expect(isLoggedIn == false)`.
- `try #require(optional)` unwraps, replacing `XCTUnwrap`.
- `Issue.record("…")` is the manual failure, replacing `XCTFail`.
- `withKnownIssue { }` asserts that a failure *does* occur and fails when it does not — for
  a bug you have not fixed yet. `isIntermittent: true` inverts the strictness: it passes
  either way but marks an expected failure when one occurs, which is what you want for a
  flake you are actively investigating.
- Swift Testing has no built-in floating-point tolerance. Use Swift Numerics'
  `isApproximatelyEqual(to:absoluteTolerance:)` — and ask before adding the dependency if
  the project does not already have it.
- Add a message to `#expect` when the failure would otherwise be ambiguous. Not always, but
  usually worth it.

## Parameterised tests

```swift
@Test(arguments: [(32.0, 0.0), (212.0, 100.0), (-40.0, -40.0)])
func fahrenheitToCelsius(values: (input: Double, output: Double)) { … }
```

Two argument collections form a **Cartesian product**, not a pairwise zip, and the
combination count grows fast. For pairwise pairing pass `zip(a, b)` as the arguments.
Parameterised tests are the right answer for boundary tables; they are the wrong answer for
cases that need different assertions.

## Traits and tags

```swift
extension Tag { @Tag static var networking: Self }

@Test(.tags(.networking))
func fetchUserProfile() async throws { … }
```

Tags cross suite boundaries, so filtering by tag selects tests wherever they live. Useful
tags in practice: `.networking`, `.slow`, `.smoke`, `.edgeCase`.

Other traits worth reaching for: `.timeLimit(…)` for anything that could hang,
`.enabled(if:)` and `.disabled("reason")` instead of commenting a test out, and
`.serialized` on suites with an unavoidable shared resource.

Raw identifiers (Swift 6.2) allow ``@Test func `Strip HTML tags from string`()``. Suggest
them as a way to remove duplicated description strings, but do not adopt them by surprise
in a project that does not already use them.

## Async and confirmations

- `@Test func` may be `async` and `throws` directly; there is no expectation-and-wait dance.
- `confirmation(expectedCount:)` replaces `XCTestExpectation`. It accepts a **range**
  (`5...10`, or a partial range) as well as an exact count, and fails outside it.
- Never assert by sleeping. Replace a `Task.sleep` wait with something you can await: a
  confirmation, an `AsyncStream` you consume, or a continuation resumed by the code under
  test. Timing-based tests are the main source of CI flakes.
- Put a `.timeLimit(…)` on tests that touch continuations — a never-resumed continuation
  hangs the run instead of failing it.

## What to test in a SwiftUI app

Never test views directly. They depend on `@State`, the environment, and layout, and they
behave unpredictably outside a running app.

Test the model. `@Observable` classes are directly testable — construct one, drive it, read
its properties. If the logic lives inside a view body, *suggest* extracting it rather than
refactoring the app under the guise of adding tests.

Expose hidden dependencies. Production code that reaches for `URLSession.shared` or
`UserDefaults.standard` internally cannot be tested without hitting the network or the
user's defaults. Inject the dependency at the boundary; a protocol is one option, and a
closure property is often lighter.

Generate, per unit under test: the happy path, the boundaries, invalid input, and — where
concurrency is part of the contract — a cancellation test.

## Structure

Mirror the production layout: a production `Extensions/URLSession-Decodable.swift` gets a
test file at the same relative path in the test target. Apply this to new tests; do not
restructure an existing test target without asking.

Keep fixtures in dedicated files, alongside the tests that use them once there are enough
of them to vary per area.

Prefer one behaviour per test. Several `#expect` lines are fine when they describe one
behaviour from different angles.

## XCTest migration

Do **not** rewrite existing XCTest suites unless asked. When asked:

| XCTest | Swift Testing |
|---|---|
| `XCTAssertEqual(a, b)` | `#expect(a == b)` |
| `XCTAssertTrue(x)` / `XCTAssertFalse(x)` | `#expect(x)` / `#expect(x == false)` |
| `XCTAssertLessThan(a, b)` | `#expect(a < b)` |
| `XCTAssertIdentical(a, b)` | `#expect(a === b)` |
| `XCTAssertThrowsError` | `#expect(throws:)` |
| `XCTUnwrap(o)` | `try #require(o)` |
| `XCTFail("m")` | `Issue.record("m")` |
| `XCTestExpectation` + `wait` | `await confirmation { }` |
| `setUp` / `tearDown` | `init()` / `deinit` |
| `XCTSkip` | `.enabled(if:)` / `.disabled(…)` |

Convert in this order: keep the same type names (class to struct) and the same test methods
(drop the `test` prefix, add `@Test`), swap assertions for expectations, then look for
places parameterised tests collapse duplication, then add `#require` preconditions, and add
traits last.

## UI tests

Swift Testing does not support UI tests. `XCUIApplication` and `XCTestCase` remain the tool
there, and that is not a legacy choice.

UI tests are slow and flaky relative to unit tests. Use them only for what genuinely cannot
be covered lower down: navigation flows across screens, system-integration surfaces such as
share sheets or permission prompts, and launch-critical paths.
`XCUIApplication.performAccessibilityAudit()` is a high-value UI test because it checks
something unit tests structurally cannot.

<!-- sources: twostraws-testing, avdlee-testing, apple-xcode27, apple-docs -->
