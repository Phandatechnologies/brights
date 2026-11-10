import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { staffApi, type StaffOverview } from '../../api/staff'
import { useAuth } from '../../auth/AuthContext'
import { daysLabel } from '../../lib/staffFormat'
import { Card, ErrorList } from './StaffUi'

/** /staff — what needs the team's attention today. */
export function StaffHomePage() {
  const { user } = useAuth()
  const [data, setData] = useState<StaffOverview | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    staffApi.overview().then(setData).catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load the overview.'))
  }, [])

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Hi {user?.first_name} 👋</h1>
      <p className="mt-1 text-slate-600">Here's what needs the Brights team.</p>
      {error && <div className="mt-6"><ErrorList messages={[error]} /></div>}
      {!data && !error && <p className="mt-8 text-slate-500">Loading…</p>}
      {data && (
        <>
          <h2 className="mt-8 text-sm font-semibold uppercase tracking-wide text-slate-500">Needs attention</h2>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <TaskCard to="/staff/applications" count={data.applications_pending} title="Applications to review"
              note={data.oldest_pending_days !== null ? `Oldest has waited ${daysLabel(data.oldest_pending_days)}` : 'All caught up'} />
            <TaskCard to="/staff/applications?status=more_info" count={data.applications_more_info} title="Waiting on the tutor"
              note="We asked these tutors for more information" quiet />
            <TaskCard count={data.photos_waiting} title="Profile photos to approve"
              note="Still in the Django admin until the next update" quiet />
          </div>

          <h2 className="mt-10 text-sm font-semibold uppercase tracking-wide text-slate-500">On Brights</h2>
          <Card className="mt-3">
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Total label="Learners" value={data.totals.learners} />
              <Total label="Parents" value={data.totals.parents} />
              <Total label="Tutor accounts" value={data.totals.tutors} />
              <Total label="Approved tutors" value={data.totals.approved_tutors} />
            </dl>
          </Card>
          <p className="mt-6 text-sm text-slate-500">
            Subjects, areas and staff accounts are still managed in the Django admin.
          </p>
        </>
      )}
    </section>
  )
}

function TaskCard({ to, count, title, note, quiet = false }: { to?: string; count: number; title: string; note: string; quiet?: boolean }) {
  const urgent = !quiet && count > 0
  const body = (
    <>
      <p className={`text-4xl font-bold tabular-nums ${urgent ? 'text-heading' : 'text-slate-700'}`}>{count}</p>
      <p className="mt-1 font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{note}</p>
    </>
  )
  const style = `block rounded-2xl border p-5 shadow-sm transition ${urgent ? 'border-brand-sun bg-brand-sun/10' : 'border-slate-200 bg-surface'}`
  return to ? (
    <Link to={to} className={`${style} hover:border-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30`}>{body}</Link>
  ) : (
    <div className={style}>{body}</div>
  )
}

function Total({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="text-2xl font-bold tabular-nums text-slate-900">{value}</dd>
    </div>
  )
}
