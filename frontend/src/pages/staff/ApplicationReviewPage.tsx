import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../../api/client'
import {
  staffApi, type ApplicationDetail, type ReviewAction, type ReviewDocument, type ReviewSubject, type SubjectDecision,
} from '../../api/staff'
import { gradeRange } from '../../lib/format'
import { daysLabel, formatDate } from '../../lib/staffFormat'
import { Card, ErrorList, StatusPill } from './StaffUi'

type Choice = { decision: SubjectDecision; note: string }

const ACTION_DONE: Record<ReviewAction, string> = {
  approve: 'Approved',
  request_info: 'Asked for more information',
  reject: 'Rejected',
  suspend: 'Suspended',
  reinstate: 'Reinstated',
}

const HISTORY_LABELS: Record<string, string> = {
  submitted: 'Sent for review',
  approved: 'Approved',
  requested_info: 'Asked for more information',
  rejected: 'Rejected',
  suspended: 'Suspended',
  reinstated: 'Reinstated',
  reapplied: 'Started a new application',
}

/** /staff/applications/:id — check the documents, decide each subject, then approve, ask for more, or reject. */
export function ApplicationReviewPage() {
  const id = Number(useParams().id)
  const [app, setApp] = useState<ApplicationDetail | null>(null)
  const [loadError, setLoadError] = useState('')
  const [done, setDone] = useState('')

  useEffect(() => {
    staffApi.application(id).then(setApp)
      .catch((e) => setLoadError(e instanceof ApiError && e.status === 404 ? 'This application doesn’t exist.' : 'Could not load the application.'))
  }, [id])

  if (loadError) return <Shell><ErrorList messages={[loadError]} /></Shell>
  if (!app) return <Shell><p className="text-slate-500">Loading…</p></Shell>

  return (
    <Shell>
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-heading">{app.name}</h1>
          <p className="mt-1 text-slate-600">
            {app.pathway === 'teacher' ? 'Qualified teacher' : 'Academic tutor (Matric results)'}
            {app.days_waiting !== null && <> · waiting {daysLabel(app.days_waiting)}</>}
          </p>
        </div>
        <StatusPill status={app.status} label={app.status_label} />
      </header>

      {done && (
        <div role="status" className="mt-6 rounded-xl border border-brand-soft/50 bg-brand-soft/10 p-4 text-sm text-pass">
          <strong>{done}.</strong> {app.first_name} has been emailed.
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)] lg:items-start">
        <div className="space-y-6">
          <ApplicantCard app={app} />
          <DocumentsCard app={app} />
        </div>
        <div className="space-y-6">
          <DecisionCard key={`${app.status}-${app.history.length}`} app={app}
            onDone={(updated, action) => { setApp(updated); setDone(ACTION_DONE[action]); window.scrollTo({ top: 0, behavior: 'smooth' }) }} />
          <HistoryCard app={app} />
        </div>
      </div>
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-6xl px-4 py-6 sm:py-8">
      <Link to="/staff/applications" className="text-sm font-medium text-link hover:underline">← All applications</Link>
      <div className="mt-4">{children}</div>
    </section>
  )
}

function ApplicantCard({ app }: { app: ApplicationDetail }) {
  return (
    <Card title="Applicant">
      <dl className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-4 gap-y-2 text-sm">
        <dt className="text-slate-500">Email</dt>
        <dd className="[overflow-wrap:anywhere] text-slate-900">
          {app.email} {app.email_verified ? <span className="text-pass">(confirmed)</span> : <span className="text-[#b54708]">(not confirmed)</span>}
        </dd>
        <dt className="text-slate-500">Born</dt>
        <dd className="text-slate-900">{formatDate(app.date_of_birth)} (age {app.age})</dd>
        {app.pathway === 'teacher' && (
          <>
            <dt className="text-slate-500">Qualification</dt><dd className="text-slate-900">{app.qualification_name || '—'}</dd>
            <dt className="text-slate-500">SACE number</dt><dd className="text-slate-900">{app.sace_number || '—'}</dd>
          </>
        )}
        <dt className="text-slate-500">Sent</dt><dd className="text-slate-900">{formatDate(app.submitted_at, true)}</dd>
        {app.reviewed_at && (
          <>
            <dt className="text-slate-500">Last decision</dt>
            <dd className="text-slate-900">{formatDate(app.reviewed_at, true)}{app.reviewed_by && <> by {app.reviewed_by}</>}</dd>
          </>
        )}
        {!app.is_active && (
          <>
            <dt className="text-slate-500">Login</dt><dd className="font-semibold text-red-700">Blocked</dd>
          </>
        )}
      </dl>
      {app.reviewer_message && (
        <div className="mt-4 rounded-xl bg-chalk p-3 text-sm">
          <p className="font-medium text-slate-700">Message the tutor can see</p>
          <p className="mt-1 whitespace-pre-line text-slate-600">{app.reviewer_message}</p>
        </div>
      )}
      {app.status === 'approved' && app.profile_id && (
        <Link to={`/tutors/${app.profile_id}`} className="mt-4 inline-block text-sm font-medium text-link hover:underline">See their public profile →</Link>
      )}
    </Card>
  )
}

