import { apiFetch } from './client'

export type AccountType = 'learner' | 'parent' | 'tutor'

/** Matches accounts/serializers.py UserSerializer */
export type User = {
  id: number
  email: string
  first_name: string
  last_name: string
  date_of_birth: string
  account_type: AccountType | ''
  is_minor: boolean
  email_verified: boolean
}

export type RegisterInput = {
  email: string
  password: string
  first_name: string
  last_name: string
  date_of_birth: string // YYYY-MM-DD
  account_type: AccountType
  guardian_consent: boolean
  guardian_name: string
}

const json = (data: unknown) => ({ method: 'POST', body: JSON.stringify(data) })

export const authApi = {
  me: () => apiFetch<User>('/api/auth/me/'),
  login: (email: string, password: string) => apiFetch<User>('/api/auth/login/', json({ email, password })),
  register: (input: RegisterInput) => apiFetch<User>('/api/auth/register/', json(input)),
  logout: () => apiFetch<void>('/api/auth/logout/', { method: 'POST' }),
  verifyEmail: (uid: string, token: string) => apiFetch<{ verified: boolean }>('/api/auth/verify-email/', json({ uid, token })),
  resendVerification: () => apiFetch<{ sent: boolean }>('/api/auth/resend-verification/', { method: 'POST' }),
  requestPasswordReset: (email: string) => apiFetch<{ detail: string }>('/api/auth/password-reset/', json({ email })),
  confirmPasswordReset: (uid: string, token: string, new_password: string) =>
    apiFetch<{ detail: string }>('/api/auth/password-reset/confirm/', json({ uid, token, new_password })),
}
