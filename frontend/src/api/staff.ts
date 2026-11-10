import { apiFetch } from './client'

/** Matches backend/staffpanel (the staff area API). */

export type StaffOverview = {
  applications_pending: number
  applications_more_info: number
  oldest_pending_days: number | null
  photos_waiting: number
  totals: { learners: number; parents: number; tutors: number; approved_tutors: number }
}

export type ApplicationStatus = 'draft' | 'pending' | 'more_info' | 'approved' | 'rejected' | 'suspended'

export type ApplicationRow = {
  id: number
  name: string
  email: string
  pathway: 'academic' | 'teacher'
  pathway_label: string
  status: ApplicationStatus
  status_label: string
  subject_count: number | null
  submitted_at: string | null
  updated_at: string
  days_waiting: number | null
}

export type SubjectDecision = 'pending' | 'approved' | 'declined'

export type ReviewSubject = {
  id: number
  subject: string
  matric_mark: number | null
  grades: number[]
  decision: SubjectDecision
  decision_note: string
  below_minimum: boolean
}

export type ReviewDocument = {
  id: number
  kind: string
  kind_label: string
  name: string
  content_type: string
  size: number
  uploaded_at: string
  url: string | null
}

export type HistoryEvent = {
  action: string
  actor: string | null
  from_status: ApplicationStatus
  to_status: ApplicationStatus
  note: string
  details: { subject: string; decision: string; note: string }[]
  created_at: string
}

export type ReviewAction = 'approve' | 'request_info' | 'reject' | 'suspend' | 'reinstate'

export type ApplicationDetail = ApplicationRow & {
  first_name: string
  date_of_birth: string
  age: number
  email_verified: boolean
  is_active: boolean
  sace_number: string
  qualification_name: string
  reviewer_message: string
  reviewed_at: string | null
  reviewed_by: string | null
  min_mark: number
  subjects: ReviewSubject[]
  documents: ReviewDocument[]
  can_view_documents: boolean
  history: HistoryEvent[]
  is_own: boolean
  actions: ReviewAction[]
  profile_id: number | null
}

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] }

export type DecisionInput = {
  action: ReviewAction
  message: string
  decisions?: { id: number; decision: SubjectDecision; note: string }[]
}

export const staffApi = {
  overview: () => apiFetch<StaffOverview>('/api/staff/overview/'),
  applications: (params: { status: string; q?: string; page?: number }) => {
    const query = new URLSearchParams({ status: params.status })
    if (params.q) query.set('q', params.q)
    if (params.page && params.page > 1) query.set('page', String(params.page))
    return apiFetch<Page<ApplicationRow>>(`/api/staff/applications/?${query}`)
  },
  application: (id: number) => apiFetch<ApplicationDetail>(`/api/staff/applications/${id}/`),
  decide: (id: number, input: DecisionInput) =>
    apiFetch<ApplicationDetail>(`/api/staff/applications/${id}/decide/`, { method: 'POST', body: JSON.stringify(input) }),
}
