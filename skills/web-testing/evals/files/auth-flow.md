# Signed-in test setup — current state

## The application

`shop-admin` is a React SPA served at `http://localhost:3000`, backed by a REST API at
`http://localhost:4000`.

Sign-in flow:

1. `GET /login` renders an email + password form.
2. Successful `POST /api/session` sets an `HttpOnly` `sid` cookie (domain `localhost`,
   `SameSite=Lax`, 12 hour expiry) **and** the SPA writes `{"orgId":"...","role":"..."}` into
   `localStorage` under the key `shop.ctx`.
3. Accounts with 2FA enabled land on `/login/totp`, where a six digit code is required. The
   staging seed exposes the shared TOTP secret through `GET /api/test/totp-secret`.
4. The SPA also keeps the currently selected warehouse in `sessionStorage` under
   `shop.warehouse`. Pages under `/inventory` redirect back to `/warehouse-picker` when it is
   absent.

## The roles the suite needs

| Role | What its tests do |
|---|---|
| `viewer` | read-only dashboards, never mutates data |
| `editor` | edits product records — each test edits its own product |
| `admin` | changes org-wide settings (tax rules, warehouses) — visible to every other test |

`viewer` and `editor` tests are the bulk of the suite (~180 tests). There are 6 `admin` tests.

## What the suite does today

Every spec file starts with:

```ts
test.beforeEach(async ({ page }) => {
  await page.goto('/login');
  await page.fill('#email', process.env.TEST_EMAIL!);
  await page.fill('#password', process.env.TEST_PASSWORD!);
  await page.click('button[type=submit]');
  await page.waitForTimeout(2500);
  await page.goto('/dashboard');
});
```

All three roles share one account (`qa+admin@example.com`, 2FA disabled specifically so the
tests can skip step 3).

## The problems

- Login accounts for roughly 6 of the 11 minutes of local suite time.
- Roughly one run in eight fails inside `beforeEach` with a blank dashboard.
- `/inventory` specs each re-pick a warehouse before they can start.
- Product management asked for 2FA to be mandatory on every account next quarter, which will
  break the whole suite at once.
- A previous attempt to run with more workers made `admin` tests and `editor` tests fail each
  other: tax rules changed underneath in-flight edits.
