import { Link, Outlet, useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthContext'

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <img src="/brights-logo.png" alt="" className="h-9 w-9" />
            <span className="text-xl font-bold text-brand-navy">Brights</span>
          </Link>

          <div className="flex items-center gap-2 text-sm font-medium">
            {user ? (
              <>
                <Link to="/dashboard" className="rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-brand-navy px-3 py-2 text-white hover:bg-brand-blue"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:justify-between">
          <p>Brights is a Phanda Technologies product.</p>
          <p>
            Photo by{' '}
            <a href="https://unsplash.com/@silverkblack" className="underline hover:text-slate-700" target="_blank" rel="noreferrer">
              Vitaly Gariev
            </a>{' '}
            on Unsplash
          </p>
        </div>
      </footer>
    </div>
  )
}
