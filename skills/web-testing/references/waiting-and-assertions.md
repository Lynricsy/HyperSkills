# Waiting and assertions

Verified against: Playwright 1.63.0.

## Contents

- [Why a fixed wait is a bug, not a slowdown](#why-a-fixed-wait-is-a-bug-not-a-slowdown)
- [Actionability: what each action already waits for](#actionability-what-each-action-already-waits-for)
- [Web-first assertions retry; awaited values do not](#web-first-assertions-retry-awaited-values-do-not)
- [`networkidle` and the other discouraged readiness signals](#networkidle-and-the-other-discouraged-readiness-signals)
- [Assertions that cannot fail](#assertions-that-cannot-fail)
- [Choosing the matcher](#choosing-the-matcher)
- [Structural assertions with `toMatchAriaSnapshot`](#structural-assertions-with-tomatchariasnapshot)
- [When no matcher fits: `expect.poll` and `toPass`](#when-no-matcher-fits-expectpoll-and-topass)
- [Soft assertions](#soft-assertions)
- [The timeout hierarchy](#the-timeout-hierarchy)
- [`AbortSignal` is not a timeout](#abortsignal-is-not-a-timeout)
- [Events whose promise must exist first](#events-whose-promise-must-exist-first)
- [The rewrite table](#the-rewrite-table)

## Why a fixed wait is a bug, not a slowdown

`page.waitForTimeout(n)` is often defended as "it just makes the test a bit slower". It does
something worse: it moves the assertion to a wall-clock offset that has no relationship to the
event being waited for. That fails in both directions.

A verified run against a page whose status field is written 800 ms after a click:

```ts
await page.locator('#form-submit').click();
await page.waitForTimeout(300);
expect(await page.locator('#status').textContent()).toBe('Saved');
```

```
Error: expect(received).toBe(expected) // Object.is equality
Expected: "Saved"
Received: ""
```

The same flow with a retrying assertion and no wait at all passes:
`await expect(page.locator('#status')).toHaveText('Saved')`.

The second failure mode is the one that does real damage. Raise the wait to `3000` and the test
passes — and now it also passes if the update takes 20 ms, if it takes 2900 ms, and if the app
regresses from 800 ms to 2500 ms. The wait has converted a functional assertion into a statement
that the value arrives *sometime within three seconds*, which is not what anyone wanted to test.

Playwright's own documentation for the method is unambiguous:
`Never wait for timeout in production. Tests that wait for time are inherently flaky. Use signals
such as network events, selectors becoming visible and others instead.`

The same argument rules out the hand-rolled version, which appears in almost every legacy suite:

```ts
let ok = false;
for (let i = 0; i < 10; i++) {
  if (await page.locator('div.confirmation').isVisible()) { ok = true; break; }
  await page.waitForTimeout(1000);
}
expect(ok).toBeTruthy();   // report says "expected true, received false" and nothing else
```

That is a reimplementation of the retry loop `expect` already runs, with a worse failure message.
One line replaces it: `await expect(page.getByRole('status')).toBeVisible({ timeout: 10_000 })`.

## Actionability: what each action already waits for

Actions do not fire immediately; each waits for its own set of actionability conditions, retrying
until the test or action timeout. This is why no pre-action visibility assertion is needed.

| Action | Waits for |
|---|---|
| `click`, `dblclick`, `tap` | attached, visible, stable (not animating), enabled, receives events (not obscured) |
| `fill` | attached, visible, enabled, editable |
| `type`, `pressSequentially` | attached, visible, enabled, editable |
| `check`, `uncheck` | attached, visible, stable, enabled, receives events |
| `selectOption` | attached, visible, enabled |
| `hover` | attached, visible, stable, receives events |
| `focus`, `blur`, `dispatchEvent` | attached only |
| `setInputFiles` | attached only |

So this pair is redundant, and the first line buys nothing:

```ts
await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();   // remove
await page.getByRole('button', { name: 'Save' }).click();
```

The distinction to keep in mind: *stable* means the element's bounding box has not changed between
two consecutive animation frames, and *receives events* means a hit test at the action point lands
on the element. A click that times out with `element is not visible` versus
`element intercepts pointer events` is telling you two different things — the second usually means
a toast, overlay or sticky header is in the way, which is a real UI defect worth reporting rather
than working around with `{ force: true }`.

`{ force: true }` skips actionability entirely. It is correct only when the intent is genuinely
"click this even though a user could not", which is almost never in an end-to-end test.

## Web-first assertions retry; awaited values do not

`expect(locator)` takes the locator and re-evaluates it until the matcher passes or
`expect.timeout` expires. `expect(await locator.something())` resolves the value once and asserts
on a snapshot. Verified on an element that appears 1.5 s after load:

```
ISVISIBLE_IMMEDIATE false     # await locator.isVisible()
AUTOWAIT_MS 1816              # await expect(locator).toBeVisible() — waited, then passed
TOBEVISIBLE_OK true
```

Playwright's type documentation says the same thing at the call site:
`If you need to assert that element is visible, prefer expect(locator).toBeVisible([options]) to
avoid flakiness.`

The rule generalises to every accessor. `expect(await locator.count()).toBe(3)` fails on a list
that is still rendering; `expect(locator).toHaveCount(3)` waits for it. `expect(await
locator.getAttribute('aria-expanded')).toBe('true')` samples once; `expect(locator).toHaveAttribute
('aria-expanded', 'true')` retries.

Accessors are still useful — for branching in *setup*, for logging, for computing a value the test
then acts on. They are not useful as the argument to an assertion.

## `networkidle` and the other discouraged readiness signals

`page.waitForLoadState('networkidle')` is frequently proposed as the "correct" replacement for a
fixed wait. It is not; Playwright marks it discouraged in the type definitions:

```
'networkidle' - **DISCOURAGED** consider operation to be finished when there are no network
connections for at least 500 ms. Don't use this method for testing, rely on web assertions to
assess readiness instead.
```

The mechanism: it waits for a 500 ms quiet period across all in-flight requests. An application
with a polling endpoint, an analytics beacon, a chat widget heartbeat or an open websocket never
produces that quiet period, so the call either burns the full timeout or — worse — returns at an
unrelated moment once the noise happens to pause. It is also the wrong question: "the network is
quiet" is not "the thing I am about to assert on exists".

`page.waitForSelector(sel, { state: 'visible' })` is the other common stand-in. It works, but it
is strictly weaker than the assertion that must follow it anyway: two statements where one will
do, and the wait's failure message describes a selector rather than an expectation.

`load` and `domcontentloaded` are fine as *navigation* semantics (`goto` waits for `load` by
default), and `commit` is useful when you want the navigation to start and intend to assert on a
loading state. None of them say anything about client-rendered content.

## Assertions that cannot fail

Four shapes recur, and all four report success regardless of the application's behaviour:

```ts
// 1. conditional assertion — if the banner never renders, nothing is checked
if (await banner.isVisible()) {
  expect(await banner.textContent()).toContain('10%');
}

// 2. existence guard — if the row never renders, the test passes
const first = await page.$('#orders > div:first-child');
if (first) { expect(await first.textContent()).not.toBe(''); }

// 3. try/catch around an assertion — swallows the only signal the test produces
try { await expect(total).toHaveText('$42.00'); } catch { /* flaky sometimes */ }

// 4. asserting a flag the test computed itself
expect(ok).toBeTruthy();
```

Shape 1 usually comes from a real ambiguity: the app shows either a banner or a toast. Express the
ambiguity in the locator, so the assertion still fails when neither appears:

```ts
await expect(banner.or(toast)).toContainText('10%');
```

Shape 2 is a handle plus a null check — replace both with `expect(locator).toHaveCount(1)` and then
assert on the content. Shape 3 is a quarantine decision disguised as code; mark the test
`test.fixme` with the issue link instead, so it is visible in the report. Shape 4 needs the
assertion to name the page state, not a boolean.

## Choosing the matcher

| Intent | Matcher | Trap |
|---|---|---|
| Element is in the DOM | `toBeAttached()` | Passes for `display:none` |
| Element is rendered and non-empty | `toBeVisible()` | An element with zero size is not visible |
| Element left the DOM | `not.toBeAttached()` | `not.toBeVisible()` also passes for still-present-but-hidden |
| Exact text | `toHaveText('Saved')` | Whitespace-trimmed but otherwise exact: `toHaveText('Sav')` fails against `Saved` (verified) |
| Substring | `toContainText('ave')` | Matches more than intended on short strings |
| List contents in order | `toHaveText([...])` | Array form asserts count *and* order |
| Count | `toHaveCount(n)` | `expect(await locator.count())` does not retry |
| Input value | `toHaveValue(v)` | `toHaveText` is empty for `<input>` |
| URL after navigation | `toHaveURL(/\/dashboard$/)` | Prefer over `waitForURL` + a second assertion |
| Enabled / editable | `toBeEnabled()`, `toBeEditable()` | `toBeEnabled` is false for `aria-disabled` too |
| Structure | `toMatchAriaSnapshot(...)` | See below |

## Structural assertions with `toMatchAriaSnapshot`

For "the page renders this structure" the accessibility tree is a better assertion target than a
pile of individual visibility checks: it covers roles, names, order and nesting in one expression,
and it fails with a readable diff.

```ts
await expect(page.getByRole('navigation')).toMatchAriaSnapshot(`
  - navigation:
    - link "Dashboard"
    - link "Orders"
    - button "Submit"
`);
```

Generate the initial snapshot from the running page with `await locator.ariaSnapshot()` rather than
writing it by hand. Keep the snapshot scoped to a region: a whole-page snapshot changes on every
unrelated edit and becomes the kind of test that gets regenerated without being read.

This complements `toBeVisible`, it does not replace it. One upstream source advises avoiding
`toBeVisible` in favour of structural matchers; that is not adopted here — `toBeVisible` is the
right assertion for "this appeared", and a structural snapshot is the right assertion for "the
region looks like this".

## When no matcher fits: `expect.poll` and `toPass`

`expect.poll` retries a function that returns a value, applying the ordinary matchers to it. Use it
for state that is not in the DOM — an API read, a database row, a queue depth:

```ts
await expect.poll(
  async () => (await request.get('/api/orders/42')).status(),
  { intervals: [500, 1000, 2000], timeout: 15_000 }
).toBe(200);
```

`expect(fn).toPass()` retries a whole block until it stops throwing, which is the escape hatch for
a composite condition:

```ts
await expect(async () => {
  const rows = page.getByRole('row');
  await expect(rows).toHaveCount(5);
  await expect(rows.first()).toContainText('Widget');
}).toPass({ timeout: 15_000 });
```

Neither is a substitute for a single web-first assertion — wrapping one assertion in `toPass` adds
a retry loop around a retry loop and makes the timeout arithmetic opaque.

## Soft assertions

`expect.soft` records a failure and continues, so one run reports every broken field instead of
only the first:

```ts
await expect.soft(page.getByTestId('subtotal')).toHaveText('$40.00');
await expect.soft(page.getByTestId('tax')).toHaveText('$2.00');
await expect.soft(page.getByTestId('total')).toHaveText('$42.00');
expect(test.info().errors).toHaveLength(0);   // or bail before an expensive step
```

Use it for a group of independent observations about one rendered state. Do not use it where a
later step depends on an earlier assertion holding — the test will continue into a state it has
already proven wrong and produce a second, confusing failure.

## The timeout hierarchy

| Setting | Default | Guidance |
|---|---|---|
| `timeout` (per test) | 30 000 ms | Leave it. A test that needs more is usually several tests |
| `expect.timeout` | 5 000 ms | Verified at 5010 ms. Raise to 10 000 for a genuinely slow app, not higher |
| `actionTimeout` | 0 (unbounded) | Leave unset — the test timeout bounds it. Verified: a click on a missing element ran 39 981 ms under `--timeout=40000` and failed with `Test timeout of 40000ms exceeded` |
| `navigationTimeout` | 0 (unbounded) | Leave unset for the same reason |
| `globalTimeout` | none | Useful in CI as a circuit breaker |
| `webServer.timeout` | 60 000 ms | Raise for a slow build step, not for a slow app |

The reason to leave action timeouts unset is that they control *how long a failure takes to
surface*, not whether it occurs. A config with `actionTimeout: 90_000`, `navigationTimeout:
120_000`, `expect.timeout: 60_000` and `timeout: 180_000` has not fixed a single race; it has
multiplied the cost of every failure and made the suite's wall time a function of its bugs.

Where a *specific* step is legitimately slow — a report generation, a video transcode — put the
timeout on that assertion (`{ timeout: 60_000 }`) and leave the globals alone. That way the
exception is documented at the line that needs it.

## `AbortSignal` is not a timeout

Actions and assertions accept a `signal`. The distinction is worth stating because the two are
easy to conflate: a timeout expresses *this should have happened by now*, and belongs in the
config; a signal expresses *we no longer care about this outcome*, and belongs in the test that
changed its mind — racing two possible flows, or abandoning a poll once another branch resolved.
Using a signal where a timeout belongs hides the missing deadline.

## Events whose promise must exist first

Response, request, popup and download waiters must be created before the action that triggers
them, or the event fires into a void:

```ts
const responsePromise = page.waitForResponse(r => r.url().includes('/api/promo') && r.ok());
await page.getByRole('button', { name: 'Apply' }).click();
const response = await responsePromise;
```

The same ordering applies to `page.route` and `page.on('dialog')`. Verified: a route registered
after `goto` misses the request the page issued during load, and the page falls into its error
branch. Dialog handlers registered after the click that opens the dialog never run, and the action
hangs until the test times out.

## The rewrite table

| Anti-pattern | Rewrite |
|---|---|
| `await page.waitForTimeout(n)` | the web-first assertion about what should have happened |
| `await page.waitForLoadState('networkidle')` | an assertion on the content that the load produces |
| `await page.waitForSelector(s, { state: 'visible' })` | `await expect(locator).toBeVisible()` |
| `expect(await locator.textContent()).toBe(x)` | `await expect(locator).toHaveText(x)` |
| `expect(await locator.count()).toBe(n)` | `await expect(locator).toHaveCount(n)` |
| `expect(await locator.isVisible()).toBe(true)` | `await expect(locator).toBeVisible()` |
| `if (await a.isVisible()) { ... } else { ... }` | `await expect(a.or(b)).toContainText(x)` |
| a `for` loop polling `isVisible()` | one `toBeVisible({ timeout })` |
| `try { await expect(...) } catch {}` | `test.fixme(...)` with the issue link |
| `await expect(x).toBeVisible()` then `await x.click()` | just `await x.click()` |
| raised `actionTimeout` to fix a flake | find the race in the trace |

<!-- sources: playwright-runtime, playwright-docs, currents-best-practices, testdino-playwright, awesome-copilot, lambdatest-playwright, anthropics-webapp-testing -->
