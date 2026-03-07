/**
 * Self-hosted OSS dashboard.
 *
 * Docs live at https://navil.ai/docs (central version tree).
 * Landing, Pricing, About, Blog, Solutions belong in the private cloud repo.
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import ScrollToTop from './components/ScrollToTop'
import { isAuthEnabled } from './auth/ClerkProviderWrapper'
import AuthTokenBridge from './auth/AuthTokenBridge'
import ProtectedRoute from './auth/ProtectedRoute'
import DashboardLayout from './layouts/DashboardLayout'

import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'

// Dashboard pages
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
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

export default function App() {
  return (
    <>
      <ScrollToTop />
      {isAuthEnabled() && <AuthTokenBridge />}

      <Routes>
        {/* Root → dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Auth routes */}
        <Route path="/sign-in/*" element={<SignIn />} />
        <Route path="/sign-up/*" element={<SignUp />} />

        {/* Protected dashboard routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="gateway" element={<Gateway />} />
          <Route path="pentest" element={<Pentest />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="agents" element={<Agents />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="credentials" element={<Credentials />} />
          <Route path="policy" element={<Policy />} />
          <Route path="feedback" element={<Feedback />} />
          <Route path="self-healing" element={<SelfHealing />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Catch-all → dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  )
}
