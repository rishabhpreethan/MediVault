import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Profile', icon: '👤' },
  { to: '/timeline', label: 'Timeline', icon: '📅' },
  { to: '/charts', label: 'Charts', icon: '📈' },
  { to: '/documents', label: 'Documents', icon: '📄' },
]

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-10">
      <div className="max-w-2xl mx-auto flex">
        {navItems.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-3 min-h-[56px] text-xs font-medium transition-colors ${
                isActive ? 'text-blue-600' : 'text-gray-500'
              }`
            }
          >
            <span className="text-xl leading-none mb-1">{icon}</span>
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
