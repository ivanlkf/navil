import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

interface LocalUser {
  email: string
  name: string
}

interface LocalAuthContextValue {
  user: LocalUser | null
  signIn: (email: string, name?: string) => void
  signOut: () => void
}

const KEY = 'navil_local_user'

function loadUser(): LocalUser | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    return JSON.parse(raw) as LocalUser
  } catch {
    return null
  }
}

const LocalAuthContext = createContext<LocalAuthContextValue>({
  user: null,
  signIn: () => {},
  signOut: () => {},
})

export function LocalAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<LocalUser | null>(loadUser)

  const signIn = useCallback((email: string, name?: string) => {
    const u: LocalUser = { email, name: name || email.split('@')[0] }
    localStorage.setItem(KEY, JSON.stringify(u))
    setUser(u)
  }, [])

  const signOut = useCallback(() => {
    localStorage.removeItem(KEY)
    setUser(null)
  }, [])

  return (
    <LocalAuthContext.Provider value={{ user, signIn, signOut }}>
      {children}
    </LocalAuthContext.Provider>
  )
}

export function useLocalAuth() {
  return useContext(LocalAuthContext)
}
