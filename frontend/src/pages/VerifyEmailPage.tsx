import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'

type State = { kind: 'checking' } | { kind: 'done' } | { kind: 'failed'; message: string }

/** /verify-email?uid=…&token=… — opened from the link in the verification email. */
export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const { user, refresh } = useAuth()
  const [state, setState] = useState<State>({ kind: 'checking' })
  const uid = params.get('uid') ?? ''
  const token = params.get('token') ?? ''

  useEffect(() => {
    let cancelled = false
    authApi.verifyEmail(uid, token)
      .then(async () => { await refresh(); if (!cancelled) setState({ kind: 'done' }) })
      .catch((err) => {
        if (!cancelled) setState({ kind: 'failed', message: err instanceof ApiError ? err.message : 'Something went wrong.' })
      })
    return () => { cancelled = true }
  }, [uid, token, refresh])

  return (
    <section className="mx-auto max-w-lg px-4 py-16 text-center">
      {state.kind === 'checking' && <p className="text-slate-600">Confirming your email…</p>}
      {state.kind === 'done' && (
        <>
          <h1 className="text-3xl font-bold text-heading">Email confirmed</h1>
          <p className="mt-3 text-slate-700">Thanks! Your account is fully set up.</p>
          <Link to={user ? '/dashboard' : '/login'} className="mt-6 inline-block rounded-full bg-brand-navy px-6 py-3 font-semibold text-white hover:bg-brand-blue">
            {user ? 'Go to your dashboard' : 'Log in'}
          </Link>
        </>
      )}
      {state.kind === 'failed' && (
        <>
          <h1 className="text-3xl font-bold text-heading">We couldn't confirm your email</h1>
          <p className="mt-3 text-slate-700">{state.message}</p>
          <p className="mt-2 text-slate-600">Log in and use “Send a new link” on your dashboard.</p>
          <Link to="/dashboard" className="mt-6 inline-block font-medium text-link hover:underline">Go to your dashboard</Link>
        </>
      )}
    </section>
  )
}
