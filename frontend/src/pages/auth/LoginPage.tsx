import { useAuth0 } from '@auth0/auth0-react'
import { Navigate } from 'react-router-dom'


function ShieldHeartIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      className="w-16 h-16"
      fill="none"
      aria-hidden="true"
    >
      {/* Shield */}
      <path
        d="M32 4L8 14v18c0 13.3 10.3 25.7 24 29 13.7-3.3 24-15.7 24-29V14L32 4z"
        fill="#2563EB"
        opacity="0.15"
      />
      <path
        d="M32 4L8 14v18c0 13.3 10.3 25.7 24 29 13.7-3.3 24-15.7 24-29V14L32 4z"
        stroke="#2563EB"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      {/* Heart */}
      <path
        d="M32 43s-11-7.5-11-15a7 7 0 0 1 11-5.7A7 7 0 0 1 43 28c0 7.5-11 15-11 15z"
        fill="#2563EB"
      />
    </svg>
  )
}

function LockIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      className="w-3.5 h-3.5 inline-block flex-shrink-0"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M11.5 6H11V4.5a3 3 0 0 0-6 0V6h-.5A1.5 1.5 0 0 0 3 7.5v5A1.5 1.5 0 0 0 4.5 14h7a1.5 1.5 0 0 0 1.5-1.5v-5A1.5 1.5 0 0 0 11.5 6zM6 4.5a2 2 0 1 1 4 0V6H6V4.5zm2 6.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z" />
    </svg>
  )
}

export function LoginPage() {
  const { loginWithRedirect, isAuthenticated, isLoading, error: auth0Error } = useAuth0()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/" replace />

  if (auth0Error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white px-4">
        <div className="w-full max-w-sm rounded-2xl bg-white shadow-sm border border-gray-100 p-8 text-center space-y-4">
          <p className="text-sm font-semibold text-red-600">Auth0 Error</p>
          <p className="text-sm text-gray-500">{auth0Error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-blue-700 transition-colors"
          >
            Reload
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo area */}
        <div className="flex flex-col items-center mb-8 space-y-3">
          <ShieldHeartIcon />
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">MediVault</h1>
          <p className="text-sm text-gray-500 text-center">
            Your health records, always with you
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-white shadow-sm border border-gray-100 p-8 space-y-4">
          <button
            onClick={() => loginWithRedirect().catch(console.error)}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Sign in
          </button>

          <button
            onClick={() =>
              loginWithRedirect({ authorizationParams: { screen_hint: 'signup' } }).catch(console.error)
            }
            className="w-full py-3 px-4 border border-gray-300 text-gray-700 rounded-xl font-medium min-h-[44px] hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
          >
            Create account
          </button>
        </div>

        {/* Trust signals */}
        <div className="mt-6 flex items-center justify-center gap-1 text-xs text-gray-400">
          <LockIcon />
          <span>HIPAA-aware · End-to-end encrypted · Your data stays yours</span>
        </div>
      </div>
    </div>
  )
}
