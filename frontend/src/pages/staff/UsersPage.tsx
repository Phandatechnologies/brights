import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ApiError } from '../../api/client'
import { userApi, type Page, type UserRow } from '../../api/staff'
import { formatDate } from '../../lib/staffFormat'
import { ErrorList } from './StaffUi'

const FILTERS = [
  ['all', 'Everyone'],
  ['learner', 'Learners'],
  ['parent', 'Parents'],
  ['tutor', 'Tutors'],
  ['staff', 'Brights team'],
  ['blocked', 'Blocked'],
  ['unconfirmed', 'Email not confirmed'],
] as const

export function Badge({ children, tone = 'grey' }: { children: React.ReactNode; tone?: 'grey' | 'red' | 'amber' }) {
  const tones = { grey: 'bg-slate-100 text-slate-700', red: 'bg-red-50 text-red-800', amber: 'bg-brand-sun/25 text-heading' }
  return <span className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ${tones[tone]}`}>{children}</span>
}

/** /staff/users — find any account. Newest first. */
export function UsersPage() {
  const [params, setParams] = useSearchParams()
  const type = params.get('type') ?? 'all'
  const q = params.get('q') ?? ''
  const page = Number(params.get('page') ?? '1')
  const [data, setData] = useState<Page<UserRow> | null>(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(q)

  useEffect(() => {
    let cancelled = false
    userApi.list({ type, q, page })
      .then((d) => { if (!cancelled) { setData(d); setError('') } })
      .catch((e) => { if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load accounts.') })
    return () => { cancelled = true }
  }, [type, q, page])

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) merged.set(key, value)
      else merged.delete(key)
    }
    if (!('page' in next)) merged.delete('page')
    setParams(merged)
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    update({ q: search.trim() })
  }

  const pages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
      <Link to="/staff/more" className="text-sm font-medium text-link hover:underline">← More</Link>
      <h1 className="mt-4 text-3xl font-bold text-heading">Users</h1>
      <p className="mt-1 text-slate-600">Every account on Brights, newest first.</p>

      <div className="mt-6 -mx-4 overflow-x-auto px-4 pb-1">
        <div role="tablist" aria-label="Show" className="flex w-max gap-2">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" role="tab" aria-selected={type === value} onClick={() => update({ type: value })}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${type === value
                ? 'border-brand-deep bg-brand-deep text-white' : 'border-slate-300 bg-surface text-slate-700 hover:border-brand'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={submit} role="search" className="mt-4 flex gap-2">
        <label htmlFor="user-q" className="sr-only">Search by name or email</label>
        <input id="user-q" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
        <button className="rounded-lg bg-brand-deep px-4 font-semibold text-white hover:bg-brand">Search</button>
      </form>

      <div className="mt-6">
        {error && <ErrorList messages={[error]} />}
        {!data && !error && <p className="text-slate-500">Loading…</p>}
        {data && data.results.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-600">{q ? `No accounts match “${q}”.` : 'Nothing here.'}</div>
        )}
        {data && data.results.length > 0 && (
          <>
            <p className="mb-3 text-sm text-slate-500">{data.count === 1 ? '1 account' : `${data.count} accounts`}</p>
            <ul className="space-y-3">
              {data.results.map((u) => (
                <li key={u.id}>
                  <Link to={`/staff/users/${u.id}`}
                    className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-surface p-4 shadow-sm transition hover:border-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900">{u.name}</p>
                      <p className="truncate text-sm text-slate-500">{u.email}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                      <Badge>{u.account_type_label}</Badge>
                      {u.is_minor && <Badge tone="amber">Under 18</Badge>}
                      {!u.email_verified && <Badge tone="amber">Email not confirmed</Badge>}
                      {!u.is_active && <Badge tone="red">Blocked</Badge>}
                      <span className="text-sm text-slate-500">Joined {formatDate(u.date_joined)}</span>
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
