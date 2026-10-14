/**
 * Mirrors backend/accounts/rules.py so the form can guide people as they type.
 * The backend is the real authority: it re-checks every rule on submit.
 */
export const ADULT_AGE = 18
export const MIN_LEARNER_AGE = 12

/** Age in whole years today, or null if the date is empty/invalid. */
export function ageFromIsoDate(iso: string, today = new Date()): number | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (!match) return null
  const [year, month, day] = match.slice(1).map(Number)
  let age = today.getFullYear() - year
  const hadBirthday =
    today.getMonth() + 1 > month || (today.getMonth() + 1 === month && today.getDate() >= day)
  if (!hadBirthday) age -= 1
  return age
}
