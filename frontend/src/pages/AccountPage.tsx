import { useState } from 'react'
import { useNavigate } from 'react-router'
import { authApi } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import { ThemeSwitch } from '../components/ThemeSwitch'
import { VerifyEmailBanner } from '../components/VerifyEmailBanner'
import { ROLE_BADGES } from '../lib/navigation'

/** /account — who you're signed in as, password, and log out. */
export function AccountPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [reset, setReset] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  if (!user) return null // RequireAuth guarantees a user

  async function sendResetLink() {
    setReset('sending')
    try {
      await authApi.requestPasswordReset(user!.email)
      setReset('sent')
    } catch {
      setReset('error')
    }
  }

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  const rows: [string, React.ReactNode][] = [
    ['Name', `${user.first_name} ${user.last_name}`],
    ['Email', <span key="email" className="break-all">{user.email}</span>],
    ['Account type', ROLE_BADGES[user.account_type]?.label ?? 'Staff'],
    ['Email confirmed', user.email_verified ? 'Yes' : 'Not yet'],
  ]

  return (
    <section className="mx-auto max-w-2xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Account</h1>
      <VerifyEmailBanner />

      <dl className="mt-6 divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-surface shadow-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex flex-wrap justify-between gap-x-6 gap-y-1 px-5 py-4">
            <dt className="text-sm text-slate-500">{label}</dt>
            <dd className="font-medium text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Password</h2>
        <p className="mt-1 text-sm text-slate-600">We’ll email you a link to choose a new password. Changing it logs you out on other devices.</p>
        {reset === 'sent' ? (
          <p className="mt-3 text-sm font-medium text-pass">Link sent to {user.email}. Check your inbox and spam folder.</p>
        ) : (
          <button type="button" onClick={sendResetLink} disabled={reset === 'sending'}
            className="mt-3 rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-heading hover:bg-slate-50 disabled:opacity-60">
            {reset === 'sending' ? 'Sending…' : 'Email me a password link'}
          </button>
        )}
        {reset === 'error' && <p className="mt-2 text-sm text-red-700">Couldn’t send the link. Try again in a minute.</p>}
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Appearance</h2>
        <p className="mt-1 text-sm text-slate-600">Automatic matches your phone or computer. Your choice is saved on this device.</p>
        <div className="mt-3"><ThemeSwitch /></div>
      </div>

      <button type="button" onClick={handleLogout}
        className="mt-6 w-full rounded-full border border-slate-300 bg-surface px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50 sm:w-auto">
        Log out
      </button>
    </section>
  )
}
