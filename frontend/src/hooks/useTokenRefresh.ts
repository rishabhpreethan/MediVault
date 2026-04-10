import { useEffect } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { setAuthToken } from '../lib/api'

const REFRESH_INTERVAL_MS = 10 * 60 * 1000 // 10 minutes

/**
 * Proactively refreshes the Auth0 access token every 10 minutes.
 * On success, updates the axios Authorization header via setAuthToken.
 * On failure (session expired), forces logout.
 */
export function useTokenRefresh(): void {
  const { isAuthenticated, getAccessTokenSilently, logout } = useAuth0()

  useEffect(() => {
    if (!isAuthenticated) return

    const intervalId = setInterval(async () => {
      try {
        const token = await getAccessTokenSilently({ cacheMode: 'off' })
        setAuthToken(token)
      } catch {
        logout({ logoutParams: { returnTo: window.location.origin } })
      }
    }, REFRESH_INTERVAL_MS)

    return () => {
      clearInterval(intervalId)
    }
  }, [isAuthenticated, getAccessTokenSilently, logout])
}
