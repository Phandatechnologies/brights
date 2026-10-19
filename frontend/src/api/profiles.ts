import { apiFetch } from './client'

export type Area = { id: number; name: string; province: string; province_label: string }
export type Province = { value: string; label: string }

/** Matches profiles/serializers.py PublicTutorSerializer. No contact details by design. */
export type PublicTutor = {
  id: number
  full_name: string
  bio: string
  hourly_rate: number
  teaches_online: boolean
  teaches_in_person: boolean
  area: Area | null
  availability: string
  subjects: { id: number; name: string; grades: number[] }[]
  verification: string
  photo_url: string | null
}

export type SearchPage = { count: number; next: string | null; previous: string | null; results: PublicTutor[] }

export type PhotoStatus = 'none' | 'pending' | 'approved' | 'rejected'

export type OwnProfile = {
  /** Public profile id: /tutors/:id */
  id: number
  bio: string
  hourly_rate: number | null
  teaches_online: boolean
  teaches_in_person: boolean
  area: number | null
  area_detail: Area | null
  availability: string
  whatsapp_number: string
  photo_status: PhotoStatus
  photo_note: string
  photo_url: string | null
  /** The tutor's own on/off switch for appearing in search. */
  accepting_learners: boolean
  missing_fields: string[]
  is_listed: boolean
}

export type OwnProfileUpdate = Partial<Omit<OwnProfile, 'id' | 'area_detail' | 'photo_status' | 'photo_note' | 'photo_url' | 'missing_fields' | 'is_listed'>>

export type TutorInsights = {
  month_label: string
  views_this_month: number
  views_last_month: number
  contacts_this_month: number
  contacts_last_month: number
  contacts_all_time: number
  top_requests: { subject: string; grade: number | null; count: number }[]
}

export type GuideVideo = { id: number; title: string; description: string; topic: string; topic_label: string; youtube_id: string }
export type GuideVideos = { channel_url: string; videos: GuideVideo[] }

export const profilesApi = {
  areas: () => apiFetch<{ provinces: Province[]; areas: Area[] }>('/api/areas/'),
  search: (params: URLSearchParams) => apiFetch<SearchPage>(`/api/tutors/?${params.toString()}`),
  tutor: (id: string | number) => apiFetch<PublicTutor>(`/api/tutors/${id}/`),

  ownProfile: () => apiFetch<OwnProfile>('/api/tutor/profile/'),
  insights: () => apiFetch<TutorInsights>('/api/tutor/insights/'),
  guides: () => apiFetch<GuideVideos>('/api/tutor/guides/'),
  updateOwnProfile: (data: OwnProfileUpdate) =>
    apiFetch<OwnProfile>('/api/tutor/profile/', { method: 'PATCH', body: JSON.stringify(data) }),
  uploadPhoto(file: File) {
    const form = new FormData()
    form.append('photo', file)
    return apiFetch<OwnProfile>('/api/tutor/profile/photo/', { method: 'POST', body: form })
  },
  deletePhoto: () => apiFetch<void>('/api/tutor/profile/photo/', { method: 'DELETE' }),
}
