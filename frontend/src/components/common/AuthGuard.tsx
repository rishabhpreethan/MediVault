import { useAuth0 } from '@auth0/auth0-react'
import { Navigate, Outlet } from 'react-router-dom'

export function AuthGuard() {
  const { isAuthenticated, isLoading } = useAuth0()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
