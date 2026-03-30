import { useAuth0 } from '@auth0/auth0-react'
import { useEffect } from 'react'
import { setAuthToken } from '../lib/api'

/**
 * Fetches the Auth0 access token silently and injects it into the axios
 * instance as a Bearer token. Re-fetches when the user's auth state changes.
 *
 * Call this once inside AuthGuard (or any top-level authenticated component).
 */
export function useAuthToken() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0()

  useEffect(() => {
    if (!isAuthenticated) {
      setAuthToken(null)
      return
    }

    let cancelled = false

    getAccessTokenSilently()
      .then((token) => {
        if (!cancelled) setAuthToken(token)
      })
      .catch(() => {
        if (!cancelled) setAuthToken(null)
      })

    return () => {
      cancelled = true
    }
  }, [isAuthenticated, getAccessTokenSilently])
}
