import { useState } from 'react'
import type { Subject, TutorApplication } from '../../api/tutor'
import { DocumentsStep } from './DocumentsStep'
import { ReviewStep } from './ReviewStep'
import { SubjectsStep } from './SubjectsStep'
import { TypeStep } from './TypeStep'

const STEPS = ['Application type', 'Subjects', 'Documents', 'Review and submit'] as const

type Props = {
  application: TutorApplication
  subjects: Subject[]
  onChange: (a: TutorApplication) => void
}

export function ApplicationEditor({ application, subjects, onChange }: Props) {
  const [step, setStep] = useState(application.status === 'more_info' ? 3 : 0)
  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1))
  const back = () => setStep((s) => Math.max(s - 1, 0))

  return (
    <div>
      {application.status === 'more_info' && (
        <div role="status" className="mb-8 rounded-xl border border-brand-gold/60 bg-brand-gold/10 p-5">
          <p className="font-semibold text-heading">Our team needs more information</p>
          {application.reviewer_message && (
            <p className="mt-2 whitespace-pre-line text-slate-800">{application.reviewer_message}</p>
          )}
          <p className="mt-2 text-sm text-slate-600">Make the changes below, then submit again.</p>
        </div>
      )}

      <nav aria-label="Application steps" className="mb-8">
        <ol className="grid grid-cols-4 gap-2">
          {STEPS.map((label, index) => {
            const current = index === step
            const done = index < step
            return (
              <li key={label}>
                <button
                  type="button"
                  onClick={() => setStep(index)}
                  aria-current={current ? 'step' : undefined}
                  className="group w-full text-left"
                >
                  <span className={`block h-1.5 rounded-full transition ${current || done ? 'bg-brand-navy' : 'bg-slate-200 group-hover:bg-slate-300'}`} />
                  <span className={`mt-2 block text-xs sm:text-sm ${current ? 'font-semibold text-heading' : 'text-slate-500'}`}>
                    <span className="tabular-nums">{index + 1}.</span> <span className="hidden sm:inline">{label}</span>
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
        <p className="mt-3 text-sm font-medium text-heading sm:hidden">{STEPS[step]}</p>
      </nav>

      {step === 0 && <TypeStep application={application} onSaved={(a) => { onChange(a); next() }} />}
      {step === 1 && <SubjectsStep application={application} subjects={subjects} onSaved={(a) => { onChange(a); next() }} onBack={back} />}
      {step === 2 && <DocumentsStep application={application} onChange={onChange} onNext={next} onBack={back} />}
      {step === 3 && <ReviewStep application={application} onSubmitted={onChange} onBack={back} onEditStep={setStep} />}
    </div>
  )
}

/** Shared Back / Continue footer for the steps. */
export function StepFooter({ onBack, busy, disabled, nextLabel = 'Save and continue', onNext }: {
  onBack?: () => void
  busy?: boolean
  disabled?: boolean
  nextLabel?: string
  onNext?: () => void
}) {
  return (
    <div className="mt-8 flex items-center justify-between gap-4 border-t border-slate-200 pt-6">
      {onBack ? (
        <button type="button" onClick={onBack} className="rounded-lg px-4 py-2.5 font-medium text-slate-700 hover:bg-slate-100">
          Back
        </button>
      ) : <span />}
      <button
        type={onNext ? 'button' : 'submit'}
        onClick={onNext}
        disabled={busy || disabled}
        className="rounded-full bg-brand-navy px-6 py-3 font-semibold text-white transition hover:bg-brand-blue focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-blue/30 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? 'Saving…' : nextLabel}
      </button>
    </div>
  )
}
