import { defineConfig, devices } from '@playwright/test';

// Checkout e2e config. CI has been green for weeks. Nobody can reproduce the
// failures engineers report locally, and the CI job takes 41 minutes.
export default defineConfig({
  testDir: './e2e',
  timeout: 180_000,
  retries: 3,
  workers: 1,
  expect: {
    timeout: 60_000,
  },
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    actionTimeout: 90_000,
    navigationTimeout: 120_000,
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    storageState: undefined,
  },
  reporter: [['html', { open: 'never' }]],
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['Pixel 5'] } },
  ],
});
