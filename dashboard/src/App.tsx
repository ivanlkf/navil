import { useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { isAuthEnabled } from './auth/ClerkProviderWrapper'
import AuthTokenBridge from './auth/AuthTokenBridge'
import ProtectedRoute from './auth/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import Scanner from './pages/Scanner'
import Agents from './pages/Agents'
import Alerts from './pages/Alerts'
import Credentials from './pages/Credentials'
import Policy from './pages/Policy'
import Feedback from './pages/Feedback'
import SelfHealing from './pages/SelfHealing'
import Gateway from './pages/Gateway'
import Pentest from './pages/Pentest'
import Settings from './pages/Settings'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Icon, { type IconName } from './components/Icon'
import UserProfile from './components/UserProfile'

const navItems: { to: string; label: string; icon: IconName }[] = [
  { to: '/', label: 'Dashboard', icon: 'chart' },
  { to: '/gateway', label: 'Gateway', icon: 'gateway' },
  { to: '/pentest', label: 'Pentest', icon: 'pentest' },
  { to: '/scanner', label: 'Scanner', icon: 'scan' },
  { to: '/agents', label: 'Agents', icon: 'bot' },
  { to: '/alerts', label: 'Alerts', icon: 'alert' },
  { to: '/credentials', label: 'Credentials', icon: 'key' },
  { to: '/policy', label: 'Policy', icon: 'shield' },
  { to: '/feedback', label: 'Feedback', icon: 'activity' },
  { to: '/self-healing', label: 'Self-Healing', icon: 'sparkles' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <>
      {/* Bridge Clerk auth tokens into the api.ts fetch layer */}
      {isAuthEnabled() && <AuthTokenBridge />}

      <Routes>
        {/* Public auth routes (only meaningful when Clerk is configured) */}
        <Route path="/sign-in/*" element={<SignIn />} />
        <Route path="/sign-up/*" element={<SignUp />} />

        {/* All other routes go through the main layout */}
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <div className="flex h-screen">
                {/* Mobile backdrop */}
                {sidebarOpen && (
                  <div
                    className="fixed inset-0 bg-black/50 z-30 md:hidden"
                    onClick={() => setSidebarOpen(false)}
                  />
                )}

                {/* Sidebar */}
                <aside
                  className={`fixed inset-y-0 left-0 z-40 w-56 bg-gray-900/80 backdrop-blur-xl border-r border-gray-800/60 flex flex-col
                    transform transition-transform duration-300 md:relative md:translate-x-0
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
                >
                  {/* Subtle gradient overlay */}
                  <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/[0.03] to-transparent pointer-events-none rounded-r-xl" />

                  <div className="relative p-5 border-b border-gray-800/60">
                    <h1 className="text-xl font-bold flex items-center gap-2.5">
                      <div className="relative">
                        <div className="absolute inset-0 bg-indigo-500/20 rounded-lg blur-sm animate-pulseGlow" />
                        <Icon name="shield" size={24} className="text-indigo-400 relative" />
                      </div>
                      <span>
                        Navil{' '}
                        <span className="text-xs font-normal text-indigo-400 bg-indigo-400/10 px-1.5 py-0.5 rounded">
                          Cloud
                        </span>
                      </span>
                    </h1>
                    <p className="text-xs text-gray-500 mt-1.5">Agent Security Dashboard</p>
                  </div>

                  <nav className="relative flex-1 p-3 space-y-1">
                    {navItems.map(({ to, label, icon }) => (
                      <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        onClick={() => setSidebarOpen(false)}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm nav-glow ${
                            isActive
                              ? 'nav-active-bar bg-indigo-500/10 text-indigo-300 font-medium'
                              : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
                          }`
                        }
                      >
                        <Icon name={icon} size={18} />
                        {label}
                      </NavLink>
                    ))}
                  </nav>

                  <UserProfile />
                </aside>

                {/* Main content */}
                <main className="flex-1 overflow-y-auto">
                  {/* Mobile hamburger */}
                  <button
                    onClick={() => setSidebarOpen(true)}
                    aria-label="Open navigation menu"
                    className="md:hidden fixed top-4 left-4 z-20 p-2 bg-gray-900/80 backdrop-blur border border-gray-800/60 rounded-lg text-gray-400 hover:text-gray-200"
                  >
                    <Icon name="menu" size={20} />
                  </button>

                  <div className="max-w-7xl mx-auto px-6 pt-16 pb-6 md:p-8">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/gateway" element={<Gateway />} />
                      <Route path="/pentest" element={<Pentest />} />
                      <Route path="/scanner" element={<Scanner />} />
                      <Route path="/agents" element={<Agents />} />
                      <Route path="/alerts" element={<Alerts />} />
                      <Route path="/credentials" element={<Credentials />} />
                      <Route path="/policy" element={<Policy />} />
                      <Route path="/feedback" element={<Feedback />} />
                      <Route path="/self-healing" element={<SelfHealing />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </div>
                </main>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}
