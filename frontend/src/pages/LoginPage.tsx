import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router'
import { ApiError } from '../api/client'
import type { User } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import { FormAlert, PasswordField, SubmitButton, TextField } from '../components/Form'
import { afterLogin } from '../lib/home'
import { AuthCard } from './AuthCard'

export function LoginPage() {
  const { login, loginWithCode } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  // Set when the user was sent here from a page that needs login; they go back there.
  const returnTo = (location.state as { from?: string } | null)?.from
  // Set by the Django admin's sign-in link (a page outside the app), e.g. ?next=/<admin>/
  const next = params.get('next')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [challenge, setChallenge] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function finish(user: User) {
    if (next && next.startsWith('/') && !next.startsWith('//')) {
      window.location.assign(next) // full page load: the admin isn't part of the app
      return
    }
    navigate(afterLogin(user, returnTo), { replace: true })
  }

  async function sendPassword() {
    const result = await login(email, password)
    if ('code_required' in result) {
      setChallenge(result.challenge)
      setCode('')
      return
    }
    finish(result)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      if (challenge) finish(await loginWithCode(challenge, code))
      else await sendPassword()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function sendNewCode() {
    setBusy(true)
    setError(null)
    try {
      await sendPassword()
      setNotice('We sent a new code. Only the newest code works.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (challenge) {
    return (
      <AuthCard title="Check your email" subtitle={<>We sent a 6-digit sign-in code to <strong className="[overflow-wrap:anywhere]">{email}</strong>.</>}>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <FormAlert message={error} />
          {notice && <p role="status" className="rounded-lg bg-brand-soft/10 p-3 text-sm text-pass">{notice}</p>}
          <TextField label="Sign-in code" name="code" inputMode="numeric" autoComplete="one-time-code" maxLength={7}
            pattern="[0-9 ]*" required autoFocus value={code} onChange={(e) => setCode(e.target.value)}
            hint="It works once, for 10 minutes. Staff accounts need this every time they log in." />
          <SubmitButton busy={busy}>Log in</SubmitButton>
          <div className="flex flex-wrap justify-between gap-2 text-sm">
            <button type="button" disabled={busy} onClick={sendNewCode} className="font-medium text-link hover:underline disabled:opacity-50">
              Send a new code
            </button>
            <button type="button" onClick={() => { setChallenge(null); setPassword(''); setError(null); setNotice(null) }}
              className="font-medium text-slate-600 hover:underline">
              Use a different account
            </button>
          </div>
        </form>
      </AuthCard>
    )
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle={<>New to Brights? <Link to="/register" className="font-medium text-link hover:underline">Create an account</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <FormAlert message={error} />
        <TextField label="Email" name="email" type="email" autoComplete="email" required
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <PasswordField label="Password" name="password" autoComplete="current-password" required
          value={password} onChange={(e) => setPassword(e.target.value)} />
        <SubmitButton busy={busy}>Log in</SubmitButton>
        <p className="text-center text-sm">
          <Link to="/forgot-password" className="font-medium text-link hover:underline">Forgot your password?</Link>
        </p>
      </form>
    </AuthCard>
  )
}
