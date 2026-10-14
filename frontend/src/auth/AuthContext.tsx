import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, type RegisterInput, type User } from '../api/auth'
import { ensureCsrfCookie } from '../api/client'

type AuthState = {
  user: User | null
  /** True until we've asked the server whether someone is already logged in. */
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  register: (input: RegisterInput) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On start-up: get a CSRF cookie, then check for an existing session.
  useEffect(() => {
    ensureCsrfCookie()
      .then(() => authApi.me())
      .then(setUser)
      .catch(() => setUser(null)) // 403 = not logged in, which is fine
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const loggedIn = await authApi.login(email, password)
    setUser(loggedIn)
    return loggedIn
  }, [])

  const register = useCallback(async (input: RegisterInput) => {
    const created = await authApi.register(input)
    setUser(created)
    return created
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
    await ensureCsrfCookie() // Django rotates the token on logout
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
