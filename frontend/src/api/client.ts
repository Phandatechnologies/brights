/**
 * Small wrapper around fetch for talking to the Django API.
 *
 * - Sends cookies (the session cookie is how Django knows who you are).
 * - Adds the CSRF token to every request that changes data.
 * - Turns Django error responses into an ApiError with per-field messages.
 */

export type FieldErrors = Record<string, string[]>

export class ApiError extends Error {
  status: number
  fieldErrors: FieldErrors
  /** Machine-readable reason from the API, e.g. "email_unverified". */
  code?: string

  constructor(status: number, message: string, fieldErrors: FieldErrors = {}, code?: string) {
    super(message)
    this.status = status
    this.fieldErrors = fieldErrors
    this.code = code
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split('=')[1]) : null
}

/** Ask Django to set the csrftoken cookie (call once when the app starts). */
export async function ensureCsrfCookie(): Promise<void> {
  await fetch('/api/auth/csrf/', { credentials: 'same-origin' })
}

/** Collect every string inside a (possibly nested) DRF error value. */
function flattenMessages(value: unknown): string[] {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(flattenMessages)
  if (value && typeof value === 'object') return Object.values(value).flatMap(flattenMessages)
  return [String(value)]
}

/** DRF errors look like {"detail": "..."} or {"field": ["msg", ...], "non_field_errors": [...]} */
function parseErrors(body: unknown): { message: string; fieldErrors: FieldErrors } {
  if (!body || typeof body !== 'object') return { message: 'Something went wrong.', fieldErrors: {} }

  const data = body as Record<string, unknown>
  if (typeof data.detail === 'string') return { message: data.detail, fieldErrors: {} }

  const fieldErrors: FieldErrors = {}
  for (const [key, value] of Object.entries(data)) {
    fieldErrors[key] = flattenMessages(value)
  }
  const general = fieldErrors.non_field_errors?.[0]
  return { message: general ?? 'Please correct the highlighted fields.', fieldErrors }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (typeof options.body === 'string') headers.set('Content-Type', 'application/json')
  if (method !== 'GET') {
    const token = readCookie('csrftoken')
    if (token) headers.set('X-CSRFToken', token)
  }

  let response: Response
  try {
    response = await fetch(path, { ...options, method, headers, credentials: 'same-origin' })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet connection and try again.')
  }

  if (response.status === 204) return undefined as T

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 429) {
      throw new ApiError(429, 'Too many attempts. Please wait a minute and try again.')
    }
    if (response.status === 403 && body === null) {
      // Django's CSRF rejection is an HTML page, not JSON.
      throw new ApiError(403, 'Your session expired. Please refresh the page and try again.')
    }
    if (response.status >= 500 || body === null) {
      throw new ApiError(response.status, 'The server had a problem. Please try again in a moment.')
    }
    const { message, fieldErrors } = parseErrors(body)
    const code = typeof (body as { code?: unknown }).code === 'string' ? (body as { code: string }).code : undefined
    if (code) delete fieldErrors.code
    throw new ApiError(response.status, message, fieldErrors, code)
  }
  return body as T
}
