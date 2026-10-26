import { Link, Outlet, useLocation, useNavigate } from 'react-router'
import type { User } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import { isTabActive, ROLE_BADGES, tabsFor, type NavIconName, type NavTab } from '../lib/navigation'
import { HomeIcon, ProfileCardIcon, SearchIcon, UserIcon, UsersIcon } from './Icons'

const ICONS: Record<NavIconName, (p: { className?: string }) => React.ReactNode> = {
  search: SearchIcon,
  users: UsersIcon,
  user: UserIcon,
  home: HomeIcon,
  profile: ProfileCardIcon,
}

/**
 * Page frame (the footer lives on the landing page only). Logged-in users get a menu for their kind of account: links in the top
 * bar on tablets and computers, and a bottom tab bar on phones (like most phone apps).
 */
export function Layout() {
  const { user } = useAuth()
  const tabs = user ? tabsFor(user) : []

  return (
    <div className={`flex min-h-screen flex-col ${user ? 'pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-0' : ''}`}>
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-surface/95 backdrop-blur">
        <nav aria-label="Main" className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4">
          <Link to={user ? tabs[0].to : '/'} className="flex shrink-0 items-center gap-2">
            <img src="/brights-logo.svg" alt="" width="36" height="36" className="h-9 w-9" />
            <span className="text-xl font-bold text-heading">Brights</span>
          </Link>
          {user ? <SignedInTopBar user={user} tabs={tabs} /> : <GuestTopBar />}
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      {user && <BottomTabBar tabs={tabs} />}
    </div>
  )
}

function GuestTopBar() {
  const { pathname } = useLocation()
  return (
    <div className="flex items-center gap-1 whitespace-nowrap text-sm font-medium sm:gap-2">
      <Link to="/tutors" aria-label="Find a tutor"
        className={`flex items-center gap-1.5 rounded-lg px-2.5 py-2 hover:bg-slate-100 ${pathname.startsWith('/tutors') ? 'text-link' : 'text-slate-700'}`}>
        <SearchIcon className="h-5 w-5" />
        <span className="hidden sm:inline">Find a tutor</span>
      </Link>
      <Link to="/login" className="rounded-lg px-2.5 py-2 text-slate-700 hover:bg-slate-100">Log in</Link>
      <Link to="/register" className="rounded-full bg-brand-deep px-4 py-2 text-white hover:bg-brand">Sign up</Link>
    </div>
  )
}

function RoleBadge({ user }: { user: User }) {
  const badge = ROLE_BADGES[user.account_type] ?? ROLE_BADGES['']
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${badge.className}`}>{badge.label}</span>
}

function SignedInTopBar({ user, tabs }: { user: User; tabs: NavTab[] }) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="flex items-center gap-2 whitespace-nowrap text-sm font-medium">
      {/* Tablets and computers: the menu sits in the top bar. Phones use the bottom bar. */}
      <div className="hidden items-center gap-1 md:flex">
        {tabs.map((tab) => {
          const active = isTabActive(tab, pathname)
          return (
            <Link key={tab.to} to={tab.to} aria-current={active ? 'page' : undefined}
              className={`rounded-lg px-3 py-2 transition ${active ? 'bg-brand-deep/5 text-heading' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}>
              {tab.label}
            </Link>
          )
        })}
      </div>
      <RoleBadge user={user} />
      <button onClick={handleLogout} className="hidden rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 md:block">
        Log out
      </button>
    </div>
  )
}

function BottomTabBar({ tabs }: { tabs: NavTab[] }) {
  const { pathname } = useLocation()
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
      <ul className={`mx-auto grid h-16 max-w-md ${tabs.length === 2 ? 'grid-cols-2' : tabs.length === 4 ? 'grid-cols-4' : 'grid-cols-3'}`}>
        {tabs.map((tab) => {
          const active = isTabActive(tab, pathname)
          const Icon = ICONS[tab.icon]
          return (
            <li key={tab.to}>
              <Link to={tab.to} aria-current={active ? 'page' : undefined}
                className={`flex h-full flex-col items-center justify-center gap-1 text-[11px] font-semibold transition ${active ? 'text-link' : 'text-slate-500 active:text-slate-800'}`}>
                <span className={`flex h-7 w-12 items-center justify-center rounded-full transition ${active ? 'bg-brand/10' : ''}`}>
                  <Icon className="h-[22px] w-[22px]" />
                </span>
                {tab.label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
