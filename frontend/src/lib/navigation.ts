import type { User } from '../api/auth'

export type NavIconName = 'search' | 'users' | 'user' | 'home' | 'profile'

export type NavTab = {
  to: string
  label: string
  icon: NavIconName
  /** Other paths that should also highlight this tab. */
  alsoActive?: string[]
}

/** Each kind of account gets its own menu. On phones these become the bottom tab bar. */
export function tabsFor(user: Pick<User, 'account_type'>): NavTab[] {
  switch (user.account_type) {
    case 'learner':
    case 'parent':
      return [
        { to: '/tutors', label: 'Find a tutor', icon: 'search' },
        { to: '/my-tutors', label: 'My tutors', icon: 'users' },
        { to: '/account', label: 'Account', icon: 'user' },
      ]
    case 'tutor':
      return [
        { to: '/dashboard', label: 'Home', icon: 'home', alsoActive: ['/tutor/apply'] },
        { to: '/tutor/profile', label: 'My profile', icon: 'profile' },
        { to: '/account', label: 'Account', icon: 'user' },
      ]
    default: // staff: they work in the Django admin
      return [
        { to: '/dashboard', label: 'Home', icon: 'home' },
        { to: '/account', label: 'Account', icon: 'user' },
      ]
  }
}

export const ROLE_BADGES: Record<string, { label: string; className: string }> = {
  learner: { label: 'Learner', className: 'bg-brand-navy/10 text-heading' },
  parent: { label: 'Parent', className: 'bg-brand-navy/10 text-heading' },
  tutor: { label: 'Tutor', className: 'bg-brand-teal/15 text-pass' },
  '': { label: 'Staff', className: 'bg-brand-gold/20 text-amber-900' },
}

/** True when `pathname` is this tab or one of its sub-pages. */
export function isTabActive(tab: NavTab, pathname: string): boolean {
  return [tab.to, ...(tab.alsoActive ?? [])].some((p) => pathname === p || pathname.startsWith(`${p}/`))
}
