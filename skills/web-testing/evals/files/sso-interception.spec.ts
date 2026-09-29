import { test, expect } from '@playwright/test';

// The app under test lives at baseURL. Sign-in goes through the company IdP:
//   GET /sso/authorize?next=/orders  -> 302 to /sso/callback?code=...
//   GET /sso/callback?code=...        -> sets the HttpOnly `sid` cookie, 302 to `next`
// In CI there is no IdP, so these tests mock it.

test('signs in through mocked SSO', async ({ page }) => {
  await page.route('**/sso/authorize**', route =>
    route.fulfill({ status: 302, headers: { location: '/sso/callback?code=test-code' } }),
  );
  await page.route('**/sso/callback**', route =>
    route.fulfill({ contentType: 'text/html', body: '<h1>Welcome, Test User</h1>' }),
  );

  await page.goto('/sso/authorize?next=/orders');
  // Fails: the page shows the real app's "Invalid SSO code" error instead of the mock.
  await expect(page.getByRole('heading', { name: 'Welcome, Test User' })).toBeVisible();
});

test('viewer cannot see the refund button', async ({ page }) => {
  // storageState in config signs every test in as an admin. Switch to the viewer
  // session for this one test by rewriting the Cookie header on API calls.
  await page.route('**/api/**', route =>
    route.continue({
      headers: { ...route.request().headers(), cookie: `sid=${process.env.VIEWER_SID}` },
    }),
  );

  await page.goto('/orders/1001');
  // Fails: the refund button is still there, as if we were still the admin.
  await expect(page.getByRole('button', { name: 'Refund' })).toHaveCount(0);
});

test('orders API is called with the session cookie', async ({ page }) => {
  let cookieHeader: string | undefined;
  await page.route('**/api/orders**', async route => {
    cookieHeader = route.request().headers()['cookie'];
    await route.continue();
  });

  await page.goto('/orders');
  await expect(page.getByRole('table')).toBeVisible();
  // Passes on Chromium, fails on our WebKit and Firefox projects: cookieHeader is undefined there.
  expect(cookieHeader).toContain('sid=');
});

test('legacy /account URL goes through one redirect hop', async ({ page }) => {
  const hits: string[] = [];
  await page.route('**/*', route => {
    hits.push(new URL(route.request().url()).pathname);
    return route.continue();
  });

  await page.goto('/account'); // server answers 301 -> /settings/profile
  // Fails: hits is ['/account'] only. We expected ['/account', '/settings/profile'].
  expect(hits.filter(p => !p.startsWith('/assets'))).toEqual(['/account', '/settings/profile']);
});
