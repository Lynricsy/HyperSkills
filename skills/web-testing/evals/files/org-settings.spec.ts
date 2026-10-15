import { test, expect } from '@playwright/test';
import { setOrgFlag, getOrgFlag } from './helpers/org';

// Every test in this file reads or writes the organisation-wide feature flags, so each one carries
// the same lock by hand. Two more tests are about to be added here.

test('beta dashboard is off by default', { lock: 'org-flags' }, async ({ page }) => {
  // Fails roughly once a week on CI and never locally. billing.spec.ts has a test that turns
  // `beta-dashboard` on and never turns it off; whether that test has already run when this one
  // starts depends on the order the files happen to be scheduled in.
  expect(await getOrgFlag('beta-dashboard')).toBe(false);
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});

test('enabling beta dashboard shows the new layout', { lock: 'org-flags' }, async ({ page }) => {
  await setOrgFlag('beta-dashboard', true);
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard (beta)' })).toBeVisible();
  await setOrgFlag('beta-dashboard', false);
});

test('audit log flag hides the export button', { lock: 'org-flags' }, async ({ page }) => {
  await setOrgFlag('audit-log', false);
  await page.goto('/settings/audit');
  await expect(page.getByRole('button', { name: 'Export' })).toBeHidden();
});

test('audit log flag shows the export button', { lock: 'org-flags' }, async ({ page }) => {
  await setOrgFlag('audit-log', true);
  await page.goto('/settings/audit');
  await expect(page.getByRole('button', { name: 'Export' })).toBeVisible();
});
