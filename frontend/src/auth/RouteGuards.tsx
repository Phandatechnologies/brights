import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './AuthContext'
import { FullPageSpinner } from '../components/FullPageSpinner'

/** Only logged-in users get through; everyone else is sent to /login and brought back after. */
export function RequireAuth() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <FullPageSpinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

/** Login/sign-up pages: logged-in users don't need them, so send them to their dashboard. */
export function GuestOnly() {
  const { user, loading } = useAuth()
  if (loading) return <FullPageSpinner />
  if (user) return <Navigate to="/dashboard" replace />
  return <Outlet />
}
