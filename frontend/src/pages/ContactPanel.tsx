import { useState } from 'react'
import { Link, useLocation } from 'react-router'
import { ApiError } from '../api/client'
import { contactApi, type ContactResult } from '../api/contact'
import type { PublicTutor } from '../api/profiles'
import { useAuth } from '../auth/AuthContext'
import { SafetyDialog } from '../components/SafetyDialog'

/** The "Contact on WhatsApp" part of a tutor's profile. */
export function ContactPanel({ tutor }: { tutor: PublicTutor }) {
  const { user } = useAuth()
  const location = useLocation()
  const [subjectId, setSubjectId] = useState<string>(tutor.subjects.length === 1 ? String(tutor.subjects[0].id) : '')
  const [grade, setGrade] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ContactResult | null>(null)
  const [safetyOpen, setSafetyOpen] = useState(false)

  if (!user) {
    return (
      <Link to="/login" state={{ from: location.pathname }}
        className="block w-full rounded-full bg-brand-deep px-5 py-3 text-center font-semibold text-white transition hover:bg-brand">
        Log in to contact
      </Link>
    )
  }
  if (user.account_type !== 'learner' && user.account_type !== 'parent') {
    return <p className="text-sm text-slate-600">Only learner and parent accounts can contact tutors.</p>
  }

  const subject = tutor.subjects.find((s) => String(s.id) === subjectId)

  async function requestContact() {
    setBusy(true)
    setError(null)
    try {
      setResult(await contactApi.contact(tutor.id, { subject: subject?.id ?? null, grade: grade ? Number(grade) : null }))
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSafetyOpen(true) // under-18 learner who hasn't seen the safety guidance yet
      } else {
        setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  async function confirmSafety() {
    setBusy(true)
    try {
      await contactApi.acknowledgeSafety()
      setSafetyOpen(false)
    } catch {
      setError('Something went wrong. Please try again.')
      setBusy(false)
      return
    }
    setBusy(false)
    await requestContact()
  }

  if (result) {
    return (
      <div className="space-y-3">
        <a href={result.whatsapp_url} target="_blank" rel="noopener noreferrer"
          className="flex w-full items-center justify-center gap-2 rounded-full bg-[#1f7a4d] px-5 py-3 font-semibold text-white transition hover:bg-[#17603c] focus:outline-none focus-visible:ring-4 focus-visible:ring-[#1f7a4d]/30">
          Open WhatsApp chat
        </a>
        <p className="text-xs leading-relaxed text-slate-500">
          Your message will start with: <span className="text-slate-700">“{result.message}”</span> You can edit it before sending.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="contact-subject" className="mb-1 block text-sm font-medium text-slate-700">Subject</label>
        <select id="contact-subject" value={subjectId} onChange={(e) => { setSubjectId(e.target.value); setGrade('') }}
          className="w-full rounded-lg border border-slate-300 bg-surface px-3 py-2">
          <option value="">Choose a subject…</option>
          {tutor.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>
      {subject && (
        <div>
          <label htmlFor="contact-grade" className="mb-1 block text-sm font-medium text-slate-700">Grade</label>
          <select id="contact-grade" value={grade} onChange={(e) => setGrade(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-surface px-3 py-2">
            <option value="">Choose a grade…</option>
            {subject.grades.map((g) => <option key={g} value={g}>Grade {g}</option>)}
          </select>
        </div>
      )}
      <button type="button" onClick={requestContact} disabled={busy}
        className="w-full rounded-full bg-brand-deep px-5 py-3 font-semibold text-white transition hover:bg-brand disabled:opacity-60">
        {busy ? 'Please wait…' : 'Contact on WhatsApp'}
      </button>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <SafetyDialog open={safetyOpen} busy={busy} onConfirm={confirmSafety} onCancel={() => setSafetyOpen(false)} />
    </div>
  )
}
