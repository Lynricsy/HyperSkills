# Test smells

One catalogue, ordered by how much damage the smell does. Each entry: what it
looks like, why it costs you, and the fix. Use it when reviewing tests, or when
a test feels wrong and you cannot say why.

## Contents

- [Tests that cannot fail](#tests-that-cannot-fail)
- [Tests that fail for the wrong reason](#tests-that-fail-for-the-wrong-reason)
- [Tests coupled to the implementation](#tests-coupled-to-the-implementation)
- [Tests that are not isolated](#tests-that-are-not-isolated)
- [Tests nobody can read](#tests-nobody-can-read)
- [Suite-level smells](#suite-level-smells)
- [Warning signs while writing](#warning-signs-while-writing)

## Tests that cannot fail

| Smell | Why it costs you | Fix |
|---|---|---|
| Mirror assertion — expected value built by the code under test or its helper | Agrees with the code by construction; a wrong implementation stays green | Hand-derived literal or a checked fixture |
| Tautology — the assertion recomputes the production algorithm | Same defect; the test tracks the code instead of the contract | Assert a worked example from the spec |
| Self-comparison — `f(x)` compared to `f(x)` | Every deterministic implementation passes, correct or not | Assert the invariant that actually matters |
| Assertion on a double — the only assertion is that a mock was called or rendered | Passes because the double exists; fails only when the double is removed | Assert the outcome the caller observes |
| Crash-only assertion — `not.toThrow`, a bare non-null check, an async callback wrapped in a sync throw matcher | Fails only on a panic; wrong values sail through | Assert the value, or the rejection, explicitly |
| Coverage test — exercises a path and asserts nothing about its effect | Raises the coverage number and protects nothing | Assert a side effect, a return value, or delete it |

## Tests that fail for the wrong reason

| Smell | Why it costs you | Fix |
|---|---|---|
| Change detector on a decision — a constant, exact wording, private structure | Breaks on every rename, silent on real bugs | Test the behaviour that depends on the decision |
| Unreviewed snapshot | A large diff nobody reads becomes a rubber stamp | Snapshot only reviewed documents; assert fields otherwise |
| Sleep-based timing — `setTimeout` waits sized to the code's own timeout | Flaky by construction on a loaded machine; slows the suite | Control the clock, or wait on the condition with a bounded poll |
| Order-dependent test — passes alone, fails in the suite, or vice versa | Erodes trust in every red; people start re-running instead of reading | Set up and tear down its own state; never share mutable module state |
| Environment-dependent test — real network, real time zone, real locale | Fails on someone else's machine for reasons unrelated to the change | Inject the boundary; pin time, zone and locale |
| Assertion on framework mechanics | Fails when a dependency changes its internals, which is not your bug | Assert your boundary contract instead |

## Tests coupled to the implementation

| Smell | Why it costs you | Fix |
|---|---|---|
| Mocked internal collaborator | Freezes today's call graph; a refactor that keeps behaviour goes red | Use the real collaborator; mock only at system boundaries |
| Private method or private field under test | The unit has no seam; the test blocks the redesign it should survive | Test through the public interface, or extract the logic to its own unit |
| Side-channel verification — querying the database, reading a log, poking a field | Passes even when the interface the caller uses is broken | Read the result back through the interface |
| Test name describing how, not what — "calls repository.save" | Documents the implementation; renaming the method invalidates the spec | Name the behaviour: "persists the order so it can be read back" |
| Over-specified interaction — argument-by-argument, ordering, exact call counts everywhere | Every internal change is a test change | Keep the strict assertions where they are the contract; drop the rest |

## Tests that are not isolated

- Module-level mutable state shared by several tests. Reset it per test, or
  build it per test. A test that only passes when its neighbour ran first is a
  latent failure with a timer on it.
- A shared fixture mutated in place by one test. Build fixtures with a factory
  so each test gets its own.
- Leaked doubles: a spy installed in one test and never restored. Restore it in
  the test's own teardown, not in a global hook you have to remember.
- Real external services in what is nominally a unit test. It will fail on a
  train.

## Tests nobody can read

- Expected values hidden behind loops, builders or helpers. The reader cannot
  tell what the test claims without executing the helper in their head.
- Setup longer than the assertion, especially double setup. The unit is coupled
  or the seam is too deep.
- Several unrelated behaviours in one test with `and` in its name. The first
  failure hides the rest.
- Assertions on incidental output — a formatted string when only one field
  matters, a whole object when the test is about its status.
- DRY applied to tests until each test is a call into a shared scenario. Tests
  are documentation; some duplication is the price of reading one test in
  isolation.

## Suite-level smells

- A skipped or disabled test with no expiry and no linked issue. It is a
  deleted test that still shows up in the count.
- The same behaviour asserted at three levels because nobody deleted the older
  test. Keep the level that catches the realistic mutation.
- A test added because a rule required a test, protecting nothing. It costs
  maintenance forever; delete it.
- Coverage used as the target. Padding the number is easier than testing the
  behaviour, so that is what happens.
- Tests that never fail. If a suite has not gone red in months, it is not
  guarding the code; mutate something on purpose and find out.

## Warning signs while writing

Any of these mid-test means stop and rethink the test, not push through:

- Setup and assertion share the same object, guaranteeing equality.
- The test can fail only through a crash or a missing selector.
- The test fails on every intentional change and never on accidental breakage.
- The test greps source text, or asserts that a removed symbol stays removed.
- The test would still pass if the whole unit under test were deleted.
- An assertion names a mock, a stub or a fixture in its own text.
- A method exists that is only ever called from test files.
- Mock setup is more than half the test, or you cannot say why the mock is
  needed.
- You are mocking something "just to be safe".

<!-- sources: obra-tdd, mattpocock-tdd, addy-tdd -->
