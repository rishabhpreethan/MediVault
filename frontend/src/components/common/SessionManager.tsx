import { useState } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { useSessionActivity } from '../../hooks/useSessionActivity'
import { useTokenRefresh } from '../../hooks/useTokenRefresh'

/**
 * SessionManager — composes session-inactivity tracking and token refresh.
 * When a 30-day inactivity timeout is detected, shows a non-dismissible modal
 * requiring the user to sign in again.
 *
 * Must be rendered inside Auth0Provider (i.e. inside AppShell / protected routes).
 */
export function SessionManager(): JSX.Element {
  const [isExpired, setIsExpired] = useState(false)
  const { logout } = useAuth0()

  useSessionActivity(() => setIsExpired(true))
  useTokenRefresh()

  if (!isExpired) {
    return <></>
  }

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-on-surface/50"
      aria-modal="true"
      role="dialog"
      aria-labelledby="session-expired-title"
      aria-describedby="session-expired-body"
    >
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-sm w-full mx-4 font-['Manrope',sans-serif]">
        {/* Lock icon */}
        <div className="flex justify-center mb-5">
          <div className="w-14 h-14 rounded-full bg-teal-50 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-7 h-7 text-primary"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M12 1.5a5.25 5.25 0 0 0-5.25 5.25v3a3 3 0 0 0-3 3v6.75a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3v-6.75a3 3 0 0 0-3-3v-3c0-2.9-2.35-5.25-5.25-5.25Zm3.75 8.25v-3a3.75 3.75 0 1 0-7.5 0v3h7.5Z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>

        <h2
          id="session-expired-title"
          className="text-center text-xl font-bold text-on-surface mb-3"
        >
          Session Expired
        </h2>
        <p
          id="session-expired-body"
          className="text-center text-sm text-on-surface-variant mb-7 leading-relaxed"
        >
          You've been inactive for 30 days. Please sign in again to continue.
        </p>

        <button
          type="button"
          onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
          className="w-full min-h-[44px] bg-primary hover:bg-teal-700 active:bg-teal-800 transition-colors text-white font-semibold rounded-xl text-sm"
        >
          Sign In
        </button>
      </div>
    </div>
  )
}
