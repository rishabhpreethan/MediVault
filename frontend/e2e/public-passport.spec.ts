/**
 * UF-008 — Public Health Passport (Clinician side)
 *
 * Tests for the /passport/:uuid public page. No auth required.
 * All backend API calls are mocked via page.route().
 */

import { test, expect } from '@playwright/test'

const VALID_UUID = '123e4567-e89b-12d3-a456-426614174000'
const UNKNOWN_UUID = '00000000-0000-0000-0000-000000000000'
const REVOKED_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

const MOCK_PASSPORT = {
  passport_id: VALID_UUID,
  member_name: 'Priya Sharma',
  blood_group: 'B+',
  allergies: ['Penicillin', 'Dust mites'],
  medications: [
    { drug_name: 'Metformin', dosage: '500 mg', frequency: 'twice daily' },
    { drug_name: 'Atorvastatin', dosage: '10 mg', frequency: 'once at night' },
  ],
  diagnoses: ['Type 2 Diabetes Mellitus', 'Dyslipidaemia'],
  generated_at: '2026-04-01T10:00:00Z',
  expires_at: null,
  disclaimer:
    'This passport contains patient-reported information. It has not been verified by a licensed clinician.',
}

test.describe('UF-008 — Public Passport page (clinician view)', () => {
  test('renders passport data for a valid UUID', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    // Hero card: member name and "Health Passport" label
    await expect(page.getByText('Priya Sharma')).toBeVisible()
    await expect(page.getByText(/health passport/i)).toBeVisible()
  })

  test('shows blood group badge on valid passport', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    await expect(page.getByText('B+')).toBeVisible()
  })

  test('shows allergies section for a valid passport', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    await expect(page.getByText('Penicillin')).toBeVisible()
    await expect(page.getByText('Dust mites')).toBeVisible()
  })

  test('shows medications section for a valid passport', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    await expect(page.getByText('Metformin')).toBeVisible()
    await expect(page.getByText('Atorvastatin')).toBeVisible()
  })

  test('shows diagnoses section for a valid passport', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    await expect(page.getByText('Type 2 Diabetes Mellitus')).toBeVisible()
  })

  test('shows "MediVault" header on public passport page', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    // MinimalHeader renders "MediVault" and "Verified by MediVault"
    await expect(page.getByText('MediVault').first()).toBeVisible()
  })

  test('shows "Passport not found" for an unknown UUID (404)', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${UNKNOWN_UUID}`, async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Passport not found' }),
      })
    })

    await page.goto(`/passport/${UNKNOWN_UUID}`)

    // NotFoundState renders "Passport not found"
    await expect(page.getByText(/passport not found/i)).toBeVisible()
  })

  test('shows "Passport expired or revoked" for a revoked UUID (410)', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${REVOKED_UUID}`, async (route) => {
      await route.fulfill({
        status: 410,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Passport revoked' }),
      })
    })

    await page.goto(`/passport/${REVOKED_UUID}`)

    // RevokedState renders "Passport expired or revoked"
    await expect(page.getByText(/passport expired or revoked/i)).toBeVisible()
  })

  test('shows disclaimer text on valid passport', async ({ page }) => {
    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)

    // DisclaimerBar renders the disclaimer text from the API response
    await expect(page.getByText(/patient-reported/i)).toBeVisible()
  })

  test('passport page does not crash with valid data', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.route(`**/api/v1/passport/public/${VALID_UUID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_PASSPORT),
      })
    })

    await page.goto(`/passport/${VALID_UUID}`)
    await page.waitForTimeout(300)

    // No unhandled JS errors
    expect(errors.filter((e) => !e.includes('Auth0'))).toHaveLength(0)
  })
})
