import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Icon, { type IconName } from '../components/Icon'
import { isAuthEnabled } from '../auth/ClerkProviderWrapper'

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

interface NavItem {
  label: string
  icon: IconName
  description?: string
  to: string
  external?: boolean
  badge?: string
}

interface NavSection {
  heading?: string
  items: NavItem[]
}

interface DropdownDef {
  label: string
  sections: NavSection[]
  /** Optional highlight card rendered in a right column. */
  highlight?: { title: string; description: string; to: string }
  width?: string
}

/* ------------------------------------------------------------------ */
/*  Data                                                              */
/* ------------------------------------------------------------------ */

const platformDropdown: DropdownDef = {
  label: 'Platform',
  width: 'w-[540px]',
  sections: [
    {
      heading: 'Products',
      items: [
        {
          label: 'Config Scanner',
          icon: 'scan',
          description: 'Deep security analysis of MCP configs',
          to: '/docs/configuration',
        },
        {
          label: 'Policy Engine',
          icon: 'shield',
          description: 'Fine-grained agent access control',
          to: '/docs/policy-engine',
        },
        {
          label: 'Anomaly Detection',
          icon: 'activity',
          description: 'Behavioral monitoring with adaptive baselines',
          to: '/#features',
        },
        {
          label: 'Security Proxy',
          icon: 'gateway',
          description: 'Real-time MCP traffic interception',
          to: '/docs/proxy',
        },
        {
          label: 'Pentest Engine',
          icon: 'pentest',
          description: 'Automated SAFE-MCP attack simulations',
          to: '/docs/pentest',
        },
        {
          label: 'LLM Analysis',
          icon: 'sparkles',
          description: 'AI-powered threat analysis',
          to: '/docs/llm',
          badge: 'PAID',
        },
      ],
    },
  ],
  highlight: {
    title: "What's new in v0.1.0",
    description:
      'Config scanner, policy engine, anomaly detection and more — explore the first release.',
    to: '/changelog',
  },
}

const solutionsDropdown: DropdownDef = {
  label: 'Solutions',
  width: 'w-[280px]',
  sections: [
    {
      items: [
        {
          label: 'MCP Security Monitoring',
          icon: 'shield',
          to: '/solutions/mcp-security',
        },
        {
          label: 'AI Agent Compliance',
          icon: 'lock',
          to: '/solutions/ai-compliance',
        },
        {
          label: 'Pentest Automation',
          icon: 'pentest',
          to: '/solutions/pentest-automation',
        },
      ],
    },
  ],
}

const resourcesDropdown: DropdownDef = {
  label: 'Resources',
  width: 'w-[280px]',
  sections: [
    {
      items: [
        { label: 'Blog', icon: 'document', to: '/blog' },
        { label: 'Changelog', icon: 'tag', to: '/changelog' },
        {
          label: 'GitHub',
          icon: 'github',
          to: 'https://github.com/ivanlkf/navil',
          external: true,
        },
        { label: 'About', icon: 'users', to: '/about' },
      ],
    },
  ],
}

const dropdowns: DropdownDef[] = [
  platformDropdown,
  solutionsDropdown,
  resourcesDropdown,
]

/* ------------------------------------------------------------------ */
/*  Sub-components                                                    */
/* ------------------------------------------------------------------ */

function NavLink({ item }: { item: NavItem }) {
  const inner = (
    <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors group">
      <div className="mt-0.5 flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
        <Icon name={item.icon} size={16} className="text-indigo-400" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-200 group-hover:text-white flex items-center gap-2">
          {item.label}
          {item.badge && (
            <span className="text-[10px] font-semibold uppercase tracking-wider text-violet-400 bg-violet-400/10 px-1.5 py-0.5 rounded">
              {item.badge}
            </span>
          )}
          {item.external && (
            <Icon name="external-link" size={12} className="text-gray-500" />
          )}
        </p>
        {item.description && (
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
            {item.description}
          </p>
        )}
      </div>
    </div>
  )

  if (item.external) {
    return (
      <a href={item.to} target="_blank" rel="noopener noreferrer">
        {inner}
      </a>
    )
  }
  return <Link to={item.to}>{inner}</Link>
}

