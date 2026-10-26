import { useState } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { tutorApi, type ApplicationStatus, type TutorApplication } from '../../api/tutor'
import { FormAlert } from '../../components/Form'
import { ApplicationSummary } from './ApplicationSummary'

const COPY: Partial<Record<ApplicationStatus, { title: string; body: string; tone: string }>> = {
  pending: {
    title: "We're reviewing your application",
    body: "Our team checks every document by hand. We'll update this page when there's news, so check back here.",
    tone: 'border-brand/30 bg-brand/5',
  },
  approved: {
    title: "You're approved",
    body: 'You can tutor the subjects marked Approved below. Complete your tutor profile so learners and parents can find you in search.',
    tone: 'border-brand-soft/50 bg-brand-soft/10',
  },
  rejected: {
    title: 'Your application was not approved',
    body: 'See the note from our team below.',
    tone: 'border-red-200 bg-red-50',
  },
  suspended: {
    title: 'Your tutor account is suspended',
    body: "You won't appear in search while your account is suspended.",
    tone: 'border-red-200 bg-red-50',
  },
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-ZA', { day: 'numeric', month: 'long', year: 'numeric' })

export function ApplicationStatusView({ application, onChange }: {
  application: TutorApplication
  onChange: (a: TutorApplication) => void
}) {
  const copy = COPY[application.status]
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [now] = useState(() => Date.now()) // read the clock once, when the page opens
  const reapplyFrom = application.reapply_available_from
  const canReapply = reapplyFrom !== null && new Date(reapplyFrom).getTime() <= now

  async function reapply() {
    setBusy(true)
    setError(null)
    try {
      onChange(await tutorApi.reapply())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }
  const submitted = application.submitted_at ? formatDate(application.submitted_at) : null

  return (
    <div className="space-y-6">
      <div role="status" className={`rounded-xl border p-6 ${copy?.tone ?? 'border-slate-200'}`}>
        <p className="font-display text-2xl font-semibold text-heading">{copy?.title ?? application.status_label}</p>
        <p className="mt-2 leading-relaxed text-slate-700">{copy?.body}</p>
        {submitted && <p className="mt-3 text-sm text-slate-500">Submitted on {submitted}</p>}
        {application.status === 'approved' && (
          <Link to="/tutor/profile" className="mt-4 inline-block rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand">
            Edit your profile
          </Link>
        )}
        {application.reviewer_message && (
          <div className="mt-4 rounded-lg bg-surface/70 p-4">
            <p className="text-sm font-medium text-slate-500">Note from the Brights team</p>
            <p className="mt-1 whitespace-pre-line text-slate-800">{application.reviewer_message}</p>
          </div>
        )}
        {reapplyFrom && (
          <div className="mt-4">
            {canReapply ? (
              <button type="button" onClick={reapply} disabled={busy}
                className="rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand disabled:opacity-60">
                {busy ? 'Starting…' : 'Start a new application'}
              </button>
            ) : (
              <p className="text-slate-700">You can apply again from <strong>{formatDate(reapplyFrom)}</strong>.</p>
            )}
            <div className="mt-3"><FormAlert message={error} /></div>
          </div>
        )}
      </div>
      <ApplicationSummary application={application} />
    </div>
  )
}
