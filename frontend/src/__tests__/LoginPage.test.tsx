import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LoginPage } from '../pages/auth/LoginPage'

// Mock @auth0/auth0-react
const mockLoginWithRedirect = vi.fn()

const mockUseAuth0 = vi.fn()

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => mockUseAuth0(),
}))

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign in button', () => {
    mockUseAuth0.mockReturnValue({
      loginWithRedirect: mockLoginWithRedirect,
      isAuthenticated: false,
      isLoading: false,
    })

    renderLoginPage()

    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders create account button', () => {
    mockUseAuth0.mockReturnValue({
      loginWithRedirect: mockLoginWithRedirect,
      isAuthenticated: false,
      isLoading: false,
    })

    renderLoginPage()

    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows spinner when isLoading', () => {
    mockUseAuth0.mockReturnValue({
      loginWithRedirect: mockLoginWithRedirect,
      isAuthenticated: false,
      isLoading: true,
    })

    const { container } = renderLoginPage()

    // Spinner is a div with animate-spin class
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()

    // Buttons should not be visible during loading
    expect(screen.queryByRole('button', { name: /sign in/i })).not.toBeInTheDocument()
  })

  it('redirects to / when already authenticated', () => {
    mockUseAuth0.mockReturnValue({
      loginWithRedirect: mockLoginWithRedirect,
      isAuthenticated: true,
      isLoading: false,
    })

    renderLoginPage()

    // When authenticated, Navigate replaces content — buttons should not be present
    expect(screen.queryByRole('button', { name: /sign in/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /create account/i })).not.toBeInTheDocument()
  })
})
