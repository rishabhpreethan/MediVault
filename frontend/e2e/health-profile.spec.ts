/**
 * UF-004 — View Health Profile (Dashboard)
 *
 * Tests that the dashboard renders correctly when the API returns an empty
 * health profile (no labs, no medications, no vitals).
 * All API calls are mocked via page.route().
 *
 * Auth note: tests expect the dev server to be running with VITE_DEV_MODE=true.
 * If not, the page redirects to /login and assertions are conditionally skipped.
 */

import { test, expect } from '@playwright/test'

// A minimal but valid HealthProfile shape (matches backend response schema)
const EMPTY_PROFILE = {
  member: {
    member_id: 'member-001',
    full_name: 'Jane Doe',
    relationship: 'SELF',
    blood_group: 'A+',
    date_of_birth: '1990-03-20',
  },
  medications: [],
  conditions: [],
  allergies: [],
  recent_vitals: [],
  recent_labs: [],
  doctors: [],
}

test.describe('UF-004 — Health Profile (Dashboard)', () => {
  test.beforeEach(async ({ page }) => {
    // Mock family members
    await page.route('**/api/v1/family/members', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([EMPTY_PROFILE.member]),
      })
    })

    // Mock health profile endpoint
    await page.route('**/api/v1/profile/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(EMPTY_PROFILE),
      })
    })

    // Also catch profile with query string (?member_id=...)
    await page.route('**/api/v1/profile*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(EMPTY_PROFILE),
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

  test('dashboard renders "Health Profile" heading', async ({ page }) => {
    await page.goto('/')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByRole('heading', { name: /health profile/i })).toBeVisible()
  })

  test('dashboard renders member name from profile', async ({ page }) => {
    await page.goto('/')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // Member name is shown in the header sub-line
    await expect(page.getByText('Jane Doe')).toBeVisible()
  })

  test('dashboard renders blood type card', async ({ page }) => {
    await page.goto('/')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // VitalsStrip renders a "Blood Type" label
    await expect(page.getByText(/blood type/i)).toBeVisible()
  })

  test('empty labs renders "No lab results yet" empty state', async ({ page }) => {
    await page.goto('/')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByText(/no lab results yet/i)).toBeVisible()
  })

  test('dashboard does not crash with empty profile', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/')

    // Allow time for async data to settle
    await page.waitForTimeout(500)

    // No unhandled JS errors
    expect(errors.filter((e) => !e.includes('Auth0'))).toHaveLength(0)
  })

  test('"Share Vault" and "New Entry" action buttons are visible', async ({ page }) => {
    await page.goto('/')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    await expect(page.getByRole('button', { name: /share vault/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /new entry/i })).toBeVisible()
  })
})
