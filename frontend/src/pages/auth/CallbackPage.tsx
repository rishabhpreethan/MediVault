import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { api, setAuthToken } from '../../lib/api'

export function CallbackPage() {
  const { getAccessTokenSilently, loginWithRedirect, isAuthenticated, isLoading } = useAuth0()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Wait until Auth0Provider has finished processing the callback
    if (isLoading) return
    if (!isAuthenticated) return

    let cancelled = false

    async function provision() {
      try {
        const token = await getAccessTokenSilently()
        setAuthToken(token)
        await api.post('/auth/provision')
        if (!cancelled) {
          const returnTo = sessionStorage.getItem('post_auth_return') ?? '/'
          sessionStorage.removeItem('post_auth_return')
          navigate(returnTo, { replace: true })
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : 'Something went wrong. Please try again.'
          setError(message)
        }
      }
    }

    provision()

    return () => {
      cancelled = true
    }
  }, [isLoading, isAuthenticated, getAccessTokenSilently, navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center justify-center px-4">
        <div className="w-full max-w-sm rounded-2xl bg-white shadow-sm border border-gray-100 p-8 space-y-6 text-center">
          <div className="flex flex-col items-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-6 h-6 text-red-500"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm.75-11.25a.75.75 0 0 0-1.5 0v4.5a.75.75 0 0 0 1.5 0v-4.5zm-.75 7a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Sign-in failed</h2>
            <p className="text-sm text-gray-500">{error}</p>
          </div>

          <button
            onClick={() => loginWithRedirect()}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center justify-center px-4">
      <div className="flex flex-col items-center space-y-4">
        <div
          className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"
          role="status"
          aria-label="Loading"
        />
        <p className="text-sm text-gray-500 font-medium">Signing you in…</p>
      </div>
    </div>
  )
}
