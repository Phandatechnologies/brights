import { apiFetch } from './client'

export type ContactResult = { whatsapp_url: string; message: string }
export type ContactHistoryItem = { tutor_id: number; name: string; last_contacted: string; available: boolean }

export const contactApi = {
  contact: (tutorId: number, data: { subject?: number | null; grade?: number | null }) =>
    apiFetch<ContactResult>(`/api/tutors/${tutorId}/contact/`, { method: 'POST', body: JSON.stringify(data) }),
  acknowledgeSafety: () => apiFetch<{ required: boolean }>('/api/contact/safety/', { method: 'POST' }),
  history: () => apiFetch<ContactHistoryItem[]>('/api/contact/history/'),
}