function DocumentsCard({ app }: { app: ApplicationDetail }) {
  return (
    <Card title="Documents">
      {!app.can_view_documents ? (
        <p className="text-sm text-slate-600">Your staff account can't open verification documents. Ask the account owner for document access.</p>
      ) : app.documents.length === 0 ? (
        <p className="text-sm text-slate-600">No documents uploaded.</p>
      ) : (
        <>
          <p className="mb-3 text-sm text-slate-500">Check the name, ID details and every mark against these.</p>
          <ul className="space-y-3">{app.documents.map((doc) => <DocumentRow key={doc.id} doc={doc} />)}</ul>
        </>
      )}
    </Card>
  )
}

function DocumentRow({ doc }: { doc: ReviewDocument }) {
  const isImage = doc.content_type.startsWith('image/')
  const kb = Math.max(1, Math.round(doc.size / 1024))
  return (
    <li className="rounded-xl border border-slate-200 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium text-slate-900">{doc.kind_label}</p>
          <p className="truncate text-sm text-slate-500">{doc.name} · {kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`}</p>
        </div>
        {doc.url && (
          <div className="flex shrink-0 gap-2 text-sm font-medium">
            <a href={`${doc.url}?inline=1`} target="_blank" rel="noopener" className="rounded-lg bg-brand-deep px-3 py-1.5 text-white hover:bg-brand">Open</a>
            <a href={doc.url} className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 hover:border-brand">Download</a>
          </div>
        )}
      </div>
      {isImage && doc.url && (
        <a href={`${doc.url}?inline=1`} target="_blank" rel="noopener" className="mt-3 block">
          <img src={`${doc.url}?inline=1`} alt={`${doc.kind_label} preview`} loading="lazy"
            className="max-h-64 w-full rounded-lg border border-slate-200 bg-chalk object-contain" />
        </a>
      )}
    </li>
  )
}

/** Per-subject decisions plus the buttons. Only the actions the server allows are shown. */
function DecisionCard({ app, onDone }: { app: ApplicationDetail; onDone: (updated: ApplicationDetail, action: ReviewAction) => void }) {
  const deciding = app.actions.includes('approve')
  const [choices, setChoices] = useState<Record<number, Choice>>(() => Object.fromEntries(app.subjects.map((s) => [s.id, initialChoice(s, app.min_mark)])))
  const [message, setMessage] = useState('')
  const [confirming, setConfirming] = useState<ReviewAction | null>(null)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  async function run(action: ReviewAction) {
    setBusy(true)
    setErrors([])
    try {
      const decisions = action === 'approve'
        ? app.subjects.map((s) => ({ id: s.id, decision: choices[s.id].decision, note: choices[s.id].note }))
        : undefined
      const updated = await staffApi.decide(app.id, { action, message, decisions })
      setConfirming(null)
      onDone(updated, action)
    } catch (e) {
      setConfirming(null)
      setErrors(e instanceof ApiError ? (e.fieldErrors.non_field_errors ?? [e.message]) : ['Something went wrong. Please try again.'])
    } finally {
      setBusy(false)
    }
  }

  const approvedCount = app.subjects.filter((s) => choices[s.id]?.decision === 'approved').length

  return (
    <Card title={deciding ? 'Your decision' : 'Subjects'}>
      <ul className="divide-y divide-slate-200">
        {app.subjects.map((s) => (
          <SubjectRow key={s.id} subject={s} minMark={app.min_mark} pathway={app.pathway} editable={deciding}
            choice={choices[s.id]} onChange={(c) => setChoices((prev) => ({ ...prev, [s.id]: c }))} />
        ))}
      </ul>

      {app.is_own && <p className="mt-4 rounded-xl bg-chalk p-3 text-sm text-slate-600">This is your own application, so another team member has to review it.</p>}

      {app.actions.length > 0 && (
        <div className="mt-5 border-t border-slate-200 pt-5">
          <label htmlFor="review-message" className="block text-sm font-medium text-slate-700">
            Message to {app.first_name} {deciding ? '(needed to ask for more information or reject)' : '(they will see this)'}
          </label>
          <textarea id="review-message" rows={4} value={message} onChange={(e) => setMessage(e.target.value)}
            placeholder={deciding ? 'e.g. Your ID copy is blurry. Please upload a clearer photo of it.' : app.actions.includes('suspend') ? 'Why the tutor is suspended' : 'Optional note to the tutor'}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />

          <div className="mt-4"><ErrorList messages={errors} /></div>

          {confirming ? (
            <Confirm action={confirming} name={app.first_name} approvedCount={approvedCount} busy={busy}
              onYes={() => run(confirming)} onNo={() => setConfirming(null)} />
          ) : (
            <div className="mt-4 flex flex-wrap gap-3">
              {app.actions.includes('approve') && (
                <button type="button" disabled={busy} onClick={() => setConfirming('approve')}
                  className="rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand disabled:opacity-50">
                  Approve {approvedCount > 0 && `(${approvedCount} ${approvedCount === 1 ? 'subject' : 'subjects'})`}
                </button>
              )}
              {app.actions.includes('request_info') && (
                <button type="button" disabled={busy} onClick={() => run('request_info')}
                  className="rounded-full border border-slate-300 px-5 py-2.5 font-semibold text-slate-800 hover:border-brand disabled:opacity-50">
                  Ask for more information
                </button>
              )}
              {app.actions.includes('reject') && (
                <button type="button" disabled={busy} onClick={() => setConfirming('reject')}
                  className="rounded-full border border-red-300 px-5 py-2.5 font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                  Reject
                </button>
              )}
              {app.actions.includes('suspend') && (
                <button type="button" disabled={busy} onClick={() => setConfirming('suspend')}
                  className="rounded-full border border-red-300 px-5 py-2.5 font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                  Suspend tutor
                </button>
              )}
              {app.actions.includes('reinstate') && (
                <button type="button" disabled={busy} onClick={() => setConfirming('reinstate')}
                  className="rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand disabled:opacity-50">
                  Reinstate tutor
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

function initialChoice(s: ReviewSubject, minMark: number): Choice {
  if (s.decision !== 'pending') return { decision: s.decision, note: s.decision_note }
  // A mark under the minimum can't be approved, so start it as declined with the reason filled in.
  if (s.below_minimum) return { decision: 'declined', note: `Matric mark is below ${minMark}%.` }
  return { decision: 'pending', note: '' }
}

function SubjectRow({ subject, minMark, pathway, editable, choice, onChange }: {
  subject: ReviewSubject; minMark: number; pathway: string; editable: boolean; choice: Choice; onChange: (c: Choice) => void
}) {
  const shown = editable ? choice : { decision: subject.decision, note: subject.decision_note }
  return (
    <li className="py-4 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-semibold text-slate-900">{subject.subject}</p>
        <p className="text-sm text-slate-500">{gradeRange(subject.grades)}</p>
      </div>
      {pathway === 'academic' && (
        <p className={`mt-1 text-sm ${subject.below_minimum ? 'font-semibold text-red-700' : 'text-slate-600'}`}>
          Matric mark: <span className="tabular-nums">{subject.matric_mark ?? '—'}%</span>
          {subject.below_minimum && ` (below the ${minMark}% minimum)`}
        </p>
      )}
      {editable ? (
        <>
          <div role="group" aria-label={`Decision for ${subject.subject}`} className="mt-3 grid grid-cols-2 gap-2">
            <button type="button" aria-pressed={choice.decision === 'approved'} disabled={subject.below_minimum}
              onClick={() => onChange({ decision: 'approved', note: '' })}
              className={`rounded-lg border px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${choice.decision === 'approved'
                ? 'border-brand-deep bg-brand-deep text-white' : 'border-slate-300 text-slate-700 hover:border-brand'}`}>
              ✓ Approve
            </button>
            <button type="button" aria-pressed={choice.decision === 'declined'}
              onClick={() => onChange({ decision: 'declined', note: choice.note })}
              className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${choice.decision === 'declined'
                ? 'border-red-600 bg-red-600 text-white' : 'border-slate-300 text-slate-700 hover:border-red-400'}`}>
              ✕ Decline
            </button>
          </div>
          {choice.decision === 'declined' && (
            <>
              <label htmlFor={`note-${subject.id}`} className="sr-only">Reason for declining {subject.subject}</label>
              <input id={`note-${subject.id}`} value={choice.note} maxLength={300} onChange={(e) => onChange({ ...choice, note: e.target.value })}
                placeholder="Reason the tutor will see (required)"
                className="mt-2 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
            </>
          )}
        </>
      ) : (
        shown.decision !== 'pending' && (
          <p className={`mt-2 text-sm font-medium ${shown.decision === 'approved' ? 'text-pass' : 'text-red-700'}`}>
            {shown.decision === 'approved' ? '✓ Approved' : `✕ Declined${shown.note ? `: ${shown.note}` : ''}`}
          </p>
        )
      )}
    </li>
  )
}

