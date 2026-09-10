# Mocking

Read this before substituting anything, and when mock setup starts growing
faster than the test.

## Contents

- [The ladder](#the-ladder)
- [Where a double is allowed](#where-a-double-is-allowed)
- [Mock at the right level](#mock-at-the-right-level)
- [Mirror the real structure completely](#mirror-the-real-structure-completely)
- [Make doubles specific](#make-doubles-specific)
- [Designing for substitution](#designing-for-substitution)
- [When to give up on doubles](#when-to-give-up-on-doubles)

## The ladder

Use the least substituted thing that does the job. Confidence drops at every
step down.

```
real implementation   highest confidence; catches real bugs
      v
fake                  in-memory implementation of the same interface
      v
stub                  returns canned data, no behaviour
      v
mock                  records interactions; the assertion target of last resort
```

A double is justified when the real dependency is slow, non-deterministic, or
has effects you cannot control or undo — charging a card, sending mail, the wall
clock, the random source. "It is easier to set up" is not on that list.

## Where a double is allowed

Substitute only at system boundaries:

- external services and third-party APIs
- the clock and the random source
- the database and the filesystem, when the real one is genuinely too slow for
  the loop — a project with a test database or a temporary directory should use
  it instead

Never substitute:

- your own modules and classes
- collaborators inside the unit under test
- anything you control and can construct cheaply

Mocking your own module freezes today's call graph into the test. The test then
fails on refactors that keep behaviour identical, and passes when the behaviour
breaks — exactly backwards.

## Mock at the right level

Learn every side effect of the real operation before replacing it. Substitute
the slow or external level and keep everything the test depends on real.

```typescript
// The double swallows the config write that duplicate detection reads,
// so the test passes while the feature is broken
vi.mock('ToolCatalog', () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined),
}));

// Only the slow server startup is substituted; the config write stays real
vi.mock('MCPServerManager');
```

When you are unsure what a real method does, run the test against the real
implementation once and watch what actually happens. Then substitute one level
lower than the thing you needed.

## Mirror the real structure completely

Build fixtures with every documented field of the real payload, not only the
fields this test reads. A partial fixture fails silently the moment downstream
code reads an omitted field: the test stays green and integration breaks.

Where the payload is large and versioned, keep one shared factory that returns
the complete shape and let each test override the two fields it cares about.
That keeps completeness and readability in the same place.

## Make doubles specific

When arguments, call counts or ordering are part of the contract, assert them —
a fake that accepts anything verifies nothing. Give each branch its own fixture
or spy so the wrong branch cannot satisfy the expectation:

- success, error and malformed-response each get their own double
- a rejection double rejects with the real error type, not a bare string
- a double that should never be called is asserted as not called, which is a
  real assertion about the code's decision

This is not a licence to assert on the double instead of the outcome. The
outcome the caller sees is the first assertion; the interaction is the second.

## Designing for substitution

**Inject the dependency.** A unit that constructs its own client cannot be
tested without patching the module system.

```typescript
// Substitutable at the call site
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Requires module patching, environment variables, and luck
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**Prefer an SDK-shaped interface over a generic fetcher.** One named function
per external operation, rather than one function taking an endpoint and
options.

```typescript
// Each operation is independently substitutable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// Substituting this needs conditional logic inside the double
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK shape gives each double one specific return shape, keeps branching out
of test setup, and makes it obvious from the test which endpoints a scenario
touches.

**Keep test-only lifecycle out of production types.** A `reset` or `destroy`
that exists so tests can clean up belongs in a test utility. Two questions: is
this called only from test files, and does this type own that resource's
lifecycle? Two wrong answers means it is a test utility.

## When to give up on doubles

Switch to a test with real components when any of these is true:

- the setup is longer than the behaviour under test
- the double is missing methods the real object has, and you keep adding them
- the tests break when the double changes, not when the code changes
- you cannot explain, in one sentence, why the double is there

At that point the cheaper test is the integration test: real collaborators, a
temporary directory or a test database, one substituted boundary at the edge.

<!-- sources: mattpocock-tdd, obra-tdd, addy-tdd -->
