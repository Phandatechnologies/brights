import { useState, type FormEvent } from 'react'
import { Link, useLocation, useParams } from 'react-router'
import { ApiError, type FieldErrors } from '../api/client'
import { REPORT_CATEGORIES, moderationApi, type ReportCategory } from '../api/moderation'
import { FieldError, FormAlert } from '../components/Form'

const MIN = 20
const MAX = 2000
const TODAY = new Date().toISOString().slice(0, 10)

/** /tutors/:id/report — report a tutor. The tutor is never told who reported them. */
export function ReportPage() {
  const { id = '' } = useParams()
  const location = useLocation()
  const tutorName = (location.state as { tutorName?: string } | null)?.tutorName ?? 'this tutor'

  const [category, setCategory] = useState<ReportCategory | ''>('')
  const [description, setDescription] = useState('')
  const [incidentDate, setIncidentDate] = useState('')
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState<{ urgent: boolean; hidden: boolean } | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setErrors({})
    if (!category) return setErrors({ category: ['Choose what the problem is.'] })
    if (description.trim().length < MIN) return setErrors({ description: [`Please describe what happened in at least ${MIN} characters.`] })
    setBusy(true)
    try {
      const result = await moderationApi.report(id, { category, description: description.trim(), incident_date: incidentDate || null })
      setSent({ urgent: result.urgent, hidden: result.tutor_hidden })
      window.scrollTo({ top: 0 })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setErrors(err.fieldErrors)
      } else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (sent) {
    return (
      <section className="mx-auto max-w-2xl px-4 py-14">
        <div role="status" className="rounded-2xl border border-brand-soft/50 bg-brand-soft/10 p-6">
          <h1 className="text-2xl font-bold text-heading">Thank you. We've received your report.</h1>
          <p className="mt-3 leading-relaxed text-slate-700">
            {sent.hidden
              ? 'Because this is a child-safety concern, the tutor has been removed from search while our team reviews it.'
              : sent.urgent
                ? 'Because this is a child-safety concern, our team has been alerted and will review it urgently.'
                : 'Our team will review it and take action if needed.'}{' '}
            We'll email you when the review is finished. The tutor won't be told who reported them.
          </p>
        </div>
        <EmergencyNote />
        <Link to="/dashboard" className="mt-6 inline-block font-medium text-link hover:underline">Back to your dashboard</Link>
      </section>
    )
  }

  return (
    <section className="mx-auto max-w-2xl px-4 py-10 sm:py-14">
      <h1 className="text-3xl font-bold tracking-[-0.02em] text-heading">Report {tutorName}</h1>
      <p className="mt-2 leading-relaxed text-slate-700">
        Reports go only to the Brights safety team. The tutor won't see your name or what you wrote.
      </p>
      <EmergencyNote />

      <form onSubmit={submit} className="mt-8 space-y-6" noValidate>
        <FormAlert message={error} />
        <fieldset>
          <legend className="mb-2 font-medium text-slate-800">What's the problem?</legend>
          <div className="space-y-2">
            {REPORT_CATEGORIES.map((c) => (
              <label key={c.value}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition ${
                  category === c.value ? 'border-brand bg-brand/5 ring-1 ring-brand' : 'border-slate-300 bg-surface hover:border-slate-400'
                }`}>
                <input type="radio" name="category" value={c.value} checked={category === c.value}
                  onChange={() => setCategory(c.value)} className="accent-brand" />
                <span className="text-slate-900">{c.label}</span>
              </label>
            ))}
          </div>
          <FieldError messages={errors.category} />
          {category === 'child_safety' && (
            <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-900">
              Our team is alerted straight away. If you contacted this tutor through Brights, they're also removed
              from search while we review your report.
            </p>
          )}
        </fieldset>

        <div>
          <label htmlFor="description" className="mb-1 block font-medium text-slate-800">What happened?</label>
          <textarea id="description" rows={7} maxLength={MAX} value={description} onChange={(e) => setDescription(e.target.value)}
            aria-describedby="description-hint"
            placeholder="Describe what happened, when, and anything the tutor said or did. Include as much detail as you can."
            className="block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 leading-relaxed outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
          <p id="description-hint" className="mt-1 text-right text-xs text-slate-500">{description.length} / {MAX}</p>
          <FieldError messages={errors.description} />
        </div>

        <div className="max-w-xs">
          <label htmlFor="incident-date" className="mb-1 block font-medium text-slate-800">When did it happen? (optional)</label>
          <input id="incident-date" type="date" max={TODAY} value={incidentDate} onChange={(e) => setIncidentDate(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5" />
          <FieldError messages={errors.incident_date} />
        </div>

        <div className="flex justify-end border-t border-slate-200 pt-6">
          <button type="submit" disabled={busy}
            className="rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand disabled:opacity-60">
            {busy ? 'Sending…' : 'Send report'}
          </button>
        </div>
      </form>
    </section>
  )
}

function EmergencyNote() {
  return (
    <p className="mt-4 rounded-lg border border-slate-200 bg-chalk p-4 text-sm leading-relaxed text-slate-700">
      If a child is in immediate danger, call <strong>SAPS on 10111</strong> or <strong>Childline on 116</strong> (free, 24 hours).
    </p>
  )
}
