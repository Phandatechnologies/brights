import { useState } from 'react'
import { ApiError } from '../../api/client'
import { tutorApi, type TutorApplication } from '../../api/tutor'
import { FormAlert } from '../../components/Form'
import { MIN_SUBJECT_MARK } from '../../lib/tutorRules'
import { StepFooter } from './ApplicationEditor'
import { ApplicationSummary } from './ApplicationSummary'

type Props = {
  application: TutorApplication
  onSubmitted: (a: TutorApplication) => void
  onBack: () => void
  onEditStep: (step: number) => void
}

/** What's still missing, worked out from the application (the server re-checks on submit). */
function missingItems(a: TutorApplication): { text: string; step: number }[] {
  const items: { text: string; step: number }[] = []
  if (a.pathway === 'teacher') {
    if (!a.sace_number.trim()) items.push({ text: 'Your SACE registration number', step: 0 })
    if (!a.qualification_name.trim()) items.push({ text: 'The name of your teaching qualification', step: 0 })
  }
  if (a.subjects.length === 0) items.push({ text: 'At least one subject', step: 1 })
  if (a.pathway === 'academic' && a.subjects.some((s) => (s.matric_mark ?? 0) < MIN_SUBJECT_MARK)) {
    items.push({ text: `A mark of ${MIN_SUBJECT_MARK}% or more for every subject`, step: 1 })
  }
  for (const doc of a.required_documents) if (!doc.uploaded) items.push({ text: doc.label, step: 2 })
  return items
}

export function ReviewStep({ application, onSubmitted, onBack, onEditStep }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [problems, setProblems] = useState<string[]>([])
  const missing = missingItems(application)

  async function submit() {
    setBusy(true)
    setError(null)
    setProblems([])
    try {
      onSubmitted(await tutorApi.submit())
      window.scrollTo({ top: 0 })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setProblems(Object.values(err.fieldErrors).flat())
      } else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      {missing.length > 0 ? (
        <div className="rounded-xl border border-slate-200 bg-chalk p-5">
          <p className="font-semibold text-heading">Still needed before you can submit</p>
          <ul className="mt-3 space-y-2">
            {missing.map((item) => (
              <li key={item.text} className="flex flex-wrap items-baseline justify-between gap-2 text-slate-800">
                <span>{item.text}</span>
                <button type="button" onClick={() => onEditStep(item.step)} className="text-sm font-medium text-link hover:underline">
                  Add it
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="rounded-xl border border-brand-soft/50 bg-brand-soft/10 p-5 text-slate-800">
          Everything's in place. Check the details below, then submit for review.
        </p>
      )}

      <div className="mt-6 space-y-2">
        <FormAlert message={error} />
        {problems.length > 0 && <ul className="list-disc pl-5 text-sm text-red-700">{problems.map((p) => <li key={p}>{p}</li>)}</ul>}
      </div>

      <div className="mt-6"><ApplicationSummary application={application} /></div>

      <p className="mt-6 text-sm leading-relaxed text-slate-600">
        By submitting, you confirm the information and documents are genuine. Once submitted, you
        can't make changes unless our team asks for more information.
      </p>
      <StepFooter onBack={onBack} busy={busy} disabled={missing.length > 0} onNext={submit} nextLabel="Submit for review" />
    </div>
  )
}
