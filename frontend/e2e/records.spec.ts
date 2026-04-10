/**
 * UF-003 / UF-010 — Document Library (Records Page)
 *
 * Smoke tests for the Clinical Archive (Records) page.
 * These tests mock all backend API calls so no running backend is required.
 *
 * Auth note: tests rely on the dev server being started with VITE_DEV_MODE=true
 * (which makes AuthGuard skip the Auth0 check). If not set, the app will
 * redirect to /login and the assertions will be skipped via the conditional.
 */

import { test, expect } from '@playwright/test'

test.describe('UF-003 / UF-010 — Records page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock family members
    await page.route('**/api/v1/family/members', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            member_id: 'member-001',
            full_name: 'Test User',
            relationship: 'SELF',
            blood_group: 'B+',
            date_of_birth: '1985-06-15',
          },
        ]),
      })
    })

    // Mock documents endpoint — return an empty archive
    await page.route('**/api/v1/documents/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
        }),
      })
    })

    // Also match without trailing slash
    await page.route('**/api/v1/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
        }),
      })
    })

    await page.route('**/api/v1/auth/provision', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ member_id: 'member-001' }),
      })
    })
  })

  test('records page renders "Clinical Archive" heading', async ({ page }) => {
    await page.goto('/records')

    // In dev mode: page renders. In prod mode with Auth0: we are redirected to login.
    const url = page.url()
    if (url.includes('/login')) {
      // Not running with dev mode — skip content assertions
      test.skip()
      return
    }

    // Heading rendered by RecordsPage when activeTab === 'archive'
    await expect(page.getByRole('heading', { name: /clinical archive/i })).toBeVisible()
  })

  test('records page shows an upload / import button', async ({ page }) => {
    await page.goto('/records')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // RecordsPage renders a button with aria-label "Import a new medical record"
    await expect(
      page.getByRole('button', { name: /import.*record/i })
    ).toBeVisible()
  })

  test('records page shows tab switcher (Archive / Timeline)', async ({ page }) => {
    await page.goto('/records')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // Tab list rendered by RecordsPage
    await expect(page.getByRole('tablist', { name: /records view/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /archive/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /timeline/i })).toBeVisible()
  })

  test('empty state is shown when no documents exist', async ({ page }) => {
    await page.goto('/records')

    const url = page.url()
    if (url.includes('/login')) {
      test.skip()
      return
    }

    // Empty state message
    await expect(page.getByText(/no records yet/i)).toBeVisible()
  })
})
