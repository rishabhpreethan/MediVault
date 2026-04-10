import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useActiveMemberDetails, useSetActiveMember } from '../../hooks/useFamily'
import { SessionManager } from '../common/SessionManager'

// ── Inline SVG icons ───────────────────────────────────────────────────────

function IconDashboard() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M3 3h8v8H3V3zm0 10h8v8H3v-8zm10-10h8v8h-8V3zm0 10h8v8h-8v-8z" />
    </svg>
  )
}

function IconRecords() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
    </svg>
  )
}

function IconInsights() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <rect x="2" y="2" width="20" height="20" rx="2" />
      <path d="M7 16l3-4 3 3 3-5" />
    </svg>
  )
}

function IconPassport() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-9 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm6 12H5v-1c0-2 4-3.1 6-3.1s6 1.1 6 3.1v1zm3-1h-1v-1c0-1.3-.8-2.4-2-3.2.4-.1.7-.1 1-.1 1.7 0 3 1.3 3 3v1.3h-1z" />
    </svg>
  )
}

function IconSettings() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}

function IconBell() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5"
      aria-hidden="true"
    >
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  )
}

// ── Nav items ──────────────────────────────────────────────────────────────

interface NavItem {
  to: string
  label: string
  Icon: () => JSX.Element
  end?: boolean
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', Icon: IconDashboard, end: true },
  { to: '/records', label: 'Records', Icon: IconRecords },
  { to: '/insights', label: 'Insights', Icon: IconInsights },
  { to: '/passport', label: 'Passport', Icon: IconPassport },
  { to: '/settings', label: 'Settings', Icon: IconSettings },
]

// ── TopNav (desktop, hidden on mobile) ────────────────────────────────────

function TopNav() {
  return (
    <header
      className="hidden md:flex fixed top-0 w-full z-50 h-16 items-center justify-between px-6 bg-white/70 backdrop-blur-md border-b border-teal-500/10 shadow-sm shadow-teal-900/5"
      aria-label="Top navigation"
    >
      {/* Logo */}
      <span className="text-primary font-bold text-lg tracking-tight select-none">
        MediVault
      </span>

      {/* Nav links */}
      <nav className="flex items-center gap-8" aria-label="Primary navigation">
        {navItems.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              isActive
                ? 'text-teal-600 font-semibold border-b-2 border-teal-500 pb-0.5 text-sm transition-colors'
                : 'text-slate-500 hover:text-teal-600 text-sm transition-colors pb-0.5'
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Right: notification bell + avatar */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="text-slate-500 hover:text-teal-600 transition-colors p-1.5 rounded-full hover:bg-teal-50 min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label="Notifications"
        >
          <IconBell />
        </button>
        <div
          className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-semibold select-none"
          aria-label="User avatar"
        >
          U
        </div>
      </div>
    </header>
  )
}

// ── BottomNav (mobile only) ────────────────────────────────────────────────

export function BottomNav() {
  const location = useLocation()

  return (
    <nav
      className="fixed bottom-0 left-0 w-full bg-white/90 backdrop-blur-md border-t border-slate-100 px-4 py-3 flex justify-around items-center z-50 md:hidden"
      aria-label="Bottom navigation"
    >
      {navItems.map(({ to, label, Icon, end }) => {
        const isActive = end
          ? location.pathname === to
          : location.pathname.startsWith(to)
        return (
          <NavLink
            key={to}
            to={to}
            end={end}
            className="flex flex-col items-center gap-0.5 min-w-[44px] min-h-[44px] justify-center"
            aria-label={label}
          >
            <span className={isActive ? 'text-teal-600' : 'text-slate-400'}>
              <Icon />
            </span>
            <span
              className={`text-[10px] font-bold ${
                isActive ? 'text-teal-600' : 'text-slate-400'
              }`}
            >
              {label}
            </span>
          </NavLink>
        )
      })}
    </nav>
  )
}

// ── AppShell ───────────────────────────────────────────────────────────────

/**
 * AppShell — responsive chrome wrapping all authenticated routes.
 *
 * Desktop (md+): fixed top nav bar, full-width content below.
 * Mobile: fixed bottom 4-tab nav bar, content above.
 *
 *   Desktop:
 *   ┌─────────────────────────────────────────┐
 *   │  TopNav (fixed, h-16)                   │
 *   ├─────────────────────────────────────────┤
 *   │  <Outlet /> (scrollable, pt-16)         │
 *   └─────────────────────────────────────────┘
 *
 *   Mobile:
 *   ┌─────────────────────┐
 *   │  <Outlet /> (pb-20) │
 *   ├─────────────────────┤
 *   │  BottomNav (fixed)  │
 *   └─────────────────────┘
 */
// ── Vault context banner ───────────────────────────────────────────────────

function VaultBanner() {
  const { member, isSelf } = useActiveMemberDetails()
  const setActiveMember = useSetActiveMember()

  if (isSelf || !member) return null

  return (
    <div className="fixed top-0 md:top-16 left-0 w-full z-40 bg-teal-600 text-white text-sm py-2 px-4 flex items-center justify-between gap-3">
      <span className="font-medium truncate">
        Viewing <strong>{member.full_name}</strong>'s vault
      </span>
      <button
        type="button"
        onClick={() => setActiveMember(null)}
        className="shrink-0 inline-flex items-center gap-1.5 bg-white/20 hover:bg-white/30 transition-colors rounded-full px-3 py-1 text-xs font-semibold"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5" aria-hidden="true">
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Switch back to my vault
      </button>
    </div>
  )
}

export function AppShell() {
  const { isSelf } = useActiveMemberDetails()
  // When viewing a family member, add extra top padding to clear the banner
  const bannerOffset = !isSelf ? 'pt-16 md:pt-28' : 'pt-6 md:pt-20'

  return (
    <div className="min-h-screen bg-surface font-['Manrope',sans-serif]">
      {/* Desktop top nav */}
      <TopNav />

      {/* Family vault banner (shown when viewing another member's vault) */}
      <VaultBanner />

      {/* Scrollable content */}
      <main className={`${bannerOffset} pb-24 md:pb-8 px-4 md:px-8 max-w-7xl mx-auto w-full`}>
        <Outlet />
      </main>

      {/* Mobile bottom nav */}
      <BottomNav />

      {/* Session inactivity + token refresh manager */}
      <SessionManager />
    </div>
  )
}
