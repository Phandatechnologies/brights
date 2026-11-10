import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ApiError } from '../../api/client'
import { staffApi, type ApplicationRow, type Page } from '../../api/staff'
import { daysLabel, formatDate } from '../../lib/staffFormat'
import { ErrorList, StatusPill } from './StaffUi'

const FILTERS = [
  ['pending', 'To review'],
  ['more_info', 'Waiting on tutor'],
  ['approved', 'Approved'],
  ['rejected', 'Rejected'],
  ['suspended', 'Suspended'],
  ['draft', 'Not sent yet'],
  ['all', 'All'],
] as const

/** /staff/applications — the review queue. Filters live in the URL so the back button keeps them. */
export function ApplicationsPage() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? 'pending'
  const q = params.get('q') ?? ''
  const page = Number(params.get('page') ?? '1')
  const [data, setData] = useState<Page<ApplicationRow> | null>(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(q)

  useEffect(() => {
    let cancelled = false
    staffApi.applications({ status, q, page })
      .then((d) => { if (!cancelled) { setData(d); setError('') } })
      .catch((e) => { if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load applications.') })
    return () => { cancelled = true }
  }, [status, q, page])

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) merged.set(key, value)
      else merged.delete(key)
    }
    if (!('page' in next)) merged.delete('page')
    setParams(merged)
  }

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    update({ q: search.trim() })
  }

  const pages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Tutor applications</h1>
      <p className="mt-1 text-slate-600">{status === 'pending' ? 'Oldest first, so everyone waits about the same time.' : 'Most recently changed first.'}</p>

      <div className="mt-6 -mx-4 overflow-x-auto px-4 pb-1">
        <div role="tablist" aria-label="Show" className="flex w-max gap-2">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" role="tab" aria-selected={status === value} onClick={() => update({ status: value })}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${status === value
                ? 'border-brand-deep bg-brand-deep text-white' : 'border-slate-300 bg-surface text-slate-700 hover:border-brand'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={submitSearch} role="search" className="mt-4 flex gap-2">
        <label htmlFor="staff-q" className="sr-only">Search by name or email</label>
        <input id="staff-q" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
        <button className="rounded-lg bg-brand-deep px-4 font-semibold text-white hover:bg-brand">Search</button>
      </form>

      <div className="mt-6">
        {error && <ErrorList messages={[error]} />}
        {!data && !error && <p className="text-slate-500">Loading…</p>}
        {data && data.results.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            {q ? `No applications match “${q}”.` : status === 'pending' ? 'Nothing to review. All caught up! 🎉' : 'Nothing here.'}
          </div>
        )}
        {data && data.results.length > 0 && (
          <>
            <p className="mb-3 text-sm text-slate-500">{data.count === 1 ? '1 application' : `${data.count} applications`}</p>
            <ul className="space-y-3">
              {data.results.map((row) => (
                <li key={row.id}>
                  <Link to={`/staff/applications/${row.id}`}
                    className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-surface p-4 shadow-sm transition hover:border-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900">{row.name}</p>
                      <p className="truncate text-sm text-slate-500">{row.email}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {row.pathway === 'teacher' ? 'Qualified teacher' : 'Matric results'} · {row.subject_count === 1 ? '1 subject' : `${row.subject_count} subjects`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 sm:flex-col sm:items-end">
                      <StatusPill status={row.status} label={row.status_label} />
                      <span className="text-sm text-slate-500">
                        {row.days_waiting !== null ? `Waiting ${daysLabel(row.days_waiting)}` : `Updated ${formatDate(row.updated_at)}`}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
            {pages > 1 && (
              <nav aria-label="Pages" className="mt-6 flex items-center justify-between">
                <button type="button" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">Previous</button>
                <span className="text-sm text-slate-600">Page {page} of {pages}</span>
                <button type="button" disabled={page >= pages} onClick={() => update({ page: String(page + 1) })}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">Next</button>
              </nav>
            )}
          </>
        )}
      </div>
    </section>
  )
}
