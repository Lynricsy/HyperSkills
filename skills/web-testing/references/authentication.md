# Authentication state

Verified against: Playwright 1.63.0.

## Contents

- [The cost being removed](#the-cost-being-removed)
- [What `storageState` actually contains](#what-storagestate-actually-contains)
- [The setup project](#the-setup-project)
- [Why not `globalSetup`](#why-not-globalsetup)
- [One session per role](#one-session-per-role)
- [Per-worker sessions when tests mutate the user](#per-worker-sessions-when-tests-mutate-the-user)
- [sessionStorage and anything else the state file omits](#sessionstorage-and-anything-else-the-state-file-omits)
- [Second factors](#second-factors)
- [Skipping the UI entirely](#skipping-the-ui-entirely)
- [Expiry and regeneration](#expiry-and-regeneration)
- [Secret hygiene](#secret-hygiene)
- [Review checklist](#review-checklist)

## The cost being removed

A `beforeEach` that drives the login form runs the slowest, least interesting part of the
application once per test. On a 180-test suite that is 180 form submissions, 180 round trips and
180 chances for the login page to be the thing that failed. It also makes every test's failure
ambiguous: a blank dashboard could be the feature under test or the login that did not settle.

The replacement is to perform the login once per run, capture the browser's authenticated state to
disk, and have every test start from it.

## What `storageState` actually contains

Verified by capturing a page that sets `localStorage.session = 'abc123'`:

```json
{
  "cookies": [],
  "origins": [
    { "origin": "http://127.0.0.1:8777",
      "localStorage": [ { "name": "session", "value": "abc123" } ] }
  ]
}
```

Two top-level keys, and nothing else: `cookies` (each with name, value, domain, path, expires,
httpOnly, secure, sameSite) and `origins` (per-origin localStorage). `HttpOnly` cookies are
included — the file is written by the browser context, not by page script, so an `HttpOnly`
session cookie round-trips correctly.

Verified on a page that writes only `sessionStorage`:

```
STATE_KEYS ["cookies","origins"]
ORIGIN_KEYS []
HAS_SESSION_STORAGE false
```

Note the second line: because that origin had no localStorage, it produced no `origins` entry at
all. So "the state file looks empty" is a normal outcome for an app that keeps session data in
`sessionStorage`, and it will not be obvious from reading the file that anything is missing.

## The setup project

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  fullyParallel: true,
  use: { baseURL: process.env.BASE_URL ?? 'http://localhost:3000' },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/viewer.json' },
      dependencies: ['setup'],
    },
  ],
});
```

```ts
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const file = 'playwright/.auth/viewer.json';

setup('authenticate as viewer', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.VIEWER_EMAIL!);
  await page.getByLabel('Password').fill(process.env.VIEWER_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  // Assert the post-login state before saving, or a failed login is saved as "success".
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await page.context().storageState({ path: file });
});
```

Verified run:

```
[1/2] [setup] › tests/auth.setup.ts:5:6 › authenticate
[2/2] [chromium] › tests/dash.spec.ts:3:5 › dashboard is reached without replaying the login UI
  2 passed (920ms)
```

Three dependency semantics worth knowing: projects with no dependencies run first; a dependent
project starts only after its dependency **completes successfully**; and if the dependency fails,
every dependent project is *skipped* rather than failed — which is why the report suddenly shows
zero tests rather than 180 failures when the login breaks. While iterating on one spec, `--no-deps`
skips setup and reuses whatever state file is already on disk.

The assertion before `storageState()` is the part most often omitted. Without it, a login that
silently failed still writes a file, and the next 180 tests fail with unrelated messages.

## Why not `globalSetup`

`globalSetup` runs before the test runner creates any browser, so there is no `page` and no
`BrowserContext` fixture. Driving a login there means launching a browser by hand, outside the
runner's tracing, timeouts, retries and reporting — and every failure in it surfaces as a runner
crash rather than a failed test.

The division of labour:

| Mechanism | For |
|---|---|
| `globalSetup` | one-time non-browser work: seed a database, mint an API token, start a stub service |
| setup **project** with `dependencies` | shared browser authentication and any state that needs a real page |
| `test.extend()` fixture | per-test or per-worker state, with guaranteed teardown |
| `globalTeardown` | cleanup after the whole run |

## One session per role

Sharing a single administrator account across a suite makes most of the suite unable to test what
it claims. A test authenticated as an administrator cannot prove that a viewer is denied anything,
and a viewer-scoped dashboard assertion passes trivially when the session has every permission.

```ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  { name: 'viewer', testMatch: /viewer\/.*\.spec\.ts/,
    use: { storageState: 'playwright/.auth/viewer.json' }, dependencies: ['setup'] },
  { name: 'editor', testMatch: /editor\/.*\.spec\.ts/,
    use: { storageState: 'playwright/.auth/editor.json' }, dependencies: ['setup'] },
  { name: 'admin',  testMatch: /admin\/.*\.spec\.ts/, workers: 1,
    use: { storageState: 'playwright/.auth/admin.json' }, dependencies: ['setup'] },
]
```

One setup file per role, or one file that loops the roles. The `admin` project above carries
`workers: 1` because its tests change organisation-wide settings that every other test can observe
— that is a scoped serialization, not a suite-wide one. `{ lock: 'org-settings' }` (Playwright
1.63+) is the narrower alternative when only a few tests contend.

For a test that genuinely needs a signed-in state no shared file can provide — a brand-new user, a
user mid-onboarding — use a fixture that logs in per test and accept the cost for those few tests:

```ts
export const test = base.extend<{ freshUser: Page }>({
  freshUser: async ({ browser, request }, use) => {
    const creds = await createUserViaApi(request);
    const context = await browser.newContext();
    const page = await context.newPage();
    await signIn(page, creds);
    await use(page);
    await context.close();
  },
});
```

## Per-worker sessions when tests mutate the user

A single state file shared by every worker is fine while all tests only read. As soon as a test
changes something on the account — a preference, a draft, a cart — parallel workers are editing one
user and failing each other. Key the state file on the worker:

```ts
export const test = base.extend<{}, { workerStorageState: string }>({
  storageState: ({ workerStorageState }, use) => use(workerStorageState),
  workerStorageState: [async ({ browser }, use, workerInfo) => {
    const file = `playwright/.auth/user-${workerInfo.workerIndex}.json`;
    if (!fs.existsSync(file)) {
      const account = await claimAccount(workerInfo.workerIndex);   // or create via API
      const context = await browser.newContext({ storageState: undefined });
      await signIn(await context.newPage(), account);
      await context.storageState({ path: file });
      await context.close();
    }
    await use(file);
  }, { scope: 'worker' }],
});
```

`workerInfo.workerIndex` is stable for the life of a worker, so the account pool can be as small as
the worker count. `testInfo.parallelIndex` is the equivalent when the fixture is test-scoped.

## sessionStorage and anything else the state file omits

Because `sessionStorage` is not serialised, any application that keeps state there will behave as
though nothing was restored. The concrete symptom: a suite whose `storageState` restores the login
cookie correctly, but every page under a section still bounces to a picker because the selected
tenant, warehouse or workspace lived in `sessionStorage`.

Seed it explicitly. `addInitScript` runs before any page script on every navigation in the context,
which is the only reliable moment:

```ts
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      sessionStorage.setItem('shop.warehouse', JSON.stringify({ id: 'wh-1' }));
    });
    await use(page);
  },
});
```

The same technique covers IndexedDB and any in-memory store the app hydrates on boot. Do not
attempt it with `page.evaluate` after `goto` — by then the app has already read the empty value and
redirected.

## Second factors

Disabling 2FA on the test account is the tempting fix and the wrong one: the suite then never
exercises the code path every real user goes through, and it breaks in one step the day the policy
becomes mandatory.

Generate the code instead. The setup project has exactly one place that needs it:

```ts
import { TOTP } from 'otpauth';   // any standard TOTP implementation

const secret = (await request.get('/api/test/totp-secret')).json();
const code = new TOTP({ secret: secret.value }).generate();
await page.getByLabel('Authentication code').fill(code);
```

Two constraints: the seeded secret must come from a test-only endpoint or fixture that does not
exist in production, and the generated code is time-bound, so generate it immediately before
filling rather than at the top of the setup file.

Where the second factor is genuinely un-automatable (hardware key, SMS to a real number), the
honest answer is that the login step cannot be covered end to end. Test it manually, mint the
session through the API for everything else, and say so rather than weakening the production
configuration to suit the suite.

## Skipping the UI entirely

For everything except the login test itself, the fastest correct path is often not the form at all:
call the session endpoint through Playwright's `request` fixture and write the resulting cookies
into the context.

```ts
setup('authenticate via api', async ({ request, context }) => {
  const res = await request.post('/api/session', {
    data: { email: process.env.VIEWER_EMAIL, password: process.env.VIEWER_PASSWORD },
  });
  expect(res.ok()).toBeTruthy();
  await context.storageState({ path: 'playwright/.auth/viewer.json' });
});
```

`request` shares the context's cookie jar, so a `Set-Cookie` from the API lands in the state file.
This is appropriate precisely because there is one other test — the login spec — whose job is to
prove the form works. Keep that test, and let nothing else depend on it.

## Expiry and regeneration

A saved state is only valid as long as its cookies are. A 12-hour session cookie means the state
file is per-run, not per-day, and a stale file produces a suite-wide failure that looks like an
application bug.

- Regenerate in the setup project on every run; do not cache the file between CI jobs.
- Add `playwright/.auth/` to `.gitignore`. The file is a live credential.
- Never commit it, never upload it as a CI artifact, and delete it in teardown for local runs on a
  shared machine.
- If the setup project is skipped with `--no-deps` during debugging, remember the file on disk may
  be expired — that is the first thing to check when "only my local run" fails.

## Secret hygiene

Credentials belong in the environment, sourced from a secret store. Three specific failure modes to
flag in review:

- A password or API key as a literal in a spec file, a config or a CI workflow. It is in version
  control and in every clone.
- A state file uploaded with the test report so the whole team's CI artifacts contain a live
  session.
- A trace recorded through a form that received a real credential. Traces capture DOM snapshots and
  network bodies; a trace of a login is a recording of that login. Use dedicated test accounts
  whose compromise is uninteresting, and prefer the API path for setup so the credential never
  enters the page.

## Review checklist

- [ ] Login happens once per run in a setup project, not in `beforeEach`.
- [ ] The setup asserts a post-login state before calling `storageState()`.
- [ ] Each role has its own state file and project; nothing runs as admin by accident.
- [ ] Tests that mutate the account use per-worker state or a per-test fresh user.
- [ ] Anything the app keeps in `sessionStorage` is seeded with `addInitScript`.
- [ ] A mandatory second factor is generated, not disabled.
- [ ] `playwright/.auth/` is gitignored, regenerated per run, never an artifact.
- [ ] No credential literal in any spec, config or workflow file.

<!-- sources: playwright-docs, ms-playwright-cli, currents-best-practices, testdino-playwright, lambdatest-playwright, playwright-runtime -->