/* ------------------------------------------------------------------ */
/*  MegaNav                                                           */
/* ------------------------------------------------------------------ */

export default function MegaNav() {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const navRef = useRef<HTMLElement>(null)

  /* Close on outside click */
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setActiveDropdown(null)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  /* Close on Escape */
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setActiveDropdown(null)
        setMobileOpen(false)
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [])

  const toggleDropdown = useCallback(
    (label: string) => {
      setActiveDropdown((prev) => (prev === label ? null : label))
    },
    [],
  )

  return (
    <>
      <nav
        ref={navRef}
        className="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800/60"
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* ---- Logo ---- */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="relative">
              <div className="absolute inset-0 bg-indigo-500/20 rounded-lg blur-sm" />
              <Icon name="shield" size={24} className="text-indigo-400 relative" />
            </div>
            <span className="text-lg font-bold text-white">
              Navil{' '}
              <span className="text-xs font-normal text-indigo-400 bg-indigo-400/10 px-1.5 py-0.5 rounded">
                Cloud
              </span>
            </span>
          </Link>

          {/* ---- Desktop nav ---- */}
          <div className="hidden lg:flex items-center gap-1">
            {dropdowns.map((dd) => (
              <div key={dd.label} className="relative">
                <button
                  onClick={() => toggleDropdown(dd.label)}
                  className={`flex items-center gap-1 px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeDropdown === dd.label
                      ? 'text-white bg-white/5'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {dd.label}
                  <Icon
                    name="chevron-down"
                    size={14}
                    className={`transition-transform ${
                      activeDropdown === dd.label ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {activeDropdown === dd.label && (
                  <div
                    className={`absolute top-full left-1/2 -translate-x-1/2 mt-3 mega-panel p-6 animate-slideDown ${dd.width ?? 'w-[280px]'}`}
                  >
                    {/* Platform dropdown: 2-column layout */}
                    {dd.highlight ? (
                      <div className="grid grid-cols-[1fr_200px] gap-6">
                        <div>
                          {dd.sections.map((section, si) => (
                            <div key={si}>
                              {section.heading && (
                                <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-3 px-2">
                                  {section.heading}
                                </p>
                              )}
                              <div className="space-y-0.5">
                                {section.items.map((item) => (
                                  <NavLink key={item.label} item={item} />
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Highlight card */}
                        <Link
                          to={dd.highlight.to}
                          className="glass-card p-4 rounded-xl flex flex-col justify-between hover:bg-white/5 transition-colors group"
                        >
                          <div>
                            <p className="text-sm font-medium text-white group-hover:text-indigo-300 transition-colors">
                              {dd.highlight.title}
                            </p>
                            <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                              {dd.highlight.description}
                            </p>
                          </div>
                          <div className="flex items-center gap-1 text-xs text-indigo-400 mt-4">
                            Learn more
                            <Icon name="arrow-right" size={12} />
                          </div>
                        </Link>
                      </div>
                    ) : (
                      /* Standard single-column dropdown */
                      <div>
                        {dd.sections.map((section, si) => (
                          <div key={si}>
                            {section.heading && (
                              <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-3 px-2">
                                {section.heading}
                              </p>
                            )}
                            <div className="space-y-0.5">
                              {section.items.map((item) => (
                                <NavLink key={item.label} item={item} />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Direct links */}
            <Link
              to="/docs"
              className="px-3 py-2 text-sm text-gray-400 hover:text-gray-200 rounded-lg transition-colors"
            >
              Docs
            </Link>
            <Link
              to="/pricing"
              className="px-3 py-2 text-sm text-gray-400 hover:text-gray-200 rounded-lg transition-colors"
            >
              Pricing
            </Link>
          </div>

          {/* ---- Right side: CTA + mobile toggle ---- */}
          <div className="flex items-center gap-3">
            {/* Desktop CTA */}
            <div className="hidden lg:flex items-center gap-3">
              <Link
                to={isAuthEnabled() ? '/sign-in' : '/dashboard'}
                className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to={isAuthEnabled() ? '/sign-up' : '/dashboard'}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 transition-colors"
              >
                Get Started
              </Link>
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 text-gray-400 hover:text-white transition-colors"
              aria-label="Open menu"
            >
              <Icon name="menu" size={22} />
            </button>
          </div>
        </div>
      </nav>

      {/* ---- Mobile overlay ---- */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-gray-950 overflow-y-auto animate-fadeIn">
          <div className="max-w-lg mx-auto px-6 py-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <Link
                to="/"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2.5"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-indigo-500/20 rounded-lg blur-sm" />
                  <Icon name="shield" size={24} className="text-indigo-400 relative" />
                </div>
                <span className="text-lg font-bold text-white">
                  Navil{' '}
                  <span className="text-xs font-normal text-indigo-400 bg-indigo-400/10 px-1.5 py-0.5 rounded">
                    Cloud
                  </span>
                </span>
              </Link>
              <button
                onClick={() => setMobileOpen(false)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                aria-label="Close menu"
              >
                <Icon name="x" size={22} />
              </button>
            </div>

            {/* Sections */}
            <div className="space-y-8">
              {dropdowns.map((dd) => (
                <div key={dd.label}>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-3">
                    {dd.label}
                  </p>
                  <div className="space-y-1">
                    {dd.sections.flatMap((s) => s.items).map((item) => (
                      <MobileNavLink
                        key={item.label}
                        item={item}
                        onClose={() => setMobileOpen(false)}
                      />
                    ))}
                  </div>
                </div>
              ))}

              {/* Direct links */}
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  More
                </p>
                <div className="space-y-1">
                  <Link
                    to="/docs"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 p-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <Icon name="book" size={16} className="text-indigo-400" />
                    Docs
                  </Link>
                  <Link
                    to="/pricing"
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 p-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <Icon name="tag" size={16} className="text-indigo-400" />
                    Pricing
                  </Link>
                </div>
              </div>
            </div>

            {/* Mobile CTA */}
            <div className="mt-10 pt-6 border-t border-gray-800/60 space-y-3">
              <Link
                to={isAuthEnabled() ? '/sign-up' : '/dashboard'}
                onClick={() => setMobileOpen(false)}
                className="block w-full text-center px-4 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 transition-colors"
              >
                Get Started
              </Link>
              <Link
                to={isAuthEnabled() ? '/sign-in' : '/dashboard'}
                onClick={() => setMobileOpen(false)}
                className="block w-full text-center px-4 py-3 border border-gray-800 text-gray-300 rounded-lg text-sm font-medium hover:bg-white/5 transition-colors"
              >
                Sign in
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

/* ------------------------------------------------------------------ */
/*  Mobile link                                                       */
/* ------------------------------------------------------------------ */

function MobileNavLink({
  item,
  onClose,
}: {
  item: NavItem
  onClose: () => void
}) {
  const inner = (
    <div className="flex items-center gap-3 p-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors">
      <Icon name={item.icon} size={16} className="text-indigo-400" />
      <span>{item.label}</span>
      {item.badge && (
        <span className="text-[10px] font-semibold uppercase tracking-wider text-violet-400 bg-violet-400/10 px-1.5 py-0.5 rounded">
          {item.badge}
        </span>
      )}
      {item.external && (
        <Icon name="external-link" size={12} className="text-gray-500 ml-auto" />
      )}
    </div>
  )

  if (item.external) {
    return (
      <a href={item.to} target="_blank" rel="noopener noreferrer">
        {inner}
      </a>
    )
  }

  return (
    <Link to={item.to} onClick={onClose}>
      {inner}
    </Link>
  )
}
