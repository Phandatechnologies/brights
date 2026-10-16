import { apiFetch } from './client'

export type ReportCategory = 'child_safety' | 'inappropriate' | 'fake_credentials' | 'scam' | 'other'

/** Same order and wording as backend/moderation/rules.py */
export const REPORT_CATEGORIES: { value: ReportCategory; label: string }[] = [
  { value: 'child_safety', label: 'A safety concern involving a child' },
  { value: 'inappropriate', label: 'Inappropriate messages or behaviour' },
  { value: 'fake_credentials', label: 'Fake or misleading qualifications' },
  { value: 'scam', label: 'Scam, no-show or payment problem' },
  { value: 'other', label: 'Something else' },
]

export const moderationApi = {
  report: (tutorId: number | string, data: { category: ReportCategory; description: string; incident_date: string | null }) =>
    apiFetch<{ id: number; urgent: boolean; tutor_hidden: boolean }>(`/api/tutors/${tutorId}/report/`, { method: 'POST', body: JSON.stringify(data) }),
}
