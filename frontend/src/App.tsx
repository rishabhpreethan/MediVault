import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { auth0Config } from './lib/auth'
import { queryClient } from './lib/query-client'
import { AuthGuard } from './components/common/AuthGuard'
import { AppShell } from './components/layout/AppShell'

// Pages
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { RecordsPage } from './pages/records/RecordsPage'
import { InsightsPage } from './pages/insights/InsightsPage'
import { PassportPage } from './pages/passport/PassportPage'
import { PublicPassportPage } from './pages/passport/PublicPassportPage'
import { LoginPage } from './pages/auth/LoginPage'
import { CallbackPage } from './pages/auth/CallbackPage'

export default function App() {
  return (
    <Auth0Provider {...auth0Config}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/callback" element={<CallbackPage />} />
            <Route path="/passport/:uuid" element={<PublicPassportPage />} />

            {/* Protected routes */}
            <Route element={<AuthGuard />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/records" element={<RecordsPage />} />
                <Route path="/insights" element={<InsightsPage />} />
                <Route path="/passport" element={<PassportPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </Auth0Provider>
  )
}
