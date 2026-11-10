import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../../api/client'
import { reportApi, type ReportAction, type ReportDetail } from '../../api/staff'
import { formatDate } from '../../lib/staffFormat'
import { ReportCard } from './ReportsPage'
import { Card, ErrorList, StatusPill } from './StaffUi'

const DONE: Record<ReportAction, string> = {
  dismiss: 'Report dismissed',
  warn: 'Warning sent to the tutor',
  suspend: 'Tutor suspended',
}

/** /staff/reports/:id — read the report and its context, then dismiss, warn or suspend. */
export function ReportReviewPage() {
  const id = Number(useParams().id)
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loadError, setLoadError] = useState('')
  const [done, setDone] = useState('')

  useEffect(() => {
    reportApi.get(id).then((r) => { setReport(r); setDone('') })
      .catch((e) => setLoadError(e instanceof ApiError && e.status === 404 ? 'This report doesn’t exist.' : 'Could not load the report.'))
  }, [id])

  return (
    <section className="mx-auto max-w-6xl px-4 py-6 sm:py-8">
      <Link to="/staff/reports" className="text-sm font-medium text-link hover:underline">← All reports</Link>
      <div className="mt-4">
        {loadError && <ErrorList messages={[loadError]} />}
        {!report && !loadError && <p className="text-slate-500">Loading…</p>}
        {report && (
          <>
            <header className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  {report.is_urgent && report.status === 'open' && (
                    <span className="rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-white">Urgent</span>
                  )}
                  <span className="text-sm text-slate-500">Report #{report.id}</span>
                </div>
                <h1 className="mt-1 text-2xl font-bold text-heading sm:text-3xl">{report.category_label}</h1>
                <p className="mt-1 text-slate-600">About {report.tutor.name} · sent {formatDate(report.created_at, true)}</p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${report.status === 'open' ? 'bg-brand-sun/25 text-heading' : 'bg-slate-100 text-slate-700'}`}>
                {report.status === 'open' ? 'Open' : `Closed: ${report.outcome_label}`}
              </span>
            </header>

            {done && (
              <div role="status" className="mt-6 rounded-xl border border-brand-soft/50 bg-brand-soft/10 p-4 text-sm text-pass">
                <strong>{done}.</strong> {report.reporter ? 'The reporter has been told the review is finished.' : ''}
              </div>
            )}

            {report.category === 'child_safety' && report.status === 'open' && (
              <div className="mt-6 rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800">
                <strong>If a child may be in danger right now,</strong> call SAPS on 10111 and Childline on 116 before anything else.
                {report.holds_tutor
                  ? ' The tutor is hidden from search until this report is closed.'
                  : ' The tutor is still visible: this reporter never contacted them through Brights.'}
              </div>
            )}

            <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] lg:items-start">
              <div className="space-y-6">
                <Card title="What was reported">
                  <p className="whitespace-pre-line text-slate-800">{report.description}</p>
                  <p className="mt-3 text-sm text-slate-500">
                    {report.incident_date ? `Happened on ${formatDate(report.incident_date)}` : 'No date given'}
                  </p>
                </Card>
                <ContextCard report={report} />
                {report.other_reports.length > 0 && (
                  <Card title={`Other reports about ${report.tutor.name} (${report.other_reports.length})`}>
                    <ul className="space-y-3">{report.other_reports.map((r) => <li key={r.id}><ReportCard row={r} /></li>)}</ul>
                  </Card>
                )}
              </div>
              <div className="space-y-6">
                <DecisionCard key={`${report.status}-${report.admin_notes.length}`} report={report}
                  onDone={(updated, action) => { setReport(updated); setDone(DONE[action]); window.scrollTo({ top: 0, behavior: 'smooth' }) }} />
                {report.admin_notes && (
                  <Card title="Internal notes">
                    <p className="whitespace-pre-line text-sm text-slate-700">{report.admin_notes}</p>
                    {report.closed_by && <p className="mt-2 text-xs text-slate-500">Closed {formatDate(report.closed_at, true)} by {report.closed_by}</p>}
                  </Card>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  )
}

function ContextCard({ report }: { report: ReportDetail }) {
  const { tutor, reporter } = report
  return (
    <Card title="Who's involved">
      <dl className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-4 gap-y-2 text-sm">
        <dt className="text-slate-500">Tutor</dt>
        <dd className="text-slate-900">
          {tutor.name}<br /><span className="[overflow-wrap:anywhere] text-slate-500">{tutor.email}</span>
        </dd>
        <dt className="text-slate-500">Tutor status</dt>
        <dd className="flex flex-wrap items-center gap-2">
          {tutor.application_status && tutor.application_status_label && <StatusPill status={tutor.application_status} label={tutor.application_status_label} />}
          {!tutor.accepting_learners && <span className="text-slate-600">Paused by the tutor</span>}
        </dd>
        <dt className="text-slate-500">Reported by</dt>
        <dd className="text-slate-900">
          {reporter ? <>{reporter.name} ({reporter.account_type})<br /><span className="[overflow-wrap:anywhere] text-slate-500">{reporter.email}</span></> : 'A deleted account'}
          {report.reporter_was_minor && <p className="mt-1 font-semibold text-red-700">The reporter is under 18.</p>}
        </dd>
        <dt className="text-slate-500">Contact</dt>
        <dd className="text-slate-900">
          {report.contacts.length === 0 ? 'Never contacted this tutor through Brights.' : (
            <ul className="space-y-0.5">
              {report.contacts.map((c, i) => <li key={i}>{c.subject}{c.grade ? `, Grade ${c.grade}` : ''} · {formatDate(c.created_at)}</li>)}
            </ul>
          )}
        </dd>
      </dl>
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm font-medium">
        {tutor.application_id && <Link to={`/staff/applications/${tutor.application_id}`} className="text-link hover:underline">Tutor's application →</Link>}
        {tutor.application_status === 'approved' && <Link to={`/tutors/${tutor.profile_id}`} className="text-link hover:underline">Public profile →</Link>}
      </div>
    </Card>
  )
}

function DecisionCard({ report, onDone }: { report: ReportDetail; onDone: (r: ReportDetail, a: ReportAction) => void }) {
  const [notes, setNotes] = useState('')
  const [message, setMessage] = useState('')
  const [confirming, setConfirming] = useState<ReportAction | null>(null)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  if (report.actions.length === 0) {
    return report.is_own ? (
      <Card title="Decision"><p className="text-sm text-slate-600">This report is about you, so another team member has to handle it.</p></Card>
    ) : null
  }

  async function run(action: ReportAction) {
    setBusy(true)
    setErrors([])
    try {
      const updated = await reportApi.decide(report.id, { action, message, notes })
      onDone(updated, action)
    } catch (e) {
      setErrors(e instanceof ApiError ? (e.fieldErrors.non_field_errors ?? [e.message]) : ['Something went wrong. Please try again.'])
    } finally {
      setConfirming(null)
      setBusy(false)
    }
  }

  const confirmText: Record<ReportAction, string> = {
    dismiss: 'Close this report with no action against the tutor?',
    warn: `Email ${report.tutor.name} your warning and close this report?`,
    suspend: `Suspend ${report.tutor.name}? They disappear from search straight away and get your message by email.`,
  }
  const field = 'mt-1 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20'

  return (
    <Card title="Decision">
      <p className="text-sm text-slate-600">Closing the report emails the reporter that it was reviewed. They're never told what action was taken.</p>
      <label htmlFor="report-notes" className="mt-4 block text-sm font-medium text-slate-700">Internal note (only the team sees this; needed to dismiss)</label>
      <textarea id="report-notes" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} className={field}
        placeholder="What you checked and why you decided this" />
      <label htmlFor="report-message" className="mt-4 block text-sm font-medium text-slate-700">Message to the tutor (needed to warn or suspend)</label>
      <textarea id="report-message" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} className={field}
        placeholder="e.g. Please only communicate with learners through their parents and in group chats." />

      <div className="mt-4"><ErrorList messages={errors} /></div>

      {confirming ? (
        <div role="alertdialog" aria-label="Confirm" className={`mt-4 rounded-xl border p-4 ${confirming === 'suspend' ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-chalk'}`}>
          <p className="text-sm text-slate-800">{confirmText[confirming]}</p>
          <div className="mt-3 flex flex-wrap gap-3">
            <button type="button" disabled={busy} onClick={() => run(confirming)}
              className={`rounded-full px-5 py-2 font-semibold text-white disabled:opacity-50 ${confirming === 'suspend' ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-deep hover:bg-brand'}`}>
              {busy ? 'Saving…' : `Yes, ${confirming === 'dismiss' ? 'dismiss' : confirming === 'warn' ? 'send warning' : 'suspend'}`}
            </button>
            <button type="button" disabled={busy} onClick={() => setConfirming(null)} className="rounded-full border border-slate-300 px-5 py-2 font-semibold text-slate-700">Cancel</button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" onClick={() => setConfirming('dismiss')} className="rounded-full border border-slate-300 px-5 py-2.5 font-semibold text-slate-800 hover:border-brand">Dismiss</button>
          <button type="button" onClick={() => setConfirming('warn')} className="rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand">Warn tutor</button>
          <button type="button" onClick={() => setConfirming('suspend')} className="rounded-full border border-red-300 px-5 py-2.5 font-semibold text-red-700 hover:bg-red-50">Suspend tutor</button>
        </div>
      )}
    </Card>
  )
}
