import { useState, type FormEvent } from 'react'
import { ApiError, type FieldErrors } from '../../api/client'
import { tutorApi, type Pathway, type TutorApplication } from '../../api/tutor'
import { FormAlert, TextField } from '../../components/Form'
import { StepFooter } from './ApplicationEditor'
import { PathwayCards } from './PathwayChooser'

export function TypeStep({ application, onSaved }: { application: TutorApplication; onSaved: (a: TutorApplication) => void }) {
  const [pathway, setPathway] = useState<Pathway>(application.pathway)
  const [saceNumber, setSaceNumber] = useState(application.sace_number)
  const [qualification, setQualification] = useState(application.qualification_name)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    try {
      const data = pathway === 'teacher'
        ? { pathway, sace_number: saceNumber.trim(), qualification_name: qualification.trim() }
        : { pathway }
      onSaved(await tutorApi.update(data))
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
        setErrors(err.fieldErrors)
      } else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={save} className="space-y-6" noValidate>
      <FormAlert message={error} />
      <PathwayCards value={pathway} onChange={setPathway} />
      {errors.subjects && <p className="text-sm text-red-700">{errors.subjects.join(' ')}</p>}

      {pathway === 'teacher' && (
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="SACE registration number" name="sace_number" value={saceNumber}
            errors={errors.sace_number} onChange={(e) => setSaceNumber(e.target.value)} />
          <TextField label="Teaching qualification" name="qualification_name" value={qualification}
            placeholder="e.g. B.Ed (Senior and FET Phase)" errors={errors.qualification_name}
            onChange={(e) => setQualification(e.target.value)} />
        </div>
      )}
      <StepFooter busy={busy} />
    </form>
  )
}
