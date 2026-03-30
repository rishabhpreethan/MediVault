import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'
import { MemberSelector } from './MemberSelector'

export function AppShell() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <span className="font-semibold text-gray-900">MediVault</span>
          <MemberSelector />
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 pb-24">
        <Outlet />
      </main>

      <BottomNav />
    </div>
  )
}
