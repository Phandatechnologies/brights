import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ApiError } from '../../api/client'
import { reportApi, type Page, type ReportRow } from '../../api/staff'
import { daysLabel, formatDate } from '../../lib/staffFormat'
import { ErrorList } from './StaffUi'

const FILTERS = [
  ['open', 'Open'],
  ['closed', 'Closed'],
  ['all', 'All'],
] as const

/** /staff/reports — safety reports about tutors. Open ones: urgent first, then oldest. */
export function ReportsPage() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? 'open'
  const page = Number(params.get('page') ?? '1')
  const [data, setData] = useState<Page<ReportRow> | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    reportApi.list(status, page)
      .then((d) => { if (!cancelled) { setData(d); setError('') } })
      .catch((e) => { if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load reports.') })
    return () => { cancelled = true }
  }, [status, page])

  const pages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Safety reports</h1>
      <p className="mt-1 text-slate-600">Reports are never shown to the tutor. Urgent child-safety reports come first.</p>

      <div role="tablist" aria-label="Show" className="mt-6 flex flex-wrap gap-2">
        {FILTERS.map(([value, label]) => (
          <button key={value} type="button" role="tab" aria-selected={status === value} onClick={() => setParams({ status: value })}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${status === value
              ? 'border-brand-deep bg-brand-deep text-white' : 'border-slate-300 bg-surface text-slate-700 hover:border-brand'}`}>
            {label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {error && <ErrorList messages={[error]} />}
        {!data && !error && <p className="text-slate-500">Loading…</p>}
        {data && data.results.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            {status === 'open' ? 'No open reports.' : 'Nothing here.'}
          </div>
        )}
        {data && data.results.length > 0 && (
          <>
            <ul className="space-y-3">{data.results.map((row) => <li key={row.id}><ReportCard row={row} /></li>)}</ul>
            {pages > 1 && (
              <nav aria-label="Pages" className="mt-6 flex items-center justify-between">
                <button type="button" disabled={page <= 1} onClick={() => setParams({ status, page: String(page - 1) })}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">Previous</button>
                <span className="text-sm text-slate-600">Page {page} of {pages}</span>
                <button type="button" disabled={page >= pages} onClick={() => setParams({ status, page: String(page + 1) })}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">Next</button>
              </nav>
            )}
          </>
        )}
      </div>
    </section>
  )
}

export function ReportCard({ row }: { row: ReportRow }) {
  const urgentOpen = row.is_urgent && row.status === 'open'
  return (
    <Link to={`/staff/reports/${row.id}`}
      className={`flex flex-col gap-2 rounded-2xl border p-4 shadow-sm transition focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30 sm:flex-row sm:items-center sm:justify-between ${urgentOpen
        ? 'border-red-400 bg-red-50 hover:border-red-600' : 'border-slate-200 bg-surface hover:border-brand'}`}>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          {urgentOpen && <span className="rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-white">Urgent</span>}
          <p className="font-semibold text-slate-900">{row.category_label}</p>
        </div>
        <p className="mt-1 text-sm text-slate-600">About <strong className="font-semibold">{row.tutor_name}</strong> · from {row.reporter_name}</p>
      </div>
      <p className="text-sm text-slate-600 sm:text-right">
        {row.status === 'open'
          ? <>Open {row.days_open !== null && daysLabel(row.days_open)}{row.holds_tutor && <><br className="hidden sm:block" /><span className="sm:hidden"> · </span>Tutor hidden</>}</>
          : <>{row.outcome_label}<br className="hidden sm:block" /><span className="sm:hidden"> · </span>{formatDate(row.closed_at)}</>}
      </p>
    </Link>
  )
}
