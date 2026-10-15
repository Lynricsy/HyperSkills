import { test, expect } from '@playwright/test';

// Green for a year on @playwright/test 1.63.0. Since the bump to 1.64.1 the fill below fails:
//   locator.fill: Timeout 30000ms exceeded.
//   - waiting for frameLocator('iframe[title="Secure payment"]').getByLabel('Card number')
//   - element is not visible
// The payment iframe sits inside the "Pay by card" accordion panel, which the app renders collapsed
// (`visibility: hidden; height: 0`) until the shopper clicks the "Pay by card" header.
// A teammate's proposed fix is `fill('4242 4242 4242 4242', { force: true })`.

test('pays by card', async ({ page }) => {
  await page.goto('/checkout');
  const payment = page.frameLocator('iframe[title="Secure payment"]');
  await payment.getByLabel('Card number').fill('4242 4242 4242 4242');
  await payment.getByLabel('Expiry').fill('12/30');
  await payment.getByLabel('CVC').fill('123');
  await page.getByRole('button', { name: 'Place order' }).click();
  await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
});
