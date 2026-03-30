import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { auth0Config } from './lib/auth'
import { queryClient } from './lib/query-client'
import { AuthGuard } from './components/common/AuthGuard'
import { AppShell } from './components/layout/AppShell'

// Pages — implemented per feature task
import { ProfilePage } from './pages/profile/ProfilePage'
import { TimelinePage } from './pages/timeline/TimelinePage'
import { ChartsPage } from './pages/charts/ChartsPage'
import { DocumentsPage } from './pages/documents/DocumentsPage'
import { PassportPage } from './pages/passport/PassportPage'
import { PublicPassportPage } from './pages/passport/PublicPassportPage'
import { LoginPage } from './pages/auth/LoginPage'

export default function App() {
  return (
    <Auth0Provider {...auth0Config}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/passport/:uuid" element={<PublicPassportPage />} />

            {/* Protected routes */}
            <Route element={<AuthGuard />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<ProfilePage />} />
                <Route path="/timeline" element={<TimelinePage />} />
                <Route path="/charts" element={<ChartsPage />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/passport" element={<PassportPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </Auth0Provider>
  )
}
