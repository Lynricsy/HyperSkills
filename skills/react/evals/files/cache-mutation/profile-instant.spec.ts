// e2e/profile-instant.spec.ts
// Green on the production rig (next build && next start, testing API exposed).
import { test, expect } from '@playwright/test'
import { instant } from '@next/playwright'

test.use({ storageState: 'e2e/.auth/alice.json' })

test('person page shell commits under instant()', async ({ page }) => {
  await page.goto('/people')
  const trigger = page.getByTestId('person-link-alice')
  await expect(trigger).toBeVisible()

  await instant(page, async () => {
    await trigger.click()
    await expect(page.getByTestId('person-shell')).toBeVisible()
  })
})
