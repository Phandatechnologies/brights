import { useState } from 'react'
import { authApi } from '../api/auth'
import { useAuth } from '../auth/AuthContext'

/** Reminds logged-in users to confirm their email, with a resend button. */
export function VerifyEmailBanner() {
  const { user } = useAuth()
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  if (!user || user.email_verified) return null

  async function resend() {
    setState('sending')
    try {
      await authApi.resendVerification()
      setState('sent')
    } catch {
      setState('error')
    }
  }

  return (
    <div role="status" className="mt-6 rounded-xl border border-brand-gold/60 bg-brand-gold/10 p-5">
      <p className="font-semibold text-brand-navy">Please confirm your email</p>
      <p className="mt-1 text-slate-700">
        We sent a link to <strong>{user.email}</strong>. You need to confirm it before you can contact tutors,
        send reports or submit a tutor application.
      </p>
      <div className="mt-3 text-sm">
        {state === 'sent' ? (
          <span className="font-medium text-pass">New link sent. Check your inbox and spam folder.</span>
        ) : (
          <button type="button" onClick={resend} disabled={state === 'sending'} className="font-medium text-brand-blue hover:underline disabled:opacity-60">
            {state === 'sending' ? 'Sending…' : 'Send a new link'}
          </button>
        )}
        {state === 'error' && <span className="ml-3 text-red-700">Couldn't send. Try again in a minute.</span>}
      </div>
    </div>
  )
}
