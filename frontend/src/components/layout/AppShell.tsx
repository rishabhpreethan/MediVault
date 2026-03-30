import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'
import { MemberSelector } from '../common/MemberSelector'

/**
 * AppShell — the persistent chrome that wraps all authenticated routes.
 *
 * Layout (mobile-first, max-w-lg centered):
 *   ┌─────────────────────────┐
 *   │  sticky header          │  ← MediVault wordmark + MemberSelector
 *   ├─────────────────────────┤
 *   │  scrollable main area   │  ← <Outlet /> (child route content)
 *   ├─────────────────────────┤
 *   │  fixed bottom nav       │  ← 5 tabs
 *   └─────────────────────────┘
 *
 * pb-20 on <main> ensures content is never hidden behind the fixed bottom nav.
 */
export function AppShell() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ── Sticky header ── */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-lg mx-auto flex items-center justify-between">
          <span className="font-semibold text-gray-900 text-base">MediVault</span>
          <MemberSelector />
        </div>
      </header>

      {/* ── Scrollable content area ── */}
      {/*
        pb-20 clears the 56 px fixed BottomNav + a comfortable margin.
        On devices with a home indicator the BottomNav adds its own safe-area
        spacer, so pb-20 is sufficient here for all viewports.
      */}
      <main className="flex-1 max-w-lg mx-auto w-full px-4 py-6 pb-20 overflow-y-auto">
        <Outlet />
      </main>

      {/* ── Fixed bottom navigation ── */}
      <BottomNav />
    </div>
  )
}
