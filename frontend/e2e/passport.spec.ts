/**
 * UF-008 — Generate and Share Health Passport (Account Owner side)
 *
 * Smoke tests for the /passport (Family Circle / PassportPage) route.
 * All API calls are mocked via page.route().
 *
 * Auth note: tests expect the dev server to be running with VITE_DEV_MODE=true.
 * If not, the page redirects to /login and assertions are conditionally skipped.
 */

import { test, expect } from '@playwright/test'

const MOCK_MEMBERS = [
  {
    member_id: 'member-001',
    full_name: 'Alice Smith',
    relationship: 'SELF',
    blood_group: 'O+',
    date_of_birth: '1988-07-14',
  },
  {
    member_id: 'member-002',
    full_name: 'Bob Smith',
    relationship: 'SPOUSE',
    blood_group: 'A-',
    date_of_birth: '1986-11-02',
  },
]

test.describe('UF-008 — Passport / Family Circle page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock family members endpoint
    await page.route('**/api/v1/family/members', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_MEMBERS),
      })
    })

    // Mock auth provision
    await page.route('**/api/v1/auth/provision', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ member_id: 'member-001' }),
      })
    })
  })

  test('passport page renders "Family Circle" heading', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByRole('heading', { name: /family circle/i })).toBeVisible()
  })

  test('primary member card is visible with member name', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // PrimaryCard renders the self member's name
    await expect(page.getByText('Alice Smith')).toBeVisible()
  })

  test('"Manage Passport" link is visible on primary member card', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // PrimaryCard renders a Link to /passport/manage with text "Manage Passport"
    await expect(page.getByRole('link', { name: /manage passport/i })).toBeVisible()
  })

  test('"Add Member" button is present', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // Header "Add Member" link + section link
    await expect(page.getByRole('link', { name: /add member/i }).first()).toBeVisible()
  })

  test('family member (non-self) is shown in the grid', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByText('Bob Smith')).toBeVisible()
  })

  test('"View Full Record" button is present on primary card', async ({ page }) => {
    await page.goto('/passport')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByRole('button', { name: /view full record/i })).toBeVisible()
  })
})
