import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './AuthContext'
import { FullPageSpinner } from '../components/FullPageSpinner'
import { homeFor } from '../lib/home'

/** Only logged-in users get through; everyone else is sent to /login and brought back after. */
export function RequireAuth() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullPageSpinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

/**
 * Login/sign-up pages: logged-in users don't need them. This also runs the moment
 * someone logs in or signs up, so it decides where they land:
 *  - just signed up → dashboard, to see "What's next" once
 *  - sent to log in from a protected page → back to that page
 *  - otherwise → their usual home (see homeFor)
 */
export function GuestOnly() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullPageSpinner />
  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    const to = location.pathname === '/register' ? '/dashboard' : (from ?? homeFor(user))
    return <Navigate to={to} replace />
  }
  return <Outlet />
}
