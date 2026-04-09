import { useAuth0 } from '@auth0/auth0-react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthToken } from '../../hooks/useAuthToken'

// Token is set at module load time in api.ts — no useEffect needed here
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true'

export function AuthGuard() {
  if (DEV_MODE) return <Outlet />

  const { isAuthenticated, isLoading } = useAuth0()
  useAuthToken()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
