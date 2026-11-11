import type { User } from '../api/auth'

export type NavIconName = 'search' | 'users' | 'user' | 'home' | 'profile' | 'clipboard' | 'photo' | 'flag' | 'more'

export type NavTab = {
  to: string
  label: string
  icon: NavIconName
  /** Other paths that should also highlight this tab. */
  alsoActive?: string[]
}

/** Each kind of account gets its own menu. On phones these become the bottom tab bar. */
export function tabsFor(user: Pick<User, 'account_type' | 'is_staff'>): NavTab[] {
  if (user.is_staff) {
    // The Brights team: the staff area replaces the Django admin for day-to-day work.
    return [
      { to: '/staff', label: 'Staff home', icon: 'home' },
      { to: '/staff/applications', label: 'Applications', icon: 'clipboard' },
      { to: '/staff/photos', label: 'Photos', icon: 'photo' },
      { to: '/staff/reports', label: 'Reports', icon: 'flag' },
      // Users, how-to videos and the staff member's own account live under "More".
      { to: '/staff/more', label: 'More', icon: 'more', alsoActive: ['/staff/users', '/staff/videos', '/account'] },
    ]
  }
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
    default: // an account with no type that isn't staff (shouldn't happen): keep it simple
      return [
        { to: '/dashboard', label: 'Home', icon: 'home' },
        { to: '/account', label: 'Account', icon: 'user' },
      ]
  }
}

export const ROLE_BADGES: Record<string, { label: string; className: string }> = {
  learner: { label: 'Learner', className: 'bg-brand-deep/10 text-heading' },
  parent: { label: 'Parent', className: 'bg-brand-deep/10 text-heading' },
  tutor: { label: 'Tutor', className: 'bg-brand-soft/15 text-pass' },
  '': { label: 'Staff', className: 'bg-brand-sun/20 text-amber-900' },
}

/** True when `pathname` is this tab or one of its sub-pages. */
export function isTabActive(tab: NavTab, pathname: string): boolean {
  // "/staff" is the staff home only; its sub-pages have their own tabs.
  if (tab.to === '/staff') return pathname === '/staff'
  return [tab.to, ...(tab.alsoActive ?? [])].some((p) => pathname === p || pathname.startsWith(`${p}/`))
}
