import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'
import { FormAlert, SubmitButton, TextField } from '../components/Form'
import { AuthCard } from './AuthCard'

/** /forgot-password — ask for a reset link. */
export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await authApi.requestPasswordReset(email)
      setSent(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard title="Reset your password" subtitle={<Link to="/login" className="font-medium text-brand-blue hover:underline">Back to log in</Link>}>
      {sent ? (
        <p role="status" className="leading-relaxed text-slate-700">
          If an account exists for <strong>{email}</strong>, we've emailed a link to reset your password. It works for 3 days.
          Check your spam folder if you don't see it.
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-4" noValidate>
          <FormAlert message={error} />
          <p className="text-slate-600">Enter the email you signed up with and we'll send you a link.</p>
          <TextField label="Email" name="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <SubmitButton busy={busy}>Send reset link</SubmitButton>
        </form>
      )}
    </AuthCard>
  )
}
