import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { contactApi, type ContactHistoryItem } from '../api/contact'
import { useAuth } from '../auth/AuthContext'

/** /my-tutors — learners and parents: tutors they've contacted through Brights. */
export function MyTutorsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<ContactHistoryItem[] | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    contactApi.history()
      .then((data) => { if (!cancelled) setItems(data) })
      .catch(() => { if (!cancelled) { setItems([]); setFailed(true) } })
    return () => { cancelled = true }
  }, [])

  return (
    <section className="mx-auto max-w-3xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">My tutors</h1>
      <p className="mt-1 text-slate-600">
        {user?.account_type === 'parent' ? 'Tutors you’ve contacted for your child.' : 'Tutors you’ve contacted through Brights.'}
      </p>

      {items === null && <p className="mt-8 text-slate-500">Loading…</p>}
      {failed && <p className="mt-8 text-red-700">Couldn’t load your tutors. Check your connection and try again.</p>}

      {items && items.length === 0 && !failed && (
        <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-surface p-8 text-center">
          <p className="font-semibold text-slate-900">No tutors yet</p>
          <p className="mt-1 text-slate-600">When you contact a tutor on WhatsApp, they’ll appear here so you can find them again.</p>
          <Link to="/tutors" className="mt-5 inline-block rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand">
            Find a tutor
          </Link>
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="mt-6 divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-surface shadow-sm">
          {items.map((item) => (
            <li key={item.tutor_id} className="flex items-center justify-between gap-3 px-5 py-4">
              <div className="min-w-0">
                {item.available ? (
                  <Link to={`/tutors/${item.tutor_id}`} className="block truncate font-semibold text-link hover:underline">{item.name}</Link>
                ) : (
                  <span className="block truncate text-slate-500">{item.name} <span className="text-sm">(not available right now)</span></span>
                )}
                <span className="text-sm text-slate-500">
                  Last contacted {new Date(item.last_contacted).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' })}
                </span>
              </div>
              <Link to={`/tutors/${item.tutor_id}/report`} state={{ tutorName: item.name }}
                className="shrink-0 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-700">
                Report
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
