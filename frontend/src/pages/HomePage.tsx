import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext'

export function HomePage() {
  const { user } = useAuth()
  return (
    <section className="mx-auto max-w-3xl px-4 py-16 text-center sm:py-24">
      <img src="/brights-logo.png" alt="" className="mx-auto h-24 w-24" />
      <h1 className="mt-6 text-4xl font-bold tracking-tight text-brand-navy sm:text-5xl">
        Find a verified tutor who gets it.
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
        Brights connects Grade 8–12 learners and their parents with tutors whose results and
        qualifications we check by hand.
      </p>
      <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
        {user ? (
          <Link to="/dashboard" className="rounded-lg bg-brand-navy px-6 py-3 font-semibold text-white hover:bg-brand-blue">
            Go to your dashboard
          </Link>
        ) : (
          <>
            <Link to="/register" className="rounded-lg bg-brand-navy px-6 py-3 font-semibold text-white hover:bg-brand-blue">
              Create a free account
            </Link>
            <Link to="/login" className="rounded-lg border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50">
              Log in
            </Link>
          </>
        )}
      </div>
      <div className="mx-auto mt-12 h-1.5 max-w-xs rounded-full bg-gradient-to-r from-brand-navy via-brand-teal to-brand-orange" />
    </section>
  )
}
