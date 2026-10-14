/**
 * Mirrors backend/tutors/rules.py so the form can warn early.
 * The backend re-checks everything; these are for guidance only.
 */
export const MIN_SUBJECT_MARK = 60
export const GRADES = [8, 9, 10, 11, 12] as const
export const MAX_UPLOAD_MB = 5
export const ACCEPTED_FILES = '.pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png'

export function markProblem(mark: number | null): string | null {
  if (mark === null || Number.isNaN(mark)) return 'Enter your Matric mark.'
  if (mark < 0 || mark > 100) return 'Marks are between 0 and 100.'
  if (mark < MIN_SUBJECT_MARK) return `You need at least ${MIN_SUBJECT_MARK}% to tutor this subject.`
  return null
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
