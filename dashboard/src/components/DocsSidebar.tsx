import { NavLink } from 'react-router-dom'
import Icon, { type IconName } from './Icon'

interface DocsSidebarProps {
  onNavigate?: () => void
}

interface NavItem {
  to: string
  label: string
  icon: IconName
}

interface NavSection {
  title: string
  items: NavItem[]
}

const sections: NavSection[] = [
  {
    title: 'Getting Started',
    items: [
      { to: '/docs', label: 'Introduction', icon: 'info' },
      { to: '/docs/getting-started', label: 'Quick Start', icon: 'terminal' },
      { to: '/docs/configuration', label: 'Configuration', icon: 'settings' },
    ],
  },
  {
    title: 'Core Features',
    items: [
      { to: '/docs/policy-engine', label: 'Policy Engine', icon: 'shield' },
      { to: '/docs/proxy', label: 'Security Proxy', icon: 'gateway' },
      { to: '/docs/pentest', label: 'Pentest Engine', icon: 'pentest' },
      { to: '/docs/llm', label: 'LLM Integration', icon: 'sparkles' },
    ],
  },
  {
    title: 'Reference',
    items: [
      { to: '/docs/api', label: 'API Reference', icon: 'code' },
    ],
  },
]

export default function DocsSidebar({ onNavigate }: DocsSidebarProps) {
  return (
    <nav className="sticky top-20 w-60 shrink-0 hidden lg:block py-10 pr-4 overflow-y-auto max-h-[calc(100vh-5rem)]">
      {sections.map((section, sectionIdx) => (
        <div key={section.title}>
          <h4
            className={`text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 ${
              sectionIdx === 0 ? 'mt-0' : 'mt-6'
            }`}
          >
            {section.title}
          </h4>
          <ul className="space-y-1">
            {section.items.map(({ to, label, icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/docs'}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-indigo-500/10 text-indigo-300 font-medium'
                        : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
                    }`
                  }
                >
                  <Icon name={icon} size={16} />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
}
