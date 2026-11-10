/** Date helpers for the staff pages. */

export function formatDate(value: string | null, withTime = false): string {
  if (!value) return '—'
  const date = new Date(value)
  return date.toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' }) +
    (withTime ? `, ${date.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' })}` : '')
}

export function daysLabel(days: number): string {
  if (days <= 0) return 'today'
  return days === 1 ? '1 day' : `${days} days`
}
