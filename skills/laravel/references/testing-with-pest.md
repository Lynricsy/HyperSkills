# Testing a Laravel application

Verified against: Laravel 13, Pest 4, PHPUnit 12. Every rule below has a PHPUnit equivalent; the
examples use Pest because the Laravel 13 skeleton installs it.

## Contents

- [What earns a test](#what-earns-a-test)
- [Naming and layout](#naming-and-layout)
- [Test data](#test-data)
- [Determinism](#determinism)
- [Assertions](#assertions)
- [Endpoint coverage](#endpoint-coverage)
- [Which layer owns which case](#which-layer-owns-which-case)
- [Suite speed](#suite-speed)
- [Reviewing a test](#reviewing-a-test)

## What earns a test

Test observable behaviour and application contracts: a test must still pass after an
implementation change that preserves behaviour. Cover every changed decision — a branch, a
validation rule, a calculation, an authorization check — plus the failure modes that matter.

Framework behaviour is already tested upstream. What the *project configures* is not framework
behaviour: a constrained relationship, a cast, a scope and a validation rule all belong to the
project and deserve tests.

Write a feature test first. A unit test is for logic that does not touch the framework. Before
writing anything, read the neighbouring tests — a pattern repeated across the suite is a
convention, and it outranks every default here. An existing test that follows the project's
convention is not defective for disagreeing with this file; report the friction rather than
rewriting it.

## Naming and layout

`{ClassName}Test.php` at the same relative path as the class under test:
`app/Actions/DeleteTeam.php` → `tests/Unit/Actions/DeleteTeamTest.php`.

The test name is the specification. State the user-visible result and the condition that produces
it, and give the exact status code for an API error:

```php
it('returns 401 when no token is provided', function () { /* ... */ });
it('does not include deployments from deleted environments', function () { /* ... */ });
```

Not `it('works')`, not `it('handleMethod creates record')` — the first specifies nothing, the
second names a method the file name already identified. Use one declaration style per file.
`describe()` only when one file genuinely covers separate lifecycle actions.

## Test data

Each test creates the records it uses, inside the test. `beforeEach()` holds configuration only —
records created there hide the setup a reader needs and force every test in the file to share one
shape.

- `create()` when the row must exist; `make()` only when the test does not touch the database.
- A named factory state carries meaning: `User::factory()->unverified()->create()` says what the
  state *is*, `create(['email_verified_at' => null])` says only what it contains.
- `for()` / relationship helpers to declare ownership, `recycle()` when several records must share
  one parent, `sequence()` when several need different attributes.
- Create only records that arrange the behaviour or support an assertion.

Use a dataset when setup, body and assertions are identical across input values — enum cases,
roles, boundary values, invalid inputs that fail the same way. Name each case after the difference
so a failure identifies it. If a case needs different setup or different assertions, it is a
different test; a branch inside the test body is two tests in one function.

## Determinism

Time, randomness, sleeping and network access all fail for reasons unrelated to the code under
test. Control all four.

Prefer a framework fake over a mock — a fake keeps the real code path:

1. Framework fakes for facades: `Event`, `Queue`, `Mail`, `Notification`, `Storage`, `Bus`,
   `Http`, `Exceptions`.
2. A developer-defined fake the application already provides.
3. A mock for a container-resolved contract only when the real implementation leaves the process
   or is nondeterministic.
4. The real implementation for everything else, including the database.

Specifics that cause silent wrong results:

- Create each fake **inside** the test that needs it, not in `beforeEach()`.
- Pass class names to `Event::fake()` and `Queue::fake()`. A bare fake swallows every dispatch,
  including ones you did not expect — use it only when the test also asserts `assertNothingPushed()`.
- Create factory records **before** `Event::fake()`. Factories rely on model events (a `creating`
  hook that assigns a UUID, for example), and a nameless fake suppresses them into an invalid model.
- `Http::preventStrayRequests()` plus a fake for the specific endpoint. A bare `Http::fake()`
  quietly accepts any request, so an unintended call passes the test.
- `freezeTime()`, `travelTo()`, `travel()`, `travelBack()` — not `Carbon::setTestNow()`.
  Laravel 13 also resets custom `Str` factories between tests, so a UUID/ULID factory set once for
  the whole suite no longer persists.
- `Sleep::fake()` so retries and backoffs do not really sleep, and assert the sleeps requested.
- `Str::createRandomStringsUsing()` when the test asserts a generated identifier or slug.
- Never mock the query builder. The test then asserts the mock; run real queries against the test
  database.
- `Exceptions::fake()` to assert the application reported the right exception — not
  `withoutExceptionHandling()`, which changes the response under test.

## Assertions

Arrange, act, assert, separated by blank lines, one action per test.

Find the assertion built for the subject before writing a manual check: Laravel response,
database, session, model, queue, event, mail and notification assertions first; Pest expectations
for plain values, types and formats; a hand-built check only when nothing exists. Confirm the name
in the documentation rather than inventing one.

- Named response assertions (`assertOk()`, `assertForbidden()`, `assertNotFound()`) over
  `assertStatus(200)` — the failure then names the broken contract.
- `assertModelExists($model)` over `assertDatabaseHas('users', ['id' => $user->id])`.
- Assert each fact once; a `200` before an `assertSee` adds nothing.
- Write the expected value literally, or derive it a different way. Computing it with the
  implementation's own logic makes the test pass when that logic is wrong.
- A write operation's complete result is the response **plus** the database state **plus** the
  jobs, events, notifications and mail it produced. On the failure path, assert that none of them
  happened. A test that asserts only `assertOk()` passes when nothing was saved.

## Endpoint coverage

For each endpoint, cover the cases that apply: missing or invalid authentication; a request from
another tenant; an insufficient role; a route or scope constraint that is not satisfied; failed
validation; and the valid request, asserting both the response and the persisted state.

Assert the application's real behaviour, not a generic code: an API returns 401 for a missing
token while a browser endpoint redirects to login. For cross-tenant access prefer 404 over 403 —
403 confirms the record exists.

Validation tests send an invalid value through the application and assert the message the user
sees. Asserting that a rules array contains a string tests a declaration, not behaviour.

## Which layer owns which case

An HTTP test proves the endpoint performs authorization; it cannot prove *which* mechanism refused,
because middleware, a policy and a bare `abort(403)` are indistinguishable from outside.

- The full permission matrix belongs in policy or gate tests, where a failure names the rule.
- One HTTP test with one refused role proves the endpoint calls authorization at all.
- The same split applies to validation rule classes and scopes: matrix at the unit layer, one case
  at the endpoint. Never drop the last endpoint case — the unit test still passes if the request
  forgets to apply the rule.

## Suite speed

Measure first: `pest --profile` (or `artisan test --profile`) and start with the ten slowest tests,
because one cause usually explains many of them.

Environment settings, in `.env.testing` or `phpunit.xml`:

- `BCRYPT_ROUNDS=4`. The default 12 makes hashing the dominant cost of every test that signs a
  user in.
- Disable Xdebug (and pcov unless the run needs coverage).
- Disable per-request packages in the test environment: Pulse, Telescope, Nightwatch.
- `WithCachedConfig` and `WithCachedRoutes` traits; `withoutVite()`.
- `LazilyRefreshDatabase` instead of `RefreshDatabase`, so tests that never touch the database do
  not pay for migrations.

Global fakes in `Pest.php` (or the base `TestCase::setUp()`): `Http::preventStrayRequests()`,
`Sleep::fake(syncWithCarbon: true)`, `Exceptions::fake()`.

`pest --parallel` spreads tests across cores and gives each process its own database. A test that
only fails in parallel breaks one of three conditions: it reads a record another test created, it
depends on run order, or it shares a file, cache key or queue name with another test.

## Reviewing a test

A passing test can still be worthless. For each one, name the defect it would catch.

- [ ] It asserts observable behaviour, and survives an implementation change that preserves it.
- [ ] It detects a defect no other test detects.
- [ ] Its name states a result and the condition producing it.
- [ ] Mutable records are created in the test; `beforeEach()` holds configuration only.
- [ ] Time, randomness, sleep and outbound HTTP are controlled.
- [ ] Each fake has an assertion, and is given class names unless the test asserts the whole result.
- [ ] A write test asserts response, database state and side effects.
- [ ] The expected value is known, not computed by the implementation's logic.
- [ ] It passes alone and in the full suite in any order.

Report findings; do not delete or rewrite someone else's test without approval. When a problem is
a suite-wide convention, report the pattern once instead of every file.

<!-- sources: laravel-boost, laravel-docs -->
