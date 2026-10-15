import { test, expect } from '@playwright/test';

// playwright.config.ts sets use: { testIdAttribute: 'data-testid' } and a pinned viewport.

test('orders page matches the visual baseline', async ({ page }) => {
  await page.goto('/orders?seed=fixture');
  await expect(page).toHaveScreenshot('orders.png', { animations: 'disabled' });
});

test('refunded order shows its status', async ({ page }) => {
  await page.goto('/orders?seed=fixture&sort=newest');
  await expect(page.getByTestId('order-row-2')).toContainText('refunded');
});

test('orders table renders', async ({ page }) => {
  await page.goto('/orders?seed=fixture');
  await expect(page.locator('[data-qa="orders-table"]')).toBeVisible();
});
