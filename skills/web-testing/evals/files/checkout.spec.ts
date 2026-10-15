import { test, expect } from '@playwright/test';
import cart from './fixtures/cart.json';

// Storefront: Next.js App Router, server-rendered. All data goes through POST /graphql
// (operations: GetCart, ApplyCoupon, GetShippingRates).

test.beforeEach(async ({ page }) => {
  await page.route('**/graphql', (route) => route.fulfill({ json: { data: { cart } } }));
});

test('applies coupon', async ({ page }) => {
  await page.goto('/checkout');
  await page.getByLabel('Coupon code').fill('SPRING10');
  await page.getByRole('button', { name: 'Apply coupon' }).click();
  await expect(page.getByTestId('cart-spinner')).toBeHidden();
  const total = await page.getByTestId('order-total').textContent();
  expect(total).toBe('$90.00');
});

test('discount rounds half-cents', async ({ page }) => {
  await page.goto('/checkout?items=3x33.335');
  await page.getByLabel('Coupon code').fill('THIRD');
  await page.getByRole('button', { name: 'Apply coupon' }).click();
  await expect(page.getByTestId('discount')).toHaveText('-$33.34');
});
