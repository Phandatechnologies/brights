import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { FormAlert, PasswordField, SubmitButton, TextField } from '../components/Form'
import { homeFor } from '../lib/home'
import { AuthCard } from './AuthCard'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // Set when the user was sent here from a page that needs login; they go back there.
  const returnTo = (location.state as { from?: string } | null)?.from

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const user = await login(email, password)
      navigate(returnTo ?? homeFor(user), { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
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
