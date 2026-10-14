import { ApiError, apiFetch } from './client'

export type Pathway = 'academic' | 'teacher'
export type ApplicationStatus = 'draft' | 'pending' | 'more_info' | 'approved' | 'rejected' | 'suspended'
export type DocumentKind = 'id_document' | 'matric_results' | 'teaching_qualification' | 'sace_certificate'

export type Subject = { id: number; name: string }

/** Shapes match backend/tutors/serializers.py */
export type SubjectDecision = 'pending' | 'approved' | 'declined'

export type ApplicationSubject = {
  id: number
  subject: Subject
  matric_mark: number | null
  grades: number[]
  decision: SubjectDecision
  decision_note: string
}

export type ApplicationDocument = {
  id: number
  kind: DocumentKind
  kind_label: string
  original_name: string
  content_type: string
  size: number
  uploaded_at: string
}

export type TutorApplication = {
  id: number
  pathway: Pathway
  status: ApplicationStatus
  status_label: string
  is_editable: boolean
  sace_number: string
  qualification_name: string
  reviewer_message: string
  subjects: ApplicationSubject[]
  documents: ApplicationDocument[]
  required_documents: { kind: DocumentKind; label: string; uploaded: boolean }[]
  reapply_available_from: string | null
  submitted_at: string | null
}

export type SubjectChoice = { subject: number; matric_mark: number | null; grades: number[] }

export type ApplicationUpdate = Partial<{
  pathway: Pathway
  sace_number: string
  qualification_name: string
  subjects: SubjectChoice[]
}>

const BASE = '/api/tutor/application/'
const json = (method: string, data?: unknown) => ({ method, body: data === undefined ? undefined : JSON.stringify(data) })

export const tutorApi = {
  subjects: () => apiFetch<Subject[]>('/api/subjects/'),

  /** The tutor's application, or null if they haven't started one. */
  async getApplication(): Promise<TutorApplication | null> {
    try {
      return await apiFetch<TutorApplication>(BASE)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return null
      throw err
    }
  },

  start: (pathway: Pathway) => apiFetch<TutorApplication>(BASE, json('POST', { pathway })),
  update: (data: ApplicationUpdate) => apiFetch<TutorApplication>(BASE, json('PATCH', data)),
  submit: () => apiFetch<TutorApplication>(`${BASE}submit/`, { method: 'POST' }),
  reapply: () => apiFetch<TutorApplication>(`${BASE}reapply/`, { method: 'POST' }),

  uploadDocument(kind: DocumentKind, file: File) {
    const form = new FormData()
    form.append('kind', kind)
    form.append('file', file)
    return apiFetch<ApplicationDocument>(`${BASE}documents/`, { method: 'POST', body: form })
  },

  deleteDocument: (id: number) => apiFetch<void>(`${BASE}documents/${id}/`, { method: 'DELETE' }),
}
