import { useAuth } from '@clerk/clerk-react'
import { useEffect } from 'react'
import { setAuthTokenFetcher } from '../api'

/**
 * Bridges Clerk's React hook (`useAuth().getToken`) to the imperative
 * `api.ts` module so every outgoing API call includes a Bearer token.
 *
 * Render this component once inside `<ClerkProvider>`.
 */
export default function AuthTokenBridge() {
  const { getToken } = useAuth()

  useEffect(() => {
    setAuthTokenFetcher(() => getToken())
  }, [getToken])

  return null
}
