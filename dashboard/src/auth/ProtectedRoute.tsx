import { SignedIn, SignedOut } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { isAuthEnabled, isAnyAuthRequired } from './ClerkProviderWrapper'
import { useLocalAuth } from './LocalAuthContext'

/**
 * Route guard for dashboard routes.
 *
 * - Clerk key set → Clerk SignedIn / SignedOut gates.
 * - VITE_NAVIL_AUTH=true → local auth (localStorage session).
 * - Neither set → no auth, dashboard is open (default for self-hosted).
 */
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  if (isAuthEnabled()) {
    return (
      <>
        <SignedIn>{children}</SignedIn>
        <SignedOut>
          <Navigate to="/sign-in" replace />
        </SignedOut>
      </>
    )
  }

  if (isAnyAuthRequired()) {
    return <LocalGuard>{children}</LocalGuard>
  }

  // No auth configured — pass through (self-hosted default)
  return <>{children}</>
}

function LocalGuard({ children }: { children: ReactNode }) {
  const { user } = useLocalAuth()
  if (!user) return <Navigate to="/sign-in" replace />
  return <>{children}</>
}
