import { SignedIn, SignedOut } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { isAuthEnabled } from './ClerkProviderWrapper'

/**
 * Route guard that redirects unauthenticated visitors to `/sign-in`.
 *
 * When Clerk is not configured the component is transparent — children
 * render unconditionally, preserving the current public-access behaviour.
 */
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!isAuthEnabled()) return <>{children}</>

  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <Navigate to="/sign-in" replace />
      </SignedOut>
    </>
  )
}
