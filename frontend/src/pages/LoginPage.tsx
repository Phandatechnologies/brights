import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { FormAlert, SubmitButton, TextField } from '../components/Form'
import { AuthCard } from './AuthCard'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const returnTo = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
      navigate(returnTo, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle={<>New to Brights? <Link to="/register" className="font-medium text-brand-blue hover:underline">Create an account</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <FormAlert message={error} />
        <TextField label="Email" name="email" type="email" autoComplete="email" required
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Password" name="password" type="password" autoComplete="current-password" required
          value={password} onChange={(e) => setPassword(e.target.value)} />
        <SubmitButton busy={busy}>Log in</SubmitButton>
      </form>
    </AuthCard>
  )
}
