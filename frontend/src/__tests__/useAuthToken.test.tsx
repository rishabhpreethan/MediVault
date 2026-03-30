import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuthToken } from '../hooks/useAuthToken'
import { setAuthToken } from '../lib/api'

// Mock Auth0
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}))

// Mock setAuthToken so we can assert on it
vi.mock('../lib/api', () => ({
  setAuthToken: vi.fn(),
  api: { defaults: { headers: { common: {} } } },
}))

import { useAuth0 } from '@auth0/auth0-react'

const mockUseAuth0 = useAuth0 as ReturnType<typeof vi.fn>
const mockSetAuthToken = setAuthToken as ReturnType<typeof vi.fn>

describe('useAuthToken', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls setAuthToken with null when not authenticated', async () => {
    mockUseAuth0.mockReturnValue({
      isAuthenticated: false,
      getAccessTokenSilently: vi.fn(),
    })

    renderHook(() => useAuthToken())

    expect(mockSetAuthToken).toHaveBeenCalledWith(null)
  })

  it('fetches token and calls setAuthToken when authenticated', async () => {
    const getAccessTokenSilently = vi.fn().mockResolvedValue('test-access-token')
    mockUseAuth0.mockReturnValue({
      isAuthenticated: true,
      getAccessTokenSilently,
    })

    renderHook(() => useAuthToken())

    await act(async () => {
      await Promise.resolve()
    })

    expect(getAccessTokenSilently).toHaveBeenCalled()
    expect(mockSetAuthToken).toHaveBeenCalledWith('test-access-token')
  })

  it('calls setAuthToken(null) when token fetch fails', async () => {
    const getAccessTokenSilently = vi.fn().mockRejectedValue(new Error('token error'))
    mockUseAuth0.mockReturnValue({
      isAuthenticated: true,
      getAccessTokenSilently,
    })

    renderHook(() => useAuthToken())

    await act(async () => {
      await Promise.resolve()
    })

    expect(mockSetAuthToken).toHaveBeenCalledWith(null)
  })
})
