import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../../api/client'
import { userApi, type UserAction, type UserDetail } from '../../api/staff'
import { formatDate } from '../../lib/staffFormat'
import { Card, ErrorList, StatusPill } from './StaffUi'
import { Badge } from './UsersPage'

const DONE: Record<UserAction, string> = {
  block: 'Login blocked. They can’t log in, and any open sessions have stopped working.',
  unblock: 'Login unblocked. They can log in again.',
  resend_confirmation: 'A new confirmation link has been emailed.',
}

/** /staff/users/:id — one account: details, activity, and block / unblock / resend. */
export function UserPage() {
  const id = Number(useParams().id)
  const [user, setUser] = useState<UserDetail | null>(null)
  const [loadError, setLoadError] = useState('')
  const [done, setDone] = useState('')

  useEffect(() => {
    userApi.get(id).then((u) => { setUser(u); setDone('') })
      .catch((e) => setLoadError(e instanceof ApiError && e.status === 404 ? 'This account doesn’t exist.' : 'Could not load the account.'))
  }, [id])

  return (
    <section className="mx-auto max-w-5xl px-4 py-6 sm:py-8">
      <Link to="/staff/users" className="text-sm font-medium text-link hover:underline">← All users</Link>
      <div className="mt-4">
        {loadError && <ErrorList messages={[loadError]} />}
        {!user && !loadError && <p className="text-slate-500">Loading…</p>}
        {user && (
          <>
            <header>
              <h1 className="text-3xl font-bold text-heading">{user.name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge>{user.account_type_label}</Badge>
                {user.is_minor && <Badge tone="amber">Under 18</Badge>}
                {!user.email_verified && <Badge tone="amber">Email not confirmed</Badge>}
                {!user.is_active && <Badge tone="red">Blocked</Badge>}
              </div>
            </header>
            {done && <div role="status" className="mt-6 rounded-xl border border-brand-soft/50 bg-brand-soft/10 p-4 text-sm text-pass">{done}</div>}

            <div className="mt-6 grid gap-6 lg:grid-cols-2 lg:items-start">
              <div className="space-y-6">
                <Card title="Details">
                  <dl className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-4 gap-y-2 text-sm">
                    <dt className="text-slate-500">Email</dt><dd className="[overflow-wrap:anywhere] text-slate-900">{user.email}</dd>
                    <dt className="text-slate-500">Born</dt><dd className="text-slate-900">{formatDate(user.date_of_birth)} (age {user.age})</dd>
                    <dt className="text-slate-500">Joined</dt><dd className="text-slate-900">{formatDate(user.date_joined, true)}</dd>
                    <dt className="text-slate-500">Last login</dt><dd className="text-slate-900">{user.last_login ? formatDate(user.last_login, true) : 'Never'}</dd>
                  </dl>
                </Card>
                {user.tutor && (
                  <Card title="As a tutor">
                    <dl className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-4 gap-y-2 text-sm">
                      <dt className="text-slate-500">Application</dt>
                      <dd>{user.tutor.application_status && user.tutor.application_status_label
                        ? <StatusPill status={user.tutor.application_status} label={user.tutor.application_status_label} /> : <span className="text-slate-900">Not started</span>}</dd>
                      <dt className="text-slate-500">Photo</dt><dd className="text-slate-900">{user.tutor.photo_status ?? '—'}</dd>
                      <dt className="text-slate-500">In search</dt><dd className="text-slate-900">{user.tutor.is_listed ? 'Yes, listed' : 'No'}</dd>
                    </dl>
                    <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm font-medium">
                      {user.tutor.application_id && <Link to={`/staff/applications/${user.tutor.application_id}`} className="text-link hover:underline">Application →</Link>}
                      {user.tutor.is_listed && user.tutor.profile_id && <Link to={`/tutors/${user.tutor.profile_id}`} className="text-link hover:underline">Public profile →</Link>}
                    </div>
                  </Card>
                )}
                <Card title="Activity">
                  <dl className="grid grid-cols-3 gap-4 text-center">
                    <div><dt className="text-xs text-slate-500">Tutors contacted</dt><dd className="text-2xl font-bold tabular-nums text-slate-900">{user.contacts_made}</dd></div>
                    <div><dt className="text-xs text-slate-500">Reports made</dt><dd className="text-2xl font-bold tabular-nums text-slate-900">{user.reports_made}</dd></div>
                    <div><dt className="text-xs text-slate-500">Reports about them</dt><dd className="text-2xl font-bold tabular-nums text-slate-900">{user.reports_about}</dd></div>
                  </dl>
                </Card>
              </div>
              <div className="space-y-6">
                <ActionsCard user={user} onDone={(u, action) => { setUser(u); setDone(DONE[action]) }} />
                <Card title="Team history">
                  {user.history.length === 0 ? <p className="text-sm text-slate-500">No team actions on this account yet.</p> : (
                    <ol className="space-y-3">
                      {user.history.map((h, i) => (
                        <li key={i} className="border-l-2 border-slate-200 pl-4">
                          <p className="text-sm text-slate-900">{h.what}</p>
                          <p className="text-xs text-slate-500">{formatDate(h.when, true)}{h.by && <> · {h.by}</>}</p>
                        </li>
                      ))}
                    </ol>
                  )}
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  )
}

function ActionsCard({ user, onDone }: { user: UserDetail; onDone: (u: UserDetail, a: UserAction) => void }) {
  const [reason, setReason] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  if (user.actions.length === 0) {
    return (
      <Card title="Actions">
        <p className="text-sm text-slate-600">
          {user.is_self ? 'This is your own account. Change it from the Account page.' : 'Only the account owner can change another team member’s account.'}
        </p>
      </Card>
    )
  }

  async function run(action: UserAction) {
    setBusy(true)
    setErrors([])
    try {
      onDone(await userApi.act(user.id, action, reason), action)
      setReason('')
    } catch (e) {
      setErrors(e instanceof ApiError ? (e.fieldErrors.non_field_errors ?? [e.message]) : ['Something went wrong. Please try again.'])
    } finally {
      setConfirming(false)
      setBusy(false)
    }
  }

  const canBlock = user.actions.includes('block')
  return (
    <Card title="Actions">
      <div className="mb-3"><ErrorList messages={errors} /></div>
      {canBlock && (
        <>
          <p className="text-sm text-slate-600">
            Blocking stops {user.first_name} logging in straight away{user.tutor ? ' and removes them from search' : ''}. Nothing is deleted; you can unblock later.
          </p>
          <label htmlFor="block-reason" className="mt-3 block text-sm font-medium text-slate-700">Why (only the team sees this)</label>
          <textarea id="block-reason" rows={2} value={reason} onChange={(e) => setReason(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
          {confirming ? (
            <div role="alertdialog" aria-label="Confirm" className="mt-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <p className="text-sm text-slate-800">Block {user.name}'s login?</p>
              <div className="mt-3 flex flex-wrap gap-3">
                <button type="button" disabled={busy} onClick={() => run('block')} className="rounded-full bg-red-600 px-5 py-2 font-semibold text-white hover:bg-red-700 disabled:opacity-50">
                  {busy ? 'Saving…' : 'Yes, block'}
                </button>
                <button type="button" disabled={busy} onClick={() => setConfirming(false)} className="rounded-full border border-slate-300 px-5 py-2 font-semibold text-slate-700">Cancel</button>
              </div>
            </div>
          ) : (
            <button type="button" onClick={() => setConfirming(true)}
              className="mt-3 rounded-full border border-red-300 px-5 py-2.5 font-semibold text-red-700 hover:bg-red-50">Block login</button>
          )}
        </>
      )}
      {user.actions.includes('unblock') && (
        <>
          <p className="text-sm text-slate-600">{user.first_name}'s login is blocked. Unblocking lets them log in again.</p>
          <button type="button" disabled={busy} onClick={() => run('unblock')}
            className="mt-3 rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand disabled:opacity-50">Unblock login</button>
        </>
      )}
      {user.actions.includes('resend_confirmation') && (
        <div className={canBlock || user.actions.includes('unblock') ? 'mt-5 border-t border-slate-200 pt-5' : ''}>
          <p className="text-sm text-slate-600">{user.first_name} hasn't confirmed their email address yet.</p>
          <button type="button" disabled={busy} onClick={() => run('resend_confirmation')}
            className="mt-3 rounded-full border border-slate-300 px-5 py-2.5 font-semibold text-slate-800 hover:border-brand disabled:opacity-50">
            Email a new confirmation link
          </button>
        </div>
      )}
    </Card>
  )
}
