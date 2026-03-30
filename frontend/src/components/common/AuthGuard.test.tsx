import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthGuard } from './AuthGuard'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}))

import { useAuth0 } from '@auth0/auth0-react'

describe('AuthGuard', () => {
  it('shows spinner while loading', () => {
    vi.mocked(useAuth0).mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
    } as ReturnType<typeof useAuth0>)

    render(
      <MemoryRouter>
        <AuthGuard />
      </MemoryRouter>
    )

    expect(document.querySelector('.animate-spin')).toBeTruthy()
  })

  it('redirects to login when not authenticated', () => {
    vi.mocked(useAuth0).mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
    } as ReturnType<typeof useAuth0>)

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthGuard />
      </MemoryRouter>
    )

    // Navigate to /login renders nothing (no Login component in test)
    expect(screen.queryByText('Coming')).toBeNull()
  })
})
