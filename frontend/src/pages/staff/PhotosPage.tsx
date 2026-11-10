import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { ApiError } from '../../api/client'
import { photoApi, type Page, type PhotoRow } from '../../api/staff'
import { formatDate } from '../../lib/staffFormat'
import { ErrorList } from './StaffUi'

const FILTERS = [
  ['pending', 'To approve'],
  ['rejected', 'Rejected'],
  ['approved', 'Approved'],
] as const

/** Quick reasons, so rejecting a photo on a phone is two taps. Staff can edit them. */
const QUICK_REASONS = [
  ['Face not clear', 'Please use a photo where your face is clearly visible.'],
  ['Other people in it', 'Please use a photo of just you, with no one else in it.'],
  ['Blurry or dark', 'This photo is too blurry or dark. Please upload a clearer one.'],
  ['Not a real photo', 'Please use a real photo of yourself, not a logo, cartoon or picture of something else.'],
] as const

/** /staff/photos — approve or reject tutors' profile photos. Tutors can't be listed until approved. */
export function PhotosPage() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? 'pending'
  const [data, setData] = useState<Page<PhotoRow> | null>(null)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let cancelled = false
    photoApi.list(status)
      .then((d) => { if (!cancelled) { setData(d); setError('') } })
      .catch((e) => { if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load photos.') })
    return () => { cancelled = true }
  }, [status, reload])

  return (
    <section className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Profile photos</h1>
      <p className="mt-1 text-slate-600">
        Approve a photo when it clearly shows the tutor's face and nothing inappropriate. If you reject it, the tutor sees your reason.
      </p>

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
            {status === 'pending' ? 'No photos waiting. All caught up! 🎉' : 'Nothing here.'}
          </div>
        )}
        {data && data.results.length > 0 && (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.results.map((row) => (
              <PhotoCard key={`${row.id}-${row.version}`} row={row} reviewing={status === 'pending'} onChanged={() => setReload((n) => n + 1)} />
            ))}
          </ul>
        )}
        {data && data.count > data.results.length && (
          <p className="mt-4 text-sm text-slate-500">Showing {data.results.length} of {data.count}. Finish these to see the rest.</p>
        )}
      </div>
    </section>
  )
}

function PhotoCard({ row, reviewing, onChanged }: { row: PhotoRow; reviewing: boolean; onChanged: () => void }) {
  const [rejecting, setRejecting] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])
  const [done, setDone] = useState<'approved' | 'rejected' | null>(null)
  const [broken, setBroken] = useState(false)

  async function decide(action: 'approve' | 'reject') {
    setBusy(true)
    setErrors([])
    try {
      await photoApi.decide(row.id, { action, version: row.version, note })
      setDone(action === 'approve' ? 'approved' : 'rejected')
    } catch (e) {
      setErrors(e instanceof ApiError ? (e.fieldErrors.non_field_errors ?? [e.message]) : ['Something went wrong. Please try again.'])
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-surface shadow-sm">
      <div className="aspect-square bg-chalk">
        {row.photo_url && !broken ? (
          <img src={row.photo_url} alt={`Profile photo uploaded by ${row.name}`} className="h-full w-full object-cover" onError={() => setBroken(true)} />
        ) : (
          <div className="flex h-full items-center justify-center p-6 text-center text-sm text-slate-600">
            This photo has changed or was removed.{' '}
            <button type="button" onClick={onChanged} className="ml-1 font-medium text-link hover:underline">Reload</button>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <p className="font-semibold text-slate-900">{row.name}</p>
        <p className="truncate text-sm text-slate-500">{row.email}</p>
        <p className="mt-1 text-xs text-slate-500">Uploaded {formatDate(row.updated_at, true)}</p>
        {row.photo_status === 'rejected' && row.photo_note && <p className="mt-2 text-sm text-slate-600">Reason given: “{row.photo_note}”</p>}

        {done && (
          <p role="status" className={`mt-3 rounded-lg p-2 text-sm font-semibold ${done === 'approved' ? 'bg-brand-soft/15 text-pass' : 'bg-red-50 text-red-800'}`}>
            {done === 'approved' ? '✓ Approved' : '✕ Rejected. The tutor will see your reason.'}
          </p>
        )}

        {reviewing && !done && !broken && (
          <div className="mt-auto pt-4">
            <div className="mb-3"><ErrorList messages={errors} /></div>
            {rejecting ? (
              <div>
                <label htmlFor={`reason-${row.id}`} className="block text-sm font-medium text-slate-700">Reason the tutor will see</label>
                <textarea id={`reason-${row.id}`} rows={3} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" />
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {QUICK_REASONS.map(([label, reason]) => (
                    <button key={label} type="button" onClick={() => setNote(reason)}
                      className="rounded-full border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:border-brand">
                      {label}
                    </button>
                  ))}
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <button type="button" disabled={busy} onClick={() => decide('reject')}
                    className="rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50">
                    {busy ? 'Saving…' : 'Reject photo'}
                  </button>
                  <button type="button" disabled={busy} onClick={() => { setRejecting(false); setErrors([]) }}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <button type="button" disabled={busy} onClick={() => decide('approve')}
                  className="rounded-lg bg-brand-deep px-3 py-2 text-sm font-semibold text-white hover:bg-brand disabled:opacity-50">
                  {busy ? 'Saving…' : '✓ Approve'}
                </button>
                <button type="button" disabled={busy} onClick={() => setRejecting(true)}
                  className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                  ✕ Reject
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </li>
  )
}
