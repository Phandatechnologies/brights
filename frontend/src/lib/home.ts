import type { User } from '../api/auth'

/**
 * Where a logged-in user lands by default.
 * Learners and parents go straight to search (they saw "What's next" once, right after
 * signing up). Tutors and staff go to their dashboard for status and to-dos.
 */
export function homeFor(user: Pick<User, 'account_type'>): string {
  return user.account_type === 'learner' || user.account_type === 'parent' ? '/tutors' : '/dashboard'
}