function Confirm({ action, name, approvedCount, busy, onYes, onNo }: {
  action: ReviewAction; name: string; approvedCount: number; busy: boolean; onYes: () => void; onNo: () => void
}) {
  const text: Partial<Record<ReviewAction, string>> = {
    approve: `Approve ${name} for ${approvedCount} ${approvedCount === 1 ? 'subject' : 'subjects'}? They'll be emailed and can start taking learners once their profile is complete.`,
    reject: `Reject ${name}'s application? They'll be emailed your message and can apply again after 30 days.`,
    suspend: `Suspend ${name}? They disappear from search straight away and are emailed your message.`,
    reinstate: `Reinstate ${name}? They'll show in search again if their profile is complete.`,
  }
  const danger = action === 'reject' || action === 'suspend'
  return (
    <div role="alertdialog" aria-label="Confirm" className={`mt-4 rounded-xl border p-4 ${danger ? 'border-red-200 bg-red-50' : 'border-brand-soft/50 bg-brand-soft/10'}`}>
      <p className="text-sm text-slate-800">{text[action]}</p>
      <div className="mt-3 flex flex-wrap gap-3">
        <button type="button" disabled={busy} onClick={onYes}
          className={`rounded-full px-5 py-2 font-semibold text-white disabled:opacity-50 ${danger ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-deep hover:bg-brand'}`}>
          {busy ? 'Saving…' : 'Yes, ' + (action === 'approve' ? 'approve' : action === 'reject' ? 'reject' : action === 'suspend' ? 'suspend' : 'reinstate')}
        </button>
        <button type="button" disabled={busy} onClick={onNo} className="rounded-full border border-slate-300 px-5 py-2 font-semibold text-slate-700">Cancel</button>
      </div>
    </div>
  )
}

function HistoryCard({ app }: { app: ApplicationDetail }) {
  return (
    <Card title="History">
      {app.history.length === 0 ? <p className="text-sm text-slate-500">Nothing yet.</p> : (
        <ol className="space-y-4">
          {app.history.map((event, i) => (
            <li key={i} className="border-l-2 border-slate-200 pl-4">
              <p className="text-sm font-semibold text-slate-900">{HISTORY_LABELS[event.action] ?? event.action}</p>
              <p className="text-xs text-slate-500">{formatDate(event.created_at, true)}{event.actor && <> · {event.actor}</>}</p>
              {event.note && <p className="mt-1 whitespace-pre-line text-sm text-slate-600">“{event.note}”</p>}
              {event.details.length > 0 && (
                <ul className="mt-1 text-sm text-slate-600">
                  {event.details.map((d) => (
                    <li key={d.subject}>{d.decision === 'approved' ? '✓' : '✕'} {d.subject}{d.note && ` (${d.note})`}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
