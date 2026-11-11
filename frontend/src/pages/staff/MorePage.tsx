import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { staffApi } from '../../api/staff'

/** /staff/more — the staff sections that don't fit in the bottom bar. */
export function MorePage() {
  const [adminUrl, setAdminUrl] = useState<string | null>(null)
  useEffect(() => { staffApi.overview().then((o) => setAdminUrl(o.django_admin_url)).catch(() => {}) }, [])

  const item = 'block rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm transition hover:border-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30'
  return (
    <section className="mx-auto max-w-3xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">More</h1>
      <ul className="mt-6 space-y-3">
        <li><Link to="/staff/users" className={item}>
          <p className="font-semibold text-slate-900">Users</p>
          <p className="mt-1 text-sm text-slate-600">Find any account. Block or unblock login, or resend the email confirmation link.</p>
        </Link></li>
        <li><Link to="/staff/videos" className={item}>
          <p className="font-semibold text-slate-900">How-to videos</p>
          <p className="mt-1 text-sm text-slate-600">Add, publish and order the YouTube videos on every tutor's Home.</p>
        </Link></li>
        <li><Link to="/account" className={item}>
          <p className="font-semibold text-slate-900">Your account</p>
          <p className="mt-1 text-sm text-slate-600">Change your password, appearance (light or dark), or log out.</p>
        </Link></li>
        {adminUrl && (
          <li><a href={adminUrl} className={item}>
            <p className="font-semibold text-slate-900">Django admin</p>
            <p className="mt-1 text-sm text-slate-600">For the rare jobs not in the staff area yet: subjects, areas and team accounts.</p>
          </a></li>
        )}
      </ul>
    </section>
  )
}
