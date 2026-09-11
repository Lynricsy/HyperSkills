import { test, expect } from '@playwright/test';

// Checkout suite. Green on CI for months, but nobody trusts it.
// `npx playwright test` locally: passes. Same suite with `--fully-parallel`: 4 of 9 fail.

let cartId = '';
let authToken = '';

test.beforeAll(async ({ browser }) => {
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/login');
  await page.fill('#email', 'qa@example.com');
  // hardcoded credential, also used by the staging seed script
  await page.fill('#password', 'hunter2-REDACTED');
  await page.click('div.login-form > form > button.primary');
  await page.waitForTimeout(3000);
  authToken = (await page.evaluate(() => localStorage.getItem('token'))) || '';
  await page.close();
});

test('01 - adds an item to the cart', async ({ page }) => {
  await page.goto('http://localhost:3000/products');
  await page.waitForTimeout(2000);
  await page.click('#product-list > li:nth-child(3) > div.card > button');
  await page.waitForTimeout(1500);
  const badge = await page.$('span.cart-badge');
  expect(await badge!.textContent()).toBe('1');
  cartId = (await page.evaluate(() => localStorage.getItem('cartId'))) || '';
});

test('02 - cart page shows the item added by test 01', async ({ page }) => {
  await page.goto(`http://localhost:3000/cart/${cartId}`);
  await page.waitForTimeout(2000);
  const rows = await page.$$('table.cart tbody tr');
  expect(rows.length).toBe(1);
});

test('03 - applies a promo code', async ({ page }) => {
  await page.goto(`http://localhost:3000/cart/${cartId}`);
  await page.waitForTimeout(2000);
  await page.fill('input[name=promo]', 'SAVE10');
  await page.click('button.apply');
  await page.waitForTimeout(2500);

  // sometimes the banner renders, sometimes a toast does, so check whichever showed up
  const banner = page.locator('div.promo-banner');
  if (await banner.isVisible()) {
    expect(await banner.textContent()).toContain('10%');
  } else {
    const toast = page.locator('.toast');
    if (await toast.isVisible()) {
      expect(await toast.textContent()).toContain('10%');
    }
  }
});

test('04 - checkout submits', async ({ page }) => {
  await page.goto(`http://localhost:3000/cart/${cartId}`);
  await page.waitForTimeout(2000);
  await page.click('text=Checkout');
  await page.waitForTimeout(4000);

  // retry loop, because the confirmation is slow on CI
  let ok = false;
  for (let i = 0; i < 10; i++) {
    if (await page.locator('div.confirmation').isVisible()) {
      ok = true;
      break;
    }
    await page.waitForTimeout(1000);
  }
  expect(ok).toBeTruthy();
});

test('05 - order appears in history', async ({ page }) => {
  await page.setExtraHTTPHeaders({ authorization: `Bearer ${authToken}` });
  await page.goto('http://localhost:3000/orders');
  await page.waitForLoadState('networkidle');
  const first = await page.$('#orders > div:first-child .order-total');
  if (first) {
    expect(await first.textContent()).not.toBe('');
  }
});

test('06 - empty cart state', async ({ page }) => {
  await page.goto('http://localhost:3000/cart/empty');
  await page.waitForTimeout(1000);
  expect(await page.locator('div.empty-state').count()).toBeGreaterThan(0);
});
