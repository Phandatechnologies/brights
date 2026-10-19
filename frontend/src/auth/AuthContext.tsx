import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, type RegisterInput, type User } from '../api/auth'
import { ApiError, ensureCsrfCookie } from '../api/client'

type AuthState = {
  user: User | null
  /** True until we've asked the server whether someone is already logged in. */
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  register: (input: RegisterInput) => Promise<User>
  logout: () => Promise<void>
  /** Re-fetch the logged-in user (e.g. after verifying their email). */
  refresh: () => Promise<void>
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

  const refresh = useCallback(async () => {
    try {
      setUser(await authApi.me())
    } catch (err) {
      // Only a real "not logged in" answer logs the user out here; a dropped
      // connection (common on phones) leaves them signed in.
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refresh }),
    [user, loading, login, register, logout, refresh],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
