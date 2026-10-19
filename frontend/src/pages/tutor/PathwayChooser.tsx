import { useState } from 'react'
import { ApiError } from '../../api/client'
import { tutorApi, type Pathway, type TutorApplication } from '../../api/tutor'
import { FormAlert, SubmitButton } from '../../components/Form'
import { PATHWAYS } from '../../lib/pathways'

export function PathwayCards({ value, onChange }: { value: Pathway | null; onChange: (p: Pathway) => void }) {
  return (
    <fieldset>
      <legend className="mb-3 font-medium text-slate-800">How will you qualify?</legend>
      <div className="grid gap-3 sm:grid-cols-2">
        {PATHWAYS.map((option) => {
          const selected = value === option.value
          return (
            <label
              key={option.value}
              className={`flex cursor-pointer gap-3 rounded-xl border p-4 transition ${
                selected ? 'border-brand-blue bg-brand-blue/5 ring-1 ring-brand-blue' : 'border-slate-300 bg-surface hover:border-slate-400'
              }`}
            >
              <input type="radio" name="pathway" value={option.value} checked={selected}
                onChange={() => onChange(option.value)} className="mt-1 accent-brand-blue" />
              <span>
                <span className="block font-semibold text-heading">{option.title}</span>
                <span className="mt-1 block text-sm leading-relaxed text-slate-600">{option.description}</span>
              </span>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}

/** First screen for a tutor with no application yet. */
export function PathwayChooser({ onStarted }: { onStarted: (a: TutorApplication) => void }) {
  const [pathway, setPathway] = useState<Pathway | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function start(event: React.FormEvent) {
    event.preventDefault()
    if (!pathway) return setError('Choose how you will qualify.')
    setBusy(true)
    setError(null)
    try {
      onStarted(await tutorApi.start(pathway))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={start} className="space-y-6">
      <p className="max-w-2xl text-lg leading-relaxed text-slate-700">
        Before you appear in search, our team checks your documents by hand. You can save your
        progress and come back at any time; nothing is reviewed until you submit.
      </p>
      <FormAlert message={error} />
      <PathwayCards value={pathway} onChange={setPathway} />
      <div className="max-w-xs">
        <SubmitButton busy={busy}>Start application</SubmitButton>
      </div>
    </form>
  )
}
