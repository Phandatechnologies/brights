import { apiFetch } from './client'

/** Matches backend/staffpanel (the staff area API). */

export type StaffOverview = {
  applications_pending: number
  applications_more_info: number
  oldest_pending_days: number | null
  photos_waiting: number
  reports_open: number
  reports_urgent: number
  totals: { learners: number; parents: number; tutors: number; approved_tutors: number }
  django_admin_url: string
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

// ---- Photos ---------------------------------------------------------------------------------

export type PhotoRow = {
  id: number
  name: string
  email: string
  photo_status: 'pending' | 'approved' | 'rejected'
  photo_note: string
  /** Which photo the screen showed; approving only works if it's still this one. */
  version: string
  photo_url: string | null
  updated_at: string
}

export const photoApi = {
  list: (status: string, page = 1) =>
    apiFetch<Page<PhotoRow>>(`/api/staff/photos/?status=${encodeURIComponent(status)}${page > 1 ? `&page=${page}` : ''}`),
  decide: (id: number, input: { action: 'approve' | 'reject'; version: string; note?: string }) =>
    apiFetch<PhotoRow>(`/api/staff/photos/${id}/decide/`, { method: 'POST', body: JSON.stringify(input) }),
}

// ---- Reports --------------------------------------------------------------------------------

export type ReportRow = {
  id: number
  category: string
  category_label: string
  is_urgent: boolean
  holds_tutor: boolean
  status: 'open' | 'closed'
  outcome: '' | 'dismissed' | 'warned' | 'suspended'
  outcome_label: string
  tutor_name: string
  reporter_name: string
  created_at: string
  closed_at: string | null
  days_open: number | null
}

export type ReportAction = 'dismiss' | 'warn' | 'suspend'

export type ReportDetail = ReportRow & {
  description: string
  incident_date: string | null
  reporter_was_minor: boolean
  reporter: { name: string; email: string; account_type: string } | null
  tutor: {
    name: string
    email: string
    profile_id: number
    application_id: number | null
    application_status: ApplicationStatus | null
    application_status_label: string | null
    accepting_learners: boolean
  }
  contacts: { subject: string; grade: number | null; created_at: string }[]
  other_reports: ReportRow[]
  admin_notes: string
  closed_by: string | null
  is_own: boolean
  actions: ReportAction[]
}

export const reportApi = {
  list: (status: string, page = 1) =>
    apiFetch<Page<ReportRow>>(`/api/staff/reports/?status=${encodeURIComponent(status)}${page > 1 ? `&page=${page}` : ''}`),
  get: (id: number) => apiFetch<ReportDetail>(`/api/staff/reports/${id}/`),
  decide: (id: number, input: { action: ReportAction; message: string; notes: string }) =>
    apiFetch<ReportDetail>(`/api/staff/reports/${id}/decide/`, { method: 'POST', body: JSON.stringify(input) }),
}

// ---- People ---------------------------------------------------------------------------------

export type UserRow = {
  id: number
  name: string
  email: string
  account_type: 'learner' | 'parent' | 'tutor' | 'staff' | ''
  account_type_label: string
  is_active: boolean
  email_verified: boolean
  is_minor: boolean
  date_joined: string
}

export type UserAction = 'block' | 'unblock' | 'resend_confirmation'

export type UserDetail = UserRow & {
  first_name: string
  date_of_birth: string
  age: number
  last_login: string | null
  tutor: {
    application_id: number | null
    application_status: ApplicationStatus | null
    application_status_label: string | null
    profile_id: number | null
    photo_status: string | null
    is_listed: boolean
  } | null
  contacts_made: number
  reports_made: number
  reports_about: number
  history: { when: string; by: string | null; what: string }[]
  is_self: boolean
  actions: UserAction[]
}

export const userApi = {
  list: (params: { type: string; q?: string; page?: number }) => {
    const query = new URLSearchParams({ type: params.type })
    if (params.q) query.set('q', params.q)
    if (params.page && params.page > 1) query.set('page', String(params.page))
    return apiFetch<Page<UserRow>>(`/api/staff/users/?${query}`)
  },
  get: (id: number) => apiFetch<UserDetail>(`/api/staff/users/${id}/`),
  act: (id: number, action: UserAction, reason = '') =>
    apiFetch<UserDetail>(`/api/staff/users/${id}/action/`, { method: 'POST', body: JSON.stringify({ action, reason }) }),
}

// ---- How-to videos --------------------------------------------------------------------------

export type Video = {
  id: number
  title: string
  description: string
  topic: string
  topic_label: string
  youtube_id: string
  order: number
  is_published: boolean
  created_at: string
}

export type VideoInput = Partial<Pick<Video, 'title' | 'description' | 'topic' | 'youtube_id' | 'order' | 'is_published'>>

export const videoApi = {
  list: () => apiFetch<{ topics: { value: string; label: string }[]; videos: Video[] }>('/api/staff/videos/'),
  add: (input: VideoInput) => apiFetch<Video>('/api/staff/videos/', { method: 'POST', body: JSON.stringify(input) }),
  update: (id: number, input: VideoInput) => apiFetch<Video>(`/api/staff/videos/${id}/`, { method: 'PATCH', body: JSON.stringify(input) }),
  remove: (id: number) => apiFetch<void>(`/api/staff/videos/${id}/`, { method: 'DELETE' }),
}
