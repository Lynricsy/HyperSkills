# Writing good tests

Read this before writing or changing an assertion, and before adding a test
double. Two gates govern everything here: a test names the break it catches,
and a test exercises the real thing.

## Contents

- [Gate 1 — name the break](#gate-1--name-the-break)
- [Derive expected values by hand](#derive-expected-values-by-hand)
- [Change detectors](#change-detectors)
- [Behaviour, not text](#behaviour-not-text)
- [Your code, not the framework](#your-code-not-the-framework)
- [Gate 2 — exercise the real thing](#gate-2--exercise-the-real-thing)
- [The mock never carries the assertion](#the-mock-never-carries-the-assertion)
- [Verify through the interface, not a side channel](#verify-through-the-interface-not-a-side-channel)
- [The mutation check](#the-mutation-check)
- [Quick reference](#quick-reference)

## Gate 1 — name the break

Before writing the body, answer: what production change should make this test
fail, and is that change a bug or a decision? A test earns its place by
catching a wrong branch, a missing side effect, a wrong argument, a boundary
case or a broken contract.

```
BEFORE writing the test body:
  Name the production change that would make this test fail.

  Cannot name one            -> redesign around an observable behaviour
  "The source text changed"  -> run the artifact and assert its effects
  Only a decision can break  -> change detector; test the behaviour that
                                depends on the decision

  Confirm the expected value is derived without the code under test.
  IF it reuses the code's logic or its helpers:
    replace it with a literal or a hand-checked fixture
```

Strict TDD produces both gates for free: a test written first and watched
failing against real code has already proven it can fail, and only earns a
double once the real dependency proves slow or external.

## Derive expected values by hand

Use literals and hand-checked fixtures. Table-driven cases with literal `want`
values are the preferred shape. An expectation computed by the code under test —
or by the same helper the code uses — passes no matter what that code does.

```typescript
// Mirror assertion: the same builder computes both sides, so it is always true
const expected = buildSearchQuery({ tag: 'urgent' });
expect(buildSearchQuery({ tag: 'urgent' })).toBe(expected);

// Hand-derived literal
expect(buildSearchQuery({ tag: 'urgent' })).toBe('tag:"urgent"');
```

The same defect wearing different clothes — the assertion re-implements the
production algorithm:

```typescript
// Tautological: the expected value is recomputed the way the code computes it
const expected = items.reduce((sum, i) => sum + i.price * i.qty, 0);
expect(calculateTotal(items)).toBe(expected);

// Independent: a total worked out once, by hand
expect(calculateTotal([{ price: 1099, qty: 2 }, { price: 250, qty: 1 }]))
  .toBe(2448);
```

Comparing a function to itself is the degenerate case, and it survives review
surprisingly often because it looks like a determinism test:

```typescript
// Passes for every deterministic implementation, including a wrong one
expect(calculateTotal(items)).toBe(calculateTotal(items));
```

If determinism is genuinely the contract — a cache key, an id generator — assert
the actual invariant (a stable literal, or equality across two different call
sites with different inputs), not self-equality.

## Change detectors

If only an intentional decision can fail a test — a constant's value, exact
message wording, private structure — it fires on every redesign and sleeps
through bugs. Test the behaviour that depends on the decision.

```typescript
// Change detector: guards the number 5
expect(MAX_RETRIES).toBe(5);

// Behaviour: guards the retry policy
const gateway = alwaysFailingGateway();
await expect(charge(order, gateway)).rejects.toThrow(/gateway/);
expect(gateway.attempts).toBe(5);
```

Snapshots are change detectors by default. A snapshot earns its place when the
output is genuinely a document (rendered markup, a generated file) and every
diff is reviewed; a snapshot nobody reads is a test that always agrees with the
code.

## Behaviour, not text

Asserting that a script, config or document contains an exact line proves only
that the source is the source. Run the artifact against controlled inputs and
assert its output, its side effects or its exit code. Prose written for humans
earns no test at all.

## Your code, not the framework

Test the contract your code makes at its boundaries: the route you register,
the query you emit, the payload you produce. Upstream mechanics belong to their
maintainers' tests — asserting that your router invokes a registered handler
tests the router, not you. When upstream behaviour genuinely surprised you,
write one narrow characterization test that names the assumption.

The same boundary applies inside your code. Constructors, getters, constants
and trivial forwarding earn a test only when they validate, normalize, default,
derive, enforce or cause a side effect. Otherwise assert the first
consumer-visible result that depends on them.

## Gate 2 — exercise the real thing

```
BEFORE adding a mock or a test helper:
  List the real method's side effects; keep the ones the test depends on
  real, and substitute the slow or external level below them.

  Mock responses mirror the complete real structure.

  A helper called only from tests lives in test utilities, not production.

  About to assert on the mock itself?
    unmock it, or delete the assertion.
```

## The mock never carries the assertion

An assertion on a double passes because the double is present and fails when it
is removed. It reports on the test setup, not on the component.

```typescript
// Asserts the mock exists
expect(view.getByTestId('sidebar-mock')).toBeTruthy();

// Asserts the real component's observable behaviour
expect(view.getByRole('navigation')).toBeVisible();
```

Call counts and arguments are worth asserting only when they are the contract
itself — a payment charged exactly once, an idempotency key forwarded unchanged.
Even then, the primary assertion is the outcome the caller sees; the call count
is the second assertion, not the only one.

An assertion that can fail only through a crash is the same problem from the
other side:

```typescript
// Cannot fail: an async callback's rejection never reaches not.toThrow
expect(async () => await checkout(cart, 'card_999')).not.toThrow();

// Names the contract, and can disagree with the code
await expect(checkout(cart, 'card_999')).rejects.toThrow(/declined/);
```

## Verify through the interface, not a side channel

Reading the database — or a private field, or a log line — to confirm an
operation happened couples the test to storage details and skips the interface
the caller actually uses.

```typescript
// Side channel: passes even if the read path is broken
await createUser({ name: 'Alice' });
const row = await db.query('SELECT * FROM users WHERE name = ?', ['Alice']);
expect(row).toBeDefined();

// Through the interface: proves the behaviour a caller depends on
const user = await createUser({ name: 'Alice' });
expect((await getUser(user.id)).name).toBe('Alice');
```

## The mutation check

Before finishing, mutate the production code in your head. At least one test
should fail for each realistic mutation:

- a wrong constant or a wrong argument
- the wrong branch handled
- a missing state change or side effect
- an empty or default return value
- missing validation for zero, empty, null, unauthorized or malformed input

A mutation that nothing catches marks the behaviour as unprotected — or the
test that claims to cover it as tautological. Run this over the slice you just
finished, not over the whole suite.

## Quick reference

| When you... | Do |
|---|---|
| Write any test | Name the break it catches — a bug, not a decision |
| Build an expected value | Derive it by hand; never with the code under test |
| Test a script or a document | Run it and assert its effects; never grep its text |
| Reach for a dependency test | Test your boundary contract, not their documented mechanics |
| Want to assert on a double | Assert the real component's outcome, or unmock it |
| Assert a call count | Assert the caller-visible outcome first, the count second |
| Confirm something was stored | Read it back through the public interface |
| Finish a slice | Run the mutation check |

<!-- sources: obra-tdd, mattpocock-tdd -->
