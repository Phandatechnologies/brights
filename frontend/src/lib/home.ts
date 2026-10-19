import type { User } from '../api/auth'

/**
 * Where a logged-in user lands by default.
 * Learners and parents go straight to search (they saw "What's next" once, right after
 * signing up). Tutors and staff go to their dashboard for status and to-dos.
 */
export function homeFor(user: Pick<User, 'account_type'>): string {
  return user.account_type === 'learner' || user.account_type === 'parent' ? '/tutors' : '/dashboard'
}

// Menu pages aren't worth returning to after logging in: people open them on purpose.
const MENU_PAGES = ['/account', '/my-tutors', '/dashboard']

/**
 * Where to go right after logging in. If the person was sent to log in from a page where
 * they were doing something specific (e.g. a tutor's profile they wanted to contact), go
 * back there. Otherwise (including an old Account or My tutors tab) go to their home.
 */
export function afterLogin(user: Pick<User, 'account_type'>, from?: string | null): string {
  return from && !MENU_PAGES.includes(from) ? from : homeFor(user)
}
