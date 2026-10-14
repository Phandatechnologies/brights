import { useMemo, useState, type FormEvent } from 'react'
import { ApiError } from '../../api/client'
import { tutorApi, type Subject, type TutorApplication } from '../../api/tutor'
import { FormAlert } from '../../components/Form'
import { GRADES, MIN_SUBJECT_MARK, markProblem } from '../../lib/tutorRules'
import { StepFooter } from './ApplicationEditor'

type Row = { subject: Subject; mark: string; grades: number[] }

type Props = {
  application: TutorApplication
  subjects: Subject[]
  onSaved: (a: TutorApplication) => void
  onBack: () => void
}

export function SubjectsStep({ application, subjects, onSaved, onBack }: Props) {
  const academic = application.pathway === 'academic'
  const [rows, setRows] = useState<Row[]>(() =>
    application.subjects.map((s) => ({
      subject: s.subject,
      mark: s.matric_mark === null ? '' : String(s.matric_mark),
      grades: s.grades,
    })),
  )
  const [adding, setAdding] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [serverProblems, setServerProblems] = useState<string[]>([])
  const [busy, setBusy] = useState(false)

  const available = useMemo(
    () => subjects.filter((s) => !rows.some((r) => r.subject.id === s.id)),
    [subjects, rows],
  )

  function addSubject(id: string) {
    const subject = subjects.find((s) => String(s.id) === id)
    if (subject) setRows((current) => [...current, { subject, mark: '', grades: [] }])
    setAdding('')
  }

  function updateRow(index: number, change: Partial<Row>) {
    setError(null) // the tutor is fixing things; clear the old warning
    setRows((current) => current.map((row, i) => (i === index ? { ...row, ...change } : row)))
  }

  function toggleGrade(index: number, grade: number) {
    const row = rows[index]
    const grades = row.grades.includes(grade) ? row.grades.filter((g) => g !== grade) : [...row.grades, grade].sort((a, b) => a - b)
    updateRow(index, { grades })
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setServerProblems([])
    if (rows.length === 0) return setError('Add at least one subject you want to tutor.')
    const firstProblem = rows.find((r) => (academic && markProblem(toMark(r.mark))) || r.grades.length === 0)
    if (firstProblem) return setError('Fix the highlighted subjects before continuing.')

    setBusy(true)
    try {
      const saved = await tutorApi.update({
        subjects: rows.map((r) => ({ subject: r.subject.id, matric_mark: academic ? toMark(r.mark) : null, grades: r.grades })),
      })
      onSaved(saved)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setServerProblems(Object.values(err.fieldErrors).flat())
      } else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={save} noValidate>
      <p className="max-w-2xl leading-relaxed text-slate-700">
        {academic
          ? `Add each subject you want to tutor with your final Matric mark. You can only tutor subjects where you got ${MIN_SUBJECT_MARK}% or more. Then choose the grades you're confident teaching.`
          : 'Add each subject your teaching qualification covers, and the grades you teach it to.'}
      </p>

      <div className="mt-6 space-y-3">
        <FormAlert message={error} />
        {serverProblems.length > 0 && (
          <ul className="list-disc pl-5 text-sm text-red-700">{serverProblems.map((p) => <li key={p}>{p}</li>)}</ul>
        )}
      </div>

      <ul className="mt-4 space-y-4">
        {rows.map((row, index) => {
          const problem = academic && row.mark !== '' ? markProblem(toMark(row.mark)) : null
          const fieldId = `mark-${row.subject.id}`
          return (
            <li key={row.subject.id} className={`rounded-xl border bg-white p-4 sm:p-5 ${problem ? 'border-red-300' : 'border-slate-200'}`}>
              <div className="flex items-start justify-between gap-4">
                <h3 className="font-sans text-lg font-semibold text-brand-navy">{row.subject.name}</h3>
                <button type="button" onClick={() => setRows((c) => c.filter((_, i) => i !== index))}
                  className="rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 hover:text-red-700"
                  aria-label={`Remove ${row.subject.name}`}>
                  Remove
                </button>
              </div>

              <div className="mt-4 flex flex-col gap-5 sm:flex-row sm:items-start">
                {academic && (
                  <div className="sm:w-36">
                    <label htmlFor={fieldId} className="mb-1 block text-sm font-medium text-slate-700">Matric mark</label>
                    <div className="relative">
                      <input id={fieldId} inputMode="numeric" value={row.mark}
                        onChange={(e) => updateRow(index, { mark: e.target.value.replace(/[^0-9]/g, '').slice(0, 3) })}
                        aria-invalid={Boolean(problem)} aria-describedby={problem ? `${fieldId}-error` : undefined}
                        className={`w-full rounded-lg border px-3 py-2.5 pr-8 tabular-nums outline-none focus:ring-2 ${
                          problem ? 'border-red-400 focus:ring-red-200' : 'border-slate-300 focus:border-brand-blue focus:ring-brand-blue/20'
                        }`} />
                      <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-500">%</span>
                    </div>
                  </div>
                )}
                <fieldset className="flex-1">
                  <legend className="mb-1 text-sm font-medium text-slate-700">Grades you'll teach</legend>
                  <div className="flex flex-wrap gap-2">
                    {GRADES.map((grade) => {
                      const on = row.grades.includes(grade)
                      return (
                        <button key={grade} type="button" aria-pressed={on} onClick={() => toggleGrade(index, grade)}
                          className={`min-w-[3.25rem] rounded-full border px-3 py-2 text-sm font-medium transition ${
                            on ? 'border-brand-navy bg-brand-navy text-white' : 'border-slate-300 bg-white text-slate-700 hover:border-slate-400'
                          }`}>
                          Gr {grade}
                        </button>
                      )
                    })}
                  </div>
                </fieldset>
              </div>
              {problem && <p id={`${fieldId}-error`} className="mt-3 text-sm text-red-700">{problem}</p>}
            </li>
          )
        })}
      </ul>

      <div className="mt-5">
        <label htmlFor="add-subject" className="mb-1 block text-sm font-medium text-slate-700">
          {rows.length ? 'Add another subject' : 'Add a subject'}
        </label>
        <select id="add-subject" value={adding} onChange={(e) => addSubject(e.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20 sm:max-w-sm">
          <option value="">Choose a subject…</option>
          {available.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>

      <StepFooter onBack={onBack} busy={busy} />
    </form>
  )
}

function toMark(value: string): number | null {
  return value === '' ? null : Number(value)
}
