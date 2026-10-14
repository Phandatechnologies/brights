// Shape of the JSON returned by GET /api/health/ (see backend/core/views.py).
export type HealthResponse = {
  status: 'ok' | 'degraded'
  database: 'connected' | 'unavailable'
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health/')
  // 503 still carries a valid JSON body describing what is down.
  if (!response.ok && response.status !== 503) {
    throw new Error(`Unexpected response: ${response.status}`)
  }
  return response.json()
}
