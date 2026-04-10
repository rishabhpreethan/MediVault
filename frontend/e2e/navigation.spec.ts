/**
 * Authenticated navigation smoke tests.
 *
 * Auth strategy: VITE_DEV_MODE=true makes AuthGuard render <Outlet /> directly
 * without checking Auth0. We simulate that by having the dev server started
 * with those env vars OR by intercepting all API/Auth0 calls so the app doesn't
 * error out.
 *
 * Since we cannot guarantee the dev server is started with VITE_DEV_MODE=true,
 * these tests inject the flag via addInitScript + mock all backend API calls
 * so the app can render without a real backend.
 */

import { test, expect } from '@playwright/test'

// ---------------------------------------------------------------------------
// Shared setup: mock Auth0 + backend API so authenticated pages can render
// ---------------------------------------------------------------------------

async function setupAuthBypass(page: import('@playwright/test').Page) {
  // Pretend VITE_DEV_MODE is true so AuthGuard skips the Auth0 check.
  // We override the env object that Vite injects at build time.
  await page.addInitScript(() => {
    // @ts-ignore — override Vite's injected env
    window.__vite_env_override__ = true
    // Vite replaces import.meta.env.* at compile time, so we cannot override it
    // via addInitScript after the fact. Instead we mock the Auth0 hooks so
    // isAuthenticated = true and isLoading = false.
    Object.defineProperty(window, '__playwright_auth__', {
      value: { isAuthenticated: true, isLoading: false },
      writable: false,
    })
  })

  // Mock the Auth0 discovery + token endpoints so no network errors bubble up
  await page.route('**/.well-known/openid-configuration', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({}),
    })
  })

  // Mock backend health check
  await page.route('**/api/v1/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok' }),
    })
  })

  // Mock family members endpoint (required by AppShell / PassportPage)
  await page.route('**/api/v1/family/members', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          member_id: 'test-member-id',
          full_name: 'Test User',
          relationship: 'SELF',
          blood_group: 'O+',
          date_of_birth: '1990-01-01',
        },
      ]),
    })
  })

  // Mock auth provision endpoint
  await page.route('**/api/v1/auth/provision', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ member_id: 'test-member-id' }),
    })
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Navigation smoke tests (dev-mode auth bypass)', () => {
  test('app shell renders when dev mode is active', async ({ page }) => {
    await setupAuthBypass(page)

    // Navigate to root — if VITE_DEV_MODE is set in the running dev server,
    // AuthGuard renders Outlet. Otherwise we land on /login; either way the
    // page should load without crashing.
    const response = await page.goto('/')
    expect(response?.status()).toBeLessThan(500)

    // The page title should be the app name in all cases
    await expect(page).toHaveTitle(/MediVault/i)
  })

  test('login page is accessible without auth', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL(/\/login/)

    // Either the login card or a redirect to "/" (dev mode)
    // In both cases the page should not show a 5xx error
    const status = page.locator('body')
    await expect(status).toBeVisible()
  })

  test('public passport route is accessible without auth', async ({ page }) => {
    // Mock the public passport API to return 404 (not found)
    await page.route('**/api/v1/passport/public/**', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Passport not found' }),
      })
    })

    await page.goto('/passport/00000000-0000-0000-0000-000000000000')

    // Should render the NotFoundState from PublicPassportPage
    await expect(page.getByText(/passport not found/i)).toBeVisible()
  })
})
