import { useAuth0 } from '@auth0/auth0-react'
import { Navigate } from 'react-router-dom'

export function LoginPage() {
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/" replace />

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">MediVault</h1>
          <p className="mt-2 text-sm text-gray-500">Your personal health record</p>
        </div>
        <button
          onClick={() => loginWithRedirect()}
          className="w-full py-3 px-4 bg-blue-600 text-white rounded-xl font-medium min-h-[44px] hover:bg-blue-700 transition-colors"
        >
          Sign in
        </button>
        <button
          onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: 'signup' } })}
          className="w-full py-3 px-4 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium min-h-[44px] hover:bg-gray-50 transition-colors"
        >
          Create account
        </button>
      </div>
    </div>
  )
}
