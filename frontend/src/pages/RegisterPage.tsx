import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import type { AccountType, RegisterInput } from '../api/auth'
import { ApiError, type FieldErrors } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { FieldError, FormAlert, SubmitButton, TextField } from '../components/Form'
import { ADULT_AGE, MIN_LEARNER_AGE, ageFromIsoDate } from '../lib/age'
import { AuthCard } from './AuthCard'

const ACCOUNT_TYPES: { value: AccountType; title: string; description: string }[] = [
  { value: 'learner', title: 'Learner', description: "I'm in Grade 8–12 and looking for a tutor" },
  { value: 'parent', title: 'Parent or guardian', description: "I'm finding a tutor for my child" },
  { value: 'tutor', title: 'Tutor', description: "I'm 18+ and want to tutor learners" },
]

/** Latest selectable birth date (today), computed once when the page module loads. */
const TODAY_ISO = new Date().toISOString().slice(0, 10)

const EMPTY: RegisterInput = {
  email: '', password: '', first_name: '', last_name: '', date_of_birth: '',
  account_type: 'learner', guardian_consent: false, guardian_name: '',
}

/** Friendly early warnings while typing. The server re-checks everything on submit. */
function ageWarning(type: AccountType, age: number | null): string | null {
  if (age === null || age < 0) return null
  if (type === 'tutor' && age < ADULT_AGE) return 'You must be at least 18 to register as a tutor.'
  if (type === 'parent' && age < ADULT_AGE) return 'You must be at least 18 to register as a parent or guardian.'
  if (type === 'learner' && age < MIN_LEARNER_AGE) return `Learners must be at least ${MIN_LEARNER_AGE} years old.`
  return null
}

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<RegisterInput>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const age = ageFromIsoDate(form.date_of_birth)
  const needsGuardian = form.account_type === 'learner' && age !== null && age >= MIN_LEARNER_AGE && age < ADULT_AGE
  const warning = ageWarning(form.account_type, age)

  function update<K extends keyof RegisterInput>(key: K, value: RegisterInput[K]) {
    setForm((current) => ({ ...current, [key]: value }))
    setFieldErrors((current) => ({ ...current, [key]: [] }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setFieldErrors({})
    try {
      // Only send guardian details when they apply.
      await register(needsGuardian ? form : { ...form, guardian_consent: false, guardian_name: '' })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setFieldErrors(err.fieldErrors)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Create your account"
      subtitle={<>Already have one? <Link to="/login" className="font-medium text-brand-blue hover:underline">Log in</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <FormAlert message={error} />

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">I am a…</legend>
          <div className="space-y-2">
            {ACCOUNT_TYPES.map((option) => {
              const selected = form.account_type === option.value
              return (
                <label
                  key={option.value}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition ${
                    selected ? 'border-brand-blue bg-brand-blue/5 ring-1 ring-brand-blue' : 'border-slate-300 hover:border-slate-400'
                  }`}
                >
                  <input
                    type="radio" name="account_type" value={option.value} checked={selected}
                    onChange={() => update('account_type', option.value)}
                    className="mt-1 accent-brand-blue"
                  />
                  <span>
                    <span className="block font-medium text-slate-900">{option.title}</span>
                    <span className="block text-sm text-slate-600">{option.description}</span>
                  </span>
                </label>
              )
            })}
          </div>
          <FieldError messages={fieldErrors.account_type} />
        </fieldset>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="First name" name="first_name" autoComplete="given-name" required
            value={form.first_name} errors={fieldErrors.first_name}
            onChange={(e) => update('first_name', e.target.value)} />
          <TextField label="Last name" name="last_name" autoComplete="family-name" required
            value={form.last_name} errors={fieldErrors.last_name}
            onChange={(e) => update('last_name', e.target.value)} />
        </div>

        <TextField label="Date of birth" name="date_of_birth" type="date" required
          max={TODAY_ISO}
          value={form.date_of_birth} errors={fieldErrors.date_of_birth}
          hint={warning ? <span className="text-amber-700">{warning}</span> : 'We use this to keep younger learners safe.'}
          onChange={(e) => update('date_of_birth', e.target.value)} />

        {needsGuardian && (
          <div className="space-y-3 rounded-lg border border-brand-gold/60 bg-brand-gold/10 p-4">
            <p className="text-sm text-slate-800">
              Because you're under 18, a parent or guardian needs to agree to you using Brights.
            </p>
            <TextField label="Parent or guardian's full name" name="guardian_name" autoComplete="off"
              value={form.guardian_name} errors={fieldErrors.guardian_name}
              onChange={(e) => update('guardian_name', e.target.value)} />
            <label className="flex items-start gap-2 text-sm text-slate-800">
              <input
                type="checkbox" name="guardian_consent" checked={form.guardian_consent}
                onChange={(e) => update('guardian_consent', e.target.checked)}
                className="mt-0.5 accent-brand-blue"
              />
              My parent or guardian has agreed to me creating a Brights account.
            </label>
            <FieldError messages={fieldErrors.guardian_consent} />
          </div>
        )}

        <TextField label="Email" name="email" type="email" autoComplete="email" required
          value={form.email} errors={fieldErrors.email}
          onChange={(e) => update('email', e.target.value)} />
        <TextField label="Password" name="password" type="password" autoComplete="new-password" required
          value={form.password} errors={fieldErrors.password}
          hint="At least 8 characters. Avoid common passwords and your name."
          onChange={(e) => update('password', e.target.value)} />

        <SubmitButton busy={busy}>Create account</SubmitButton>
      </form>
    </AuthCard>
  )
}
