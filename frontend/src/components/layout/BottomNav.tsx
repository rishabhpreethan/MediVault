import { NavLink } from 'react-router-dom'

// SVG icon components — inline to avoid an icon-library dependency
function IconUser() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-6 h-6"
      aria-hidden="true"
    >
      <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z" />
    </svg>
  )
}

function IconTimeline() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-6 h-6"
      aria-hidden="true"
    >
      <path d="M13 2.05v2.02c3.95.49 7 3.85 7 7.93 0 3.21-1.81 6-4.72 7.72L13 17v5h5l-1.22-1.22C19.91 19.07 22 15.76 22 12c0-5.18-3.95-9.45-9-9.95zM11 2.05C5.95 2.55 2 6.82 2 12c0 3.76 2.09 7.07 5.22 8.78L6 22h5v-5l-2.28 2.28C7.81 18 6 15.21 6 12c0-4.08 3.05-7.44 7-7.93V2.05z" />
    </svg>
  )
}

function IconCharts() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-6 h-6"
      aria-hidden="true"
    >
      <path d="M3.5 18.5l6-6 4 4 7-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <rect x="2" y="2" width="20" height="20" rx="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function IconDocuments() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-6 h-6"
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" />
    </svg>
  )
}

function IconPassport() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-6 h-6"
      aria-hidden="true"
    >
      <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-9 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm6 12H5v-1c0-2 4-3.1 6-3.1s6 1.1 6 3.1v1zm3-1h-1v-1c0-1.3-.8-2.4-2-3.2.4-.1.7-.1 1-.1 1.7 0 3 1.3 3 3v1.3h-1z" />
    </svg>
  )
}

interface NavItem {
  to: string
  label: string
  Icon: () => JSX.Element
  end?: boolean
}

const navItems: NavItem[] = [
  { to: '/', label: 'Profile', Icon: IconUser, end: true },
  { to: '/timeline', label: 'Timeline', Icon: IconTimeline },
  { to: '/charts', label: 'Charts', Icon: IconCharts },
  { to: '/documents', label: 'Documents', Icon: IconDocuments },
  { to: '/passport', label: 'Passport', Icon: IconPassport },
]

export function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-10 safe-area-inset-bottom"
      aria-label="Main navigation"
    >
      <div className="max-w-lg mx-auto flex">
        {navItems.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 min-h-[56px] text-xs font-medium transition-colors ${
                isActive
                  ? 'text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`
            }
            aria-label={label}
          >
            {({ isActive }) => (
              <>
                <span
                  className={`mb-0.5 transition-transform ${isActive ? 'scale-110' : ''}`}
                >
                  <Icon />
                </span>
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
      {/* Safe area spacer for devices with home indicator */}
      <div className="h-safe-bottom" />
    </nav>
  )
}
