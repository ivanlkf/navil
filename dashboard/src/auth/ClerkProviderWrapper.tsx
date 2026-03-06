import { ClerkProvider } from '@clerk/clerk-react'
import type { ReactNode } from 'react'

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined

/** Whether Clerk auth is configured (publishable key present). */
export function isAuthEnabled(): boolean {
  return !!CLERK_KEY
}

/**
 * Wraps children in `<ClerkProvider>` when the publishable key is set.
 * Falls through transparently when Clerk is not configured, so existing
 * behaviour (no auth, all routes public) is preserved.
 */
export default function ClerkProviderWrapper({ children }: { children: ReactNode }) {
  if (!CLERK_KEY) return <>{children}</>

  return (
    <ClerkProvider publishableKey={CLERK_KEY}>
      {children}
    </ClerkProvider>
  )
}
