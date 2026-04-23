import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClientProvider, useQuery } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'

import { auth0Config } from './lib/auth'
import { queryClient } from './lib/query-client'
import { api } from './lib/api'
import { AuthGuard } from './components/common/AuthGuard'
import { AppShell } from './components/layout/AppShell'

// Pages
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { RecordsPage } from './pages/records/RecordsPage'
import { DocumentDetailPage } from './pages/records/DocumentDetailPage'
import { PassportManagePage } from './pages/passport/PassportManagePage'
import { AddFamilyMemberPage } from './pages/passport/AddFamilyMemberPage'
import { PublicPassportPage } from './pages/passport/PublicPassportPage'
import { LoginPage } from './pages/auth/LoginPage'
import { CallbackPage } from './pages/auth/CallbackPage'
import { AccountSettingsPage } from './pages/settings/AccountSettingsPage'
import { FamilyCirclePage } from './pages/family/FamilyCirclePage'
import { InviteAcceptancePage } from './pages/family/InviteAcceptancePage'
import { OnboardingPage } from './pages/onboarding/OnboardingPage'
import { ProviderDashboardPage } from './pages/provider/ProviderDashboardPage'
import { ProviderPatientPage } from './pages/provider/ProviderPatientPage'

// ── Provider role guard ────────────────────────────────────────────────────

function RequireProvider({ children }: { children: React.ReactNode }) {
  const { data, isLoading } = useQuery<{ onboarding_completed: boolean; role: string }>({
    queryKey: ['onboarding-status'],
    queryFn: async () => {
      const { data } = await api.get('/auth/onboarding/status')
      return data
    },
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!data || data.role !== 'PROVIDER') {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

// ── Onboarding guard ───────────────────────────────────────────────────────

function RequireOnboarding({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth0()

  const { data, isLoading } = useQuery<{ onboarding_completed: boolean; role: string }>({
    queryKey: ['onboarding-status'],
    queryFn: async () => {
      const { data } = await api.get('/auth/onboarding/status')
      return data
    },
    enabled: isAuthenticated && !authLoading,
    staleTime: 60_000,
  })

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    )
  }

  if (data && !data.onboarding_completed) {
    return <Navigate to="/onboarding" replace />
  }

  return <>{children}</>
}

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
            <Route path="/invite/:token" element={<InviteAcceptancePage />} />

            {/* Onboarding — authenticated but outside AppShell */}
            <Route element={<AuthGuard />}>
              <Route path="/onboarding" element={<OnboardingPage />} />
            </Route>

            {/* Protected routes — gated behind onboarding completion */}
            <Route element={<AuthGuard />}>
              <Route
                element={
                  <RequireOnboarding>
                    <AppShell />
                  </RequireOnboarding>
                }
              >
                <Route path="/" element={<PassportManagePage />} />
                <Route path="/health" element={<DashboardPage />} />
                <Route path="/records" element={<RecordsPage />} />
                <Route path="/records/:documentId" element={<DocumentDetailPage />} />
                <Route path="/insights" element={<Navigate to="/health" replace />} />
                <Route path="/passport/add-member" element={<AddFamilyMemberPage />} />
                <Route path="/settings" element={<AccountSettingsPage />} />
                <Route path="/family" element={<FamilyCirclePage />} />
              </Route>
            </Route>

            {/* Provider routes — PROVIDER role only, no AppShell wrapping */}
            <Route element={<AuthGuard />}>
              <Route
                path="/provider"
                element={
                  <RequireOnboarding>
                    <RequireProvider>
                      <ProviderDashboardPage />
                    </RequireProvider>
                  </RequireOnboarding>
                }
              />
              <Route
                path="/provider/patient/:requestId"
                element={
                  <RequireOnboarding>
                    <RequireProvider>
                      <ProviderPatientPage />
                    </RequireProvider>
                  </RequireOnboarding>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </Auth0Provider>
  )
}
