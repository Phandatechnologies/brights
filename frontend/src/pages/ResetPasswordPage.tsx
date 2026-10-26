import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { authApi } from '../api/auth'
import { ApiError, type FieldErrors } from '../api/client'
import { FormAlert, PasswordField, SubmitButton } from '../components/Form'
import { AuthCard } from './AuthCard'

/** /reset-password?uid=…&token=… — choose a new password from the emailed link. */
export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [done, setDone] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setErrors({})
    if (password !== confirm) return setErrors({ confirm: ["The passwords don't match."] })
    setBusy(true)
    try {
      await authApi.confirmPasswordReset(params.get('uid') ?? '', params.get('token') ?? '', password)
      setDone(true)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.fieldErrors.new_password ? null : err.message)
        setErrors(err.fieldErrors)
      } else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard title="Choose a new password" subtitle="Use at least 8 characters that aren't easy to guess.">
      {done ? (
        <div role="status" className="space-y-4">
          <p className="text-slate-700">Your password has been changed, and you've been logged out on other devices.</p>
          <Link to="/login" className="inline-block rounded-full bg-brand-deep px-6 py-3 font-semibold text-white hover:bg-brand">Log in</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4" noValidate>
          <FormAlert message={error} />
          {error && <p className="text-sm"><Link to="/forgot-password" className="font-medium text-link hover:underline">Request a new link</Link></p>}
          <PasswordField label="New password" name="new_password" autoComplete="new-password" value={password}
            errors={errors.new_password} onChange={(e) => setPassword(e.target.value)} />
          <PasswordField label="Confirm new password" name="confirm" autoComplete="new-password" value={confirm}
            errors={errors.confirm} onChange={(e) => setConfirm(e.target.value)} />
          <SubmitButton busy={busy}>Change password</SubmitButton>
        </form>
      )}
    </AuthCard>
  )
}
