# Network interception and time

Verified against: Playwright 1.63.0.

## Contents

- [What to mock, and what never to](#what-to-mock-and-what-never-to)
- [Routes must exist before the request](#routes-must-exist-before-the-request)
- [`route` and `fulfill`](#route-and-fulfill)
- [Modifying rather than replacing](#modifying-rather-than-replacing)
- [Scope, ordering and removal](#scope-ordering-and-removal)
- [Waiting on a response](#waiting-on-a-response)
- [HAR record and replay](#har-record-and-replay)
- [Asserting on requests the app makes](#asserting-on-requests-the-app-makes)
- [Time: `page.clock`](#time-pageclock)
- [Locale, timezone and other emulated context](#locale-timezone-and-other-emulated-context)
- [The `request` fixture for setup and teardown](#the-request-fixture-for-setup-and-teardown)
- [Review checklist](#review-checklist)

## What to mock, and what never to

The default is not to mock. An end-to-end test's value comes from running the real stack; every
stub narrows what the test proves.

Mock what you do not own:

- payment providers, identity providers, address lookup, mapping, captcha;
- analytics, session replay, chat widgets, ad tags — these make CI slow and noisy and prove
  nothing about the product;
- anything with a rate limit, a cost per call, or a sandbox that is itself unreliable;
- an error path you cannot provoke for real (a 503 from a dependency, a malformed payload).

Do not mock your own API. A test that stubs its own backend and drives its own frontend is a
component test wearing an end-to-end test's costume: it runs a browser, waits for a network round
trip that never happens, and would still pass if the real endpoint were deleted. If the intent is
to test the frontend against a fixed payload, write a component test and get it in milliseconds.

The one legitimate exception on your own API is provoking a response you otherwise cannot: a 500,
a timeout, a paginated edge case. Keep those tests few, and name them for the condition they
force.

## Routes must exist before the request

Verified. Registering the route after `goto` misses the request the page issues during load, and
the page falls into its error branch:

```ts
test('route registered after goto misses the in-flight request', async ({ page }) => {
  await page.goto('/api.html');
  await page.route('**/api/items', r => r.fulfill({ json: { items: ['too-late'] } }));
  await expect(page.locator('#out')).toHaveText('ERR');   // passes — the mock never applied
});
```

The correct order, also verified:

```ts
test('route fulfils the api call', async ({ page }) => {
  await page.route('**/api/items', r => r.fulfill({ json: { items: ['mocked-a', 'mocked-b'] } }));
  await page.goto('/api.html');
  await expect(page.locator('#out')).toHaveText('mocked-a,mocked-b');
});
```

The same ordering rule applies to `page.on('dialog')`, `page.on('download')`,
`page.waitForResponse` and `page.waitForEvent('popup')`: the handler or promise must be in place
before the action that triggers the event. A dialog handler registered after the click never runs,
and the click waits until the test times out because the dialog blocks the page.

For routes that must apply to every test, register them in a fixture or in `context.route` rather
than repeating them:

```ts
export const test = base.extend({
  context: async ({ context }, use) => {
    await context.route('**/*.analytics.com/**', r => r.abort());
    await context.route('**/*.hotjar.com/**', r => r.abort());
    await use(context);
  },
});
```

## `route` and `fulfill`

```ts
// JSON body — `json` sets the content type for you
await page.route('**/api/orders', r => r.fulfill({ json: { orders: [] } }));

// status only
await page.route('**/api/orders', r => r.fulfill({ status: 503 }));

// a network failure rather than an HTTP error
await page.route('**/api/orders', r => r.abort('failed'));

// block a whole class of resource to speed a test up
await page.route(/\.(png|jpe?g|webp|woff2?)$/, r => r.abort());

// conditional: mock one case, let the rest through
await page.route('**/api/orders/**', async r => {
  if (r.request().url().endsWith('/999')) return r.fulfill({ status: 404 });
  return r.fallback();
});
```

`r.fallback()` passes the request to the next matching handler (or the network); `r.continue()`
sends it to the network immediately, skipping any remaining handlers. Getting these two confused is
the usual reason a "more specific" route never fires.

URL patterns accept a glob, a regexp or a predicate. Globs match the full URL, so `**/api/items`
matches any host — which is normally what you want and occasionally not.

## Modifying rather than replacing

Often the useful mock is the real response with one field changed, which keeps the rest of the
payload honest:

```ts
await page.route('**/api/cart', async r => {
  const response = await r.fetch();
  const body = await response.json();
  body.discountPct = 10;
  await r.fulfill({ response, json: body });
});
```

`r.fetch()` performs the real request from the test's context and hands back the response, so
status and headers are preserved. The same shape modifies the request instead:

```ts
await page.route('**/api/**', r =>
  r.continue({ headers: { ...r.request().headers(), 'x-test-run': runId } }));
```

## Scope, ordering and removal

- `page.route` applies to one page; `context.route` to every page in the context, including popups.
- Handlers registered later run first. A general handler added in a fixture and a specific one
  added in a test therefore work in the expected order, with the test's winning.
- `page.unroute(pattern)` removes one; `page.unrouteAll()` removes all. Needed when a test must
  observe the real behaviour after observing the mocked one.
- Routes do not survive a context, so a fixture that creates a fresh context per test starts clean.

## Waiting on a response

Create the promise first, then act:

```ts
const promoResponse = page.waitForResponse(
  r => r.url().includes('/api/promo') && r.request().method() === 'POST');
await page.getByRole('button', { name: 'Apply' }).click();
expect((await promoResponse).status()).toBe(200);
```

This is a legitimate wait, unlike `networkidle`: it names the exact request. Even so, prefer
asserting on the rendered result when one exists — `expect(discountRow).toHaveText('-10%')` proves
the user sees the discount, while a 200 only proves the server answered. Use the response waiter
when the assertion genuinely concerns the request (an analytics event fired, the right payload was
sent), or to get at a value the UI does not show.

## HAR record and replay

For an application with many third-party calls, recording once and replaying is less work than
writing individual routes:

```bash
npx playwright open --save-har=fixtures/checkout.har --save-har-glob='**/api/**' https://app.test
```

```ts
await page.routeFromHAR('fixtures/checkout.har', { url: '**/api/**', update: false });
```

`update: true` re-records on the next run, which is how the fixture is refreshed. Two caveats: a
HAR is a snapshot and will drift silently from the real API — schedule a run with `update: true`
and diff it — and a recorded HAR contains whatever was in the traffic, including tokens, so scrub
it before committing.

## Asserting on requests the app makes

Sometimes the requirement is about the request, not the response — an event was sent, a PATCH
carried the right body, no request was made at all:

```ts
const calls: string[] = [];
await page.route('**/api/tasks/*', async r => {
  calls.push(`${r.request().method()} ${new URL(r.request().url()).pathname}`);
  await r.fallback();
});

await page.getByRole('checkbox', { name: 'Write tests' }).check();
await expect.poll(() => calls).toContain('PATCH /api/tasks/42');
expect(r.request().postDataJSON()).toEqual({ status: 'completed' });
```

`expect.poll` rather than a bare `expect` on the array, because the request is asynchronous with
respect to the click.

## Time: `page.clock`

A test that depends on the current date, a countdown, a relative timestamp ("3 minutes ago") or a
polling interval needs the clock controlled, not tolerated. Playwright installs a fake clock into
the page:

```ts
await page.clock.install({ time: new Date('2026-03-01T10:00:00Z') });
await page.goto('/dashboard');
await expect(page.getByTestId('greeting')).toHaveText('Good morning');

await page.clock.fastForward('02:00');          // skip two hours of timers
await expect(page.getByTestId('greeting')).toHaveText('Good afternoon');

await page.clock.pauseAt(new Date('2026-03-01T23:59:50Z'));
await page.clock.runFor(20_000);                // cross midnight deliberately
```

`setFixedTime` freezes `Date` without touching timers, which is the lighter option when only the
displayed date matters. `install` replaces `Date`, `setTimeout`, `setInterval`,
`requestAnimationFrame` and `performance.now`, so the app's own polling is under test control too.

Do not hand-roll this with `addInitScript` and a `Date` subclass. That misses `performance.now`,
the timer functions and `Intl`, and it drifts from whatever the app actually reads.

`install` must run before the page script that captures `Date`, i.e. before `goto`.

## Locale, timezone and other emulated context

Set these in `use` so every test agrees, rather than tolerating both formats in assertions:

```ts
use: {
  locale: 'en-GB',
  timezoneId: 'Europe/London',
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
  colorScheme: 'light',
  reducedMotion: 'reduce',
}
```

`reducedMotion` is a top-level `use` option — not nested under `contextOptions`. It sets the
`prefers-reduced-motion` media feature, so it only helps if the application honours it; it does not
stop an unconditional CSS animation. For screenshot stability the relevant control is
`toHaveScreenshot(..., { animations: 'disabled' })`.

Permissions and geolocation are context-level too: `permissions: ['geolocation']` plus
`geolocation: { latitude: 51.5, longitude: -0.12 }`, or `context.grantPermissions` mid-test.

## The `request` fixture for setup and teardown

`request` is an HTTP client that shares the browser context's cookie jar. It is the fastest way to
create the data a test needs and to remove it afterwards, and it keeps the UI out of setup:

```ts
export const test = base.extend<{ order: Order }>({
  order: async ({ request }, use) => {
    const created = await request.post('/api/test/orders', { data: { lines: 1 } });
    const order = await created.json();
    await use(order);
    await request.delete(`/api/test/orders/${order.id}`);   // runs even if the test failed
  },
});
```

Teardown after `use()` runs whether the test passed or failed, which is what makes fixtures the
right home for resource lifecycle. A page object that creates records has no equivalent guarantee.

This is setup, not the test: a test whose *assertions* are all HTTP is an API test and does not
need a browser at all.

## Review checklist

- [ ] Nothing stubs the application's own API except to force an error that cannot be provoked.
- [ ] Third parties — analytics, chat, ads, maps, payments — are stubbed or aborted.
- [ ] Every route is registered before the navigation or action that triggers the request.
- [ ] Event waiters (`waitForResponse`, dialog, popup, download) are created before their trigger.
- [ ] `fallback()` versus `continue()` is used deliberately where handlers overlap.
- [ ] Date-dependent tests use `page.clock`, not tolerance or a hand-rolled `Date` patch.
- [ ] `locale`, `timezoneId`, `viewport` and `deviceScaleFactor` are pinned in config.
- [ ] Any committed HAR has been scrubbed of credentials and has a refresh plan.

<!-- sources: playwright-docs, playwright-runtime, ms-playwright-cli, currents-best-practices, testdino-playwright, lambdatest-playwright, addyosmani-devtools -->
