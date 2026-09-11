# Locators

Verified against: Playwright 1.63.0 (Chromium 153).

## Contents

- [The priority, and the reason for it](#the-priority-and-the-reason-for-it)
- [Accessible names are computed, not read off an attribute](#accessible-names-are-computed-not-read-off-an-attribute)
- [Strict mode](#strict-mode)
- [Narrowing: filter, and, or, scoping](#narrowing-filter-and-or-scoping)
- [`getByTestId` is a contract](#getbytestid-is-a-contract)
- [Laziness, re-resolution, and the staleness myth](#laziness-re-resolution-and-the-staleness-myth)
- [`visible()` and the `:visible` pseudo-class](#visible-and-the-visible-pseudo-class)
- [Frames and shadow DOM](#frames-and-shadow-dom)
- [Reading the page before writing the locator](#reading-the-page-before-writing-the-locator)
- [What not to use](#what-not-to-use)

## The priority, and the reason for it

Stop at the first that works:

1. `getByRole(role, { name })` — the accessibility tree. Stable across markup changes, and it
   fails when the element stops being announced correctly, which is a defect worth failing on.
2. `getByLabel(text)` — form controls. Equivalent to role+name for inputs, and more readable.
3. `getByPlaceholder(text)` — only where there is genuinely no label (and note that a
   placeholder-only field is itself an accessibility problem).
4. `getByText(text)` — non-interactive content: a heading, an error message, a total.
5. `getByTestId(id)` — a deliberate contract, see below.

The argument for this order is not style. A CSS descendant chain such as
`#product-list > li:nth-child(3) > div.card > button` encodes the DOM shape at the moment the test
was written: wrap the card in one more `div`, or reorder the list, and the test breaks while the
product still works. A role-based locator encodes what the user perceives, so it breaks exactly
when the user-visible contract breaks.

`getByRole` also takes `exact`, `level` (headings), `checked`, `selected`, `expanded`, `pressed`
and `disabled`, which is usually enough to avoid falling down the list:

```ts
page.getByRole('heading', { level: 2, name: 'Order summary' })
page.getByRole('checkbox', { name: 'Ship to billing address', checked: false })
page.getByRole('button', { name: /^Save$/ })   // regexp when the name has decoration
```

## Accessible names are computed, not read off an attribute

The name that `getByRole` matches comes from the accessible-name computation: `aria-label`, then
`aria-labelledby`, then a `<label>`, then the element's text content, then `title`, then `alt` on
an image inside it. Three consequences that produce confusing misses:

- An icon-only button with no `aria-label` has no accessible name, so
  `getByRole('button', { name: 'Delete' })` cannot find it even though the tooltip says Delete.
  That is a real defect; fix the component rather than switching to a CSS class.
- Whitespace and case are normalised, and matching is substring-and-case-insensitive by default.
  `{ name: 'save' }` matches `Save changes`. Pass `exact: true` or a regexp when that is too loose.
- Text inserted by CSS `::before`/`::after` is not in the accessibility tree, so a label that is
  visually present can be invisible to a role locator.

## Strict mode

Every Playwright locator is strict: resolving to more than one element is an error on use, not a
silent first match. The failure text names each match, which is usually the whole diagnosis:

```
Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Submit' }) resolved to 2 elements:
    1) <button class="btn" id="nav-submit">Submit</button> aka locator('#nav-submit')
    2) <button class="btn" type="button" id="form-submit">Submit</button> aka locator('#form-submit')
Call log:
  - waiting for getByRole('button', { name: 'Submit' })
```

Note the `aka locator(...)` suggestions — Playwright has already generated a unique locator for
each match. Note also the call log: the violation is reported *after* waiting, so a strict-mode
error on an element you expect to be unique sometimes means a second copy appeared late (a modal
duplicating the page's buttons, a virtualised list rendering twice during transition).

Resist `.first()`. It converts a genuine ambiguity into a dependency on document order, which is
the thing the locator was supposed to stop depending on. `.first()` is legitimate only where the
set is genuinely homogeneous and the intent is literally "any of these" — a row in a list of
identical skeleton placeholders, for instance.

## Narrowing: filter, and, or, scoping

Scope to a region rather than lengthening the selector:

```ts
const summary = page.getByRole('region', { name: 'Order summary' });
await expect(summary.getByRole('button', { name: 'Submit' })).toBeEnabled();
```

`filter` narrows by content or by a child:

```ts
page.getByRole('listitem')
    .filter({ hasText: 'Widget A1' })
    .getByRole('button', { name: 'Remove' })

page.getByRole('row').filter({ has: page.getByRole('cell', { name: 'Overdue' }) })
page.getByRole('row').filter({ hasNot: page.getByRole('cell', { name: 'Paid' }) })
```

`and` intersects two locators, which is how you express "the button that is also in this state"
without a CSS attribute selector. `or` expresses a genuine either/or — and it is the correct
replacement for a conditional assertion, because it still fails when neither appears:

```ts
const confirmation = page.getByRole('status').or(page.getByRole('alert'));
await expect(confirmation).toContainText('10%');
```

## `getByTestId` is a contract

`getByTestId` is last on the list, not forbidden. It earns its place for things with no meaningful
role or name: a chart canvas, a drag handle, a container whose only job is layout, a row that must
be identified by its record rather than its text.

Two rules make it honest:

- Add the attribute to the component on purpose, in the same change as the test. A test id that
  the application does not emit is a test that fails for the wrong reason.
- Reaching for it because the accessible name is missing hides an accessibility defect behind a
  passing test. Add the label, then locate by role.

The attribute name is configurable once, in the config, rather than per call:
`use: { testIdAttribute: 'data-qa' }`.

## Laziness, re-resolution, and the staleness myth

A locator is a description, not a reference. Nothing is queried when it is constructed; the query
runs on every use. So this is correct, and the reload does not invalidate anything:

```ts
const total = page.getByTestId('order-total');
await expect(total).toHaveText('$42.00');
await page.reload();
await expect(total).toHaveText('$42.00');   // fine — re-resolved
```

The thing that genuinely goes stale is a raw `ElementHandle` from `page.$`, `page.$$` or
`elementHandle()`. Playwright's own types mark `ElementHandle` use as discouraged in favour of
locators and web-first assertions, and there are two independent reasons:

- **No waiting.** `await page.$('#late:visible')` on an element that appears 1.5 s later returns
  `null` immediately — verified locally. Every handle-based flow therefore needs a wait bolted on
  in front of it, which is where fixed waits come from.
- **No strictness.** `page.$$('table.cart tbody tr')` returns however many rows had rendered at
  that instant, so `rows.length` is a sample, not an assertion. `expect(locator).toHaveCount(n)`
  retries until the count is right or the timeout expires.

## `visible()` and the `:visible` pseudo-class

`locator.visible()` (Playwright 1.63+) returns a locator narrowed to visible matches, and
visibility is re-checked on every use rather than at the moment of the call:

```ts
await page.locator('button').visible().click();       // the visible one of several
page.getByRole('row').filter({ visible: false });     // the inverse
```

This is the modern replacement for the `:visible` CSS pseudo-class inside a selector string, and
it composes with `filter` and `and`. It is a *narrowing* tool, not an assertion: to assert that
something is visible, use `expect(locator).toBeVisible()`.

## Frames and shadow DOM

Open shadow DOM is transparent to locators — `getByRole` pierces it, and no special API is needed.
Closed shadow roots are not reachable, by design.

Iframes need an explicit hop, and `frameLocator` composes with everything else:

```ts
const checkout = page.frameLocator('iframe[title="Secure payment"]');
await checkout.getByLabel('Card number').fill('4242 4242 4242 4242');
```

Two frame-specific traps: a frame that navigates invalidates work in progress inside it, so scope
the frame locator freshly rather than holding one across a navigation; and a third-party payment
or captcha frame is exactly the kind of dependency to stub rather than drive.

## Reading the page before writing the locator

Locators invented from a written description are guesses. Read the accessibility tree of the
running page instead — that is the same data `getByRole` matches against:

```ts
console.log(await page.locator('nav').ariaSnapshot());
```

```
- navigation:
  - button "Submit"
```

The same snapshot is the input to `toMatchAriaSnapshot`, so an exploratory pass produces both the
locators and the structural assertion. An agent driving a browser through a tool should prefer the
accessibility snapshot over a screenshot for the same reason: the snapshot carries the names and
roles that the locators will use, while a screenshot carries pixels.

## What not to use

| Instead of | Use | Why |
|---|---|---|
| `page.click('button[type=submit]')` | `page.getByRole('button', { name: 'Submit' }).click()` | The string-selector shorthand encodes markup and skips the role layer |
| `page.$('.badge')`, `page.$$('tr')` | `page.locator(...)` + `toHaveText` / `toHaveCount` | Handles neither wait nor enforce uniqueness |
| `div.card > button.primary` | a scoped role locator | Breaks on any refactor that adds a wrapper |
| `locator.first()` on an ambiguous match | `filter` / `and` / a scoped parent | Pins the test to document order |
| `:visible` inside a selector string | `locator.visible()` (1.63+) | Re-evaluated per use, composes with filters |
| `getByTestId` because the name is missing | add the accessible name, then `getByRole` | The missing name is the bug |
| XPath | role, text, or `filter({ has })` | Brittle and unreadable; acceptable only for a third-party widget with no other handle |

<!-- sources: playwright-runtime, playwright-docs, ms-playwright-cli, currents-best-practices, testdino-playwright, awesome-copilot, lambdatest-playwright -->
