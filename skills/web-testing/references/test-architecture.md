# Test architecture

Verified against: Playwright 1.63.0.

## Contents

- [What deserves an end-to-end test](#what-deserves-an-end-to-end-test)
- [Component test or end-to-end test](#component-test-or-end-to-end-test)
- [Fixtures are the sharing primitive](#fixtures-are-the-sharing-primitive)
- [Page objects, with a threshold](#page-objects-with-a-threshold)
- [Page object anti-patterns](#page-object-anti-patterns)
- [`test.step`](#teststep)
- [One behaviour per test](#one-behaviour-per-test)
- [File, project and tag layout](#file-project-and-tag-layout)
- [`baseURL` and never a hardcoded host](#baseurl-and-never-a-hardcoded-host)
- [Setting up data](#setting-up-data)
- [Review checklist](#review-checklist)

## What deserves an end-to-end test

An end-to-end test costs a browser, a server, real latency and a maintenance burden that scales
with the UI's churn rate. It buys one thing nothing else buys: evidence that the tiers work
together in a real engine.

Spend it on:

- the journeys whose failure is a business incident — sign in, checkout, publish, invite;
- flows that cross a boundary no unit test covers — an upload that goes to storage and comes back,
  an OAuth redirect, a webhook that changes what the UI shows;
- interactions that only exist in a real browser — drag and drop, file pickers, clipboard, focus
  management across a modal, multi-tab flows;
- the handful of regressions that actually escaped to production, each as one test.

Do not spend it on:

- business logic reachable as a function — a rounding rule, a permission predicate, a reducer;
- API contracts — those are cheaper and more precise as HTTP tests;
- edge cases and permutation matrices — a parameterised unit test covers twenty cases in the time
  one browser test covers one;
- every field's validation message, which is a component test;
- appearance. A screenshot assertion is a narrow tool for a specific regression, not a way to test
  design (`frontend-design` owns how a page should look).

The practical test: if the assertion would still be meaningful with the browser removed, remove the
browser.

## Component test or end-to-end test

| Signal | Component test | End-to-end |
|---|---|---|
| The thing under test is one component's behaviour | yes | no |
| The assertion needs a real server and real data | no | yes |
| The interesting cases are many and cheap | yes | no |
| The flow spans several pages or a navigation | no | yes |
| The bug being prevented was an integration bug | no | yes |
| You are about to stub your own API to make it pass | yes — that is the signal | no |

That last row is the most useful one in review. A Playwright test that routes the application's own
endpoints to fixtures has paid for a browser and a server and then removed the server from the
test. It proves the frontend renders a payload, which is exactly a component test's job, with a
hundred times the latency.

Framework component internals — hooks, reactivity, stores — belong to the `react`, `vue`, `svelte`
or `astro` skill; the unit-testing methodology belongs to `test-driven-development`.

## Fixtures are the sharing primitive

If a suite only adopts one structuring mechanism, it should be fixtures. They compose, they are
lazy (created only when a test names them), and teardown after `use()` runs whether the test passed
or failed — which nothing else in the framework guarantees.

```ts
// tests/fixtures.ts
import { test as base, expect, type Page } from '@playwright/test';

type Fixtures = {
  order: { id: string };
  ordersPage: OrdersPage;
};

export const test = base.extend<Fixtures>({
  order: async ({ request }, use) => {
    const created = await request.post('/api/test/orders', { data: { lines: 1 } });
    const order = await created.json();
    await use(order);
    await request.delete(`/api/test/orders/${order.id}`);
  },

  ordersPage: async ({ page }, use) => {
    await use(new OrdersPage(page));
  },
});

export { expect };
```

```ts
import { test, expect } from './fixtures';

test('an order can be cancelled', async ({ order, ordersPage }) => {
  await ordersPage.goto(order.id);
  await ordersPage.cancel();
  await expect(ordersPage.status).toHaveText('Cancelled');
});
```

Scopes: the default is per-test; `{ scope: 'worker' }` creates once per worker and is the right home
for an expensive resource (a database client, a claimed account, a per-worker auth state). A
worker-scoped fixture receives `workerInfo`, whose `workerIndex` is the key for partitioning
shared resources such as accounts.

Module-level `let` is the thing fixtures replace. It looks like sharing and behaves like coupling:
it survives between tests in one worker and is empty in another, which is precisely the bug that
`--fully-parallel` exposes.

## Page objects, with a threshold

A page object is worth creating when both hold:

- the page or component has **5 or more** interactions the tests perform, and
- it appears in **3 or more** test files.

Below that, a plain helper function is smaller and clearer. The threshold exists because a page
object has a real cost: an indirection that has to be read to understand any test that uses it.

```ts
export class OrdersPage {
  readonly status = this.page.getByTestId('order-status');
  readonly cancelButton = this.page.getByRole('button', { name: 'Cancel order' });

  constructor(private readonly page: Page) {}

  async goto(id: string) {
    await this.page.goto(`/orders/${id}`);
    await expect(this.page.getByRole('heading', { name: 'Order' })).toBeVisible();
  }

  async cancel() {
    await this.cancelButton.click();
    await this.page.getByRole('button', { name: 'Confirm' }).click();
  }
}
```

Two things make this one worth its indirection: the methods express *intent* (`cancel()`, not
`clickButton('Cancel order')`), and the locators are exposed so tests can assert on them directly
rather than through a `getStatusText()` wrapper.

Inject page objects through fixtures rather than constructing them in each test — that way the
lifecycle stays in the fixture layer where teardown is guaranteed.

## Page object anti-patterns

- **Locator-only page objects.** A class whose entire body is public locators and no methods is a
  namespace with extra syntax. Either add intent-revealing methods, or skip the class.
- **Page objects that manage resources.** A `createOrder()` that posts to the API inside a page
  object has no teardown guarantee. Resource lifecycle belongs in a fixture.
- **Over-abstraction.** `clickButton(page, name)` and `getTitle()` wrappers add a layer and remove
  information — the reader now has to check whether `clickButton` does anything unusual.
- **A `BasePage` with shared getters.** Inheritance for `page` plus `navigate()` couples every page
  object to a hierarchy for two lines of reuse. Composition through fixtures is cheaper.
- **Assertions buried inside page objects.** A method that both acts and asserts makes the test
  unreadable — the test no longer says what it checks. The exception is a readiness assertion
  inside a `goto`, as above, which prevents a whole class of wrong-page failures.

## `test.step`

Steps group actions so that the report names the phase that failed rather than a line number:

```ts
test('a visitor can check out', async ({ page }) => {
  await test.step('add an item to the cart', async () => { /* ... */ });
  await test.step('apply the promo code', async () => { /* ... */ });
  await test.step('complete payment', async () => { /* ... */ });
});
```

This is worth doing for any test longer than about ten lines — in a trace and in the HTML report the
steps become the top-level timeline, which is a large improvement when triaging a failure someone
else's test produced.

Do not use steps to smuggle several tests into one. Steps are narration; if step 2 could fail for a
reason unrelated to step 1, they are separate tests.

## One behaviour per test

One behaviour, not one assertion. A checkout test may legitimately assert the confirmation appears,
the order id is shown and the cart is empty — those are one behaviour observed three ways. It may
not also assert that the promo code endpoint validates its input; that is a different behaviour and
belongs in its own test, where its failure is unambiguous.

Ordinal test titles (`01 - adds an item`, `02 - cart shows the item added by 01`) are the symptom of
the opposite: one behaviour split across several tests that depend on each other. Merge them into
one test, or give each one its own data.

Name tests for the behaviour and the outcome, not the mechanics: `a promo code reduces the total by
its percentage`, not `test promo`.

## File, project and tag layout

```
e2e/
  fixtures.ts
  auth.setup.ts
  checkout/
    guest-checkout.spec.ts
    promo-codes.spec.ts
  admin/
    tax-rules.spec.ts
  pages/
    orders-page.ts
```

- One spec file per feature or page; the file name matches the feature.
- Projects carry configuration differences (a role's storage state, a browser, a serialized admin
  group), not organisational ones.
- Tags are the selective-run mechanism: `test('checkout works', { tag: ['@smoke'] }, ...)` and
  `npx playwright test --grep @smoke`. Keep the tag vocabulary small — `@smoke` and `@slow` earn
  their place; a tag per team does not.
- `test.fixme` with an issue link for a test that is currently wrong; `test.skip(condition, reason)`
  for an environment that genuinely cannot run it. A bare `test.skip` is how a test dies quietly.

## `baseURL` and never a hardcoded host

```ts
use: { baseURL: process.env.BASE_URL ?? 'http://localhost:3000' }
```

Then every navigation is relative: `await page.goto('/orders')`. An absolute URL passed to `goto`
silently ignores `baseURL`, so one hardcoded `http://localhost:3000/...` in a spec makes that test
un-runnable against staging while every other test moves — and it fails with a connection error
rather than anything that names the cause.

## Setting up data

Order of preference:

1. **Through the API, in a fixture.** Fastest, most reliable, teardown guaranteed. Needs a
   test-only endpoint or an admin token.
2. **Through a seeded fixture dataset**, with each test claiming a record it alone owns (keyed on
   `workerInfo.workerIndex` or a generated id).
3. **Through the UI.** Only when the creation flow is itself under test. A test that creates its
   prerequisite through five pages of UI has five extra ways to fail for reasons unrelated to its
   assertion.

Whatever the mechanism, the test must not depend on a record another test also writes. Shared
mutable fixtures are the most common source of an isolation flake, and they get worse as the suite
and the worker count grow.

## Review checklist

- [ ] Every end-to-end test defends a journey whose failure matters; logic tests live lower down.
- [ ] No test stubs the application's own API to make itself pass.
- [ ] Shared state is a fixture, never a module-level variable.
- [ ] Page objects meet the 5-interactions-and-3-files threshold and expose intent, not wrappers.
- [ ] Resource creation and teardown live in fixtures, not in page objects.
- [ ] No ordinal test titles and no cross-test dependencies.
- [ ] `baseURL` in config; every `goto` relative.
- [ ] Long tests use `test.step` so the report names the failing phase.
- [ ] Skips and fixmes carry a reason or an issue link.

<!-- sources: currents-best-practices, testdino-playwright, awesome-copilot, lambdatest-playwright, playwright-docs, wshobson-e2e -->
