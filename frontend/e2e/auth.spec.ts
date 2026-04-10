/**
 * UF-002 — Log In (Returning User)
 *
 * Tests for the login page and unauthenticated redirect behaviour.
 * These are public-page tests — no auth bypass needed.
 */

import { test, expect } from '@playwright/test'

test.describe('UF-002 — Login page', () => {
  test('renders login page with heading and sign-in button', async ({ page }) => {
    await page.goto('/login')

    // The page title/brand
    await expect(page.getByText('MediVault')).toBeVisible()

    // Sign in button rendered by LoginPage
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('login page has a "Create account" button', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible()
  })

  test('unauthenticated visit to "/" redirects to /login', async ({ page }) => {
    // VITE_DEV_MODE is NOT set in the test environment (no .env injected),
    // so Auth0Provider will treat the user as unauthenticated and AuthGuard
    // will redirect to /login.
    // We mock the Auth0 token endpoint so no real network call is made.
    await page.route('**/oauth/token', async (route) => {
      await route.fulfill({ status: 401, body: JSON.stringify({ error: 'unauthorized' }) })
    })

    await page.goto('/')

    // Should end up on the login page
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByText('MediVault')).toBeVisible()
  })
})
