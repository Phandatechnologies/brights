import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { profilesApi, type Area, type Province, type SearchPage as SearchResult } from '../api/profiles'
import { tutorApi, type Subject } from '../api/tutor'
import { SearchSelect } from '../components/SearchSelect'
import { TutorCard } from '../components/TutorCard'
import { GRADES } from '../lib/tutorRules'

const FILTER_KEYS = ['subject', 'grade', 'mode', 'province', 'area', 'min_price', 'max_price', 'sort'] as const

type Loaded = { key: string; data: SearchResult } | { key: string; error: string }

const selectClass =
  'w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20'

/** /tutors — public tutor search. Filters live in the URL so searches can be shared. */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [provinces, setProvinces] = useState<Province[]>([])
  const [areas, setAreas] = useState<Area[]>([])
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  // Filters start open on large screens and collapsed on phones, so results are visible first.
  const [filtersOpen, setFiltersOpen] = useState(() => window.matchMedia('(min-width: 1024px)').matches)

  const key = params.toString()
  const page = Number(params.get('page') ?? '1')

  useEffect(() => {
    tutorApi.subjects().then(setSubjects).catch(() => setSubjects([]))
    profilesApi.areas().then((r) => { setProvinces(r.provinces); setAreas(r.areas) }).catch(() => {})
  }, [])

  useEffect(() => {
    let cancelled = false
    profilesApi.search(new URLSearchParams(key))
      .then((data) => { if (!cancelled) setLoaded({ key, data }) })
      .catch(() => { if (!cancelled) setLoaded({ key, error: 'Could not load tutors. Please try again.' }) })
    return () => { cancelled = true }
  }, [key])

  const loading = loaded?.key !== key
  const province = params.get('province') ?? ''
  const areaOptions = useMemo(() => areas.filter((a) => !province || a.province === province), [areas, province])

  function setFilter(name: (typeof FILTER_KEYS)[number], value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    if (name === 'province') next.delete('area') // an old area may not belong to the new province
    next.delete('page')
    setParams(next, { replace: true })
  }

  function goToPage(n: number) {
    const next = new URLSearchParams(params)
    if (n > 1) next.set('page', String(n))
    else next.delete('page')
    setParams(next)
    window.scrollTo({ top: 0 })
  }

  const hasFilters = FILTER_KEYS.some((k) => k !== 'sort' && params.get(k))
  const result = loaded && 'data' in loaded ? loaded.data : null
  const totalPages = result ? Math.max(1, Math.ceil(result.count / 12)) : 1

  return (
    <section className="mx-auto max-w-6xl px-4 py-10 sm:py-14">
      <h1 className="text-3xl font-bold tracking-[-0.02em] text-heading sm:text-4xl">Find a tutor</h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Every tutor here has been checked by our team. Online tutors can teach you from anywhere in South Africa.
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-[17rem_1fr]">
        <aside aria-label="Filters" className="lg:sticky lg:top-24 lg:self-start">
          <details className="rounded-xl border border-slate-200 bg-surface p-4" open={filtersOpen}
            onToggle={(e) => setFiltersOpen(e.currentTarget.open)}>
            <summary className="flex cursor-pointer list-none items-center justify-between font-semibold text-heading">
              <span>Filters{hasFilters && <span className="ml-2 rounded-full bg-brand-navy px-2 py-0.5 text-xs text-white">On</span>}</span>
              <span className="text-sm font-normal text-slate-500">{filtersOpen ? 'Hide' : 'Show'}</span>
            </summary>
            <div className="mt-4 space-y-4">
              <Field label="Subject" id="f-subject">
                <SearchSelect id="f-subject" emptyLabel="Any subject" value={params.get('subject') ?? ''}
                  options={subjects.map((s) => ({ value: String(s.id), label: s.name }))}
                  onChange={(v) => setFilter('subject', v)} />
              </Field>
              <Field label="Grade" id="f-grade">
                <select id="f-grade" className={selectClass} value={params.get('grade') ?? ''} onChange={(e) => setFilter('grade', e.target.value)}>
                  <option value="">Any grade</option>
                  {GRADES.map((g) => <option key={g} value={g}>Grade {g}</option>)}
                </select>
              </Field>
              <fieldset>
                <legend className="mb-1 text-sm font-medium text-slate-700">Lessons</legend>
                <div className="grid grid-cols-3 overflow-hidden rounded-lg border border-slate-300 text-sm">
                  {[['', 'Any'], ['online', 'Online'], ['in_person', 'In person']].map(([value, label]) => {
                    const active = (params.get('mode') ?? '') === value
                    return (
                      <button key={value} type="button" aria-pressed={active} onClick={() => setFilter('mode', value)}
                        className={`px-2 py-2 font-medium transition ${active ? 'bg-brand-navy text-white' : 'bg-surface text-slate-700 hover:bg-slate-50'}`}>
                        {label}
                      </button>
                    )
                  })}
                </div>
              </fieldset>
              <Field label="Province" id="f-province">
                <select id="f-province" className={selectClass} value={province} onChange={(e) => setFilter('province', e.target.value)}>
                  <option value="">Any province</option>
                  {provinces.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </Field>
              <Field label="Area" id="f-area">
                <SearchSelect id="f-area" emptyLabel="Any area" value={params.get('area') ?? ''}
                  options={areaOptions.map((a) => ({ value: String(a.id), label: a.name }))}
                  onChange={(v) => setFilter('area', v)} />
              </Field>
              <fieldset>
                <legend className="mb-1 text-sm font-medium text-slate-700">Price per hour (R)</legend>
                <div className="flex items-center gap-2">
                  <PriceInput label="Minimum price" value={params.get('min_price') ?? ''} onCommit={(v) => setFilter('min_price', v)} placeholder="Min" />
                  <span className="text-slate-400">to</span>
                  <PriceInput label="Maximum price" value={params.get('max_price') ?? ''} onCommit={(v) => setFilter('max_price', v)} placeholder="Max" />
                </div>
              </fieldset>
              {hasFilters && (
                <button type="button" onClick={() => setParams(new URLSearchParams(), { replace: true })}
                  className="text-sm font-medium text-link hover:underline">
                  Clear filters
                </button>
              )}
            </div>
          </details>
        </aside>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-slate-600" aria-live="polite">
              {loading ? 'Searching…' : result ? `${result.count} tutor${result.count === 1 ? '' : 's'} found` : ''}
            </p>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              Sort by
              <select className="rounded-lg border border-slate-300 bg-surface px-2 py-1.5 text-slate-900" value={params.get('sort') ?? ''}
                onChange={(e) => setFilter('sort', e.target.value)}>
                <option value="">Newest</option>
                <option value="price_low">Price: low to high</option>
                <option value="price_high">Price: high to low</option>
              </select>
            </label>
          </div>

          {loaded && 'error' in loaded && <p role="alert" className="mt-6 text-red-700">{loaded.error}</p>}

          {result && result.results.length === 0 && !loading && (
            <div className="mt-6 rounded-xl border border-dashed border-slate-300 p-10 text-center">
              <p className="font-semibold text-heading">No tutors match these filters yet</p>
              <p className="mt-1 text-slate-600">Try another area, include online lessons, or widen the price range.</p>
            </div>
          )}

          <ul className={`mt-6 grid gap-4 sm:grid-cols-2 transition ${loading ? 'opacity-50' : ''}`}>
            {result?.results.map((tutor) => (
              <li key={tutor.id}>
                <TutorCard tutor={tutor} />
              </li>
            ))}
          </ul>

          {result && totalPages > 1 && (
            <nav aria-label="Pages" className="mt-8 flex items-center justify-between">
              <button type="button" disabled={page <= 1} onClick={() => goToPage(page - 1)}
                className="rounded-lg px-4 py-2 font-medium text-heading hover:bg-slate-100 disabled:opacity-40">Previous</button>
              <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
              <button type="button" disabled={page >= totalPages} onClick={() => goToPage(page + 1)}
                className="rounded-lg px-4 py-2 font-medium text-heading hover:bg-slate-100 disabled:opacity-40">Next</button>
            </nav>
          )}
        </div>
      </div>
    </section>
  )
}

function Field({ label, id, children }: { label: string; id: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  )
}

/** Applies the price when the person leaves the box or presses Enter, not on every keystroke. */
function PriceInput({ label, value, onCommit, placeholder }: {
  label: string; value: string; onCommit: (v: string) => void; placeholder: string
}) {
  const [draft, setDraft] = useState(value)
  const [lastValue, setLastValue] = useState(value)
  if (value !== lastValue) { setLastValue(value); setDraft(value) } // follow "Clear filters"
  return (
    <input aria-label={label} inputMode="numeric" placeholder={placeholder} value={draft}
      onChange={(e) => setDraft(e.target.value.replace(/[^0-9]/g, '').slice(0, 5))}
      onBlur={() => draft !== value && onCommit(draft)}
      onKeyDown={(e) => { if (e.key === 'Enter') onCommit(draft) }}
      className="w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 tabular-nums outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
  )
}
