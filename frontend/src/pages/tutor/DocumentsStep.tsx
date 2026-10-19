import { useRef, useState } from 'react'
import { ApiError } from '../../api/client'
import { tutorApi, type DocumentKind, type TutorApplication } from '../../api/tutor'
import { ACCEPTED_FILES, MAX_UPLOAD_MB, formatBytes } from '../../lib/tutorRules'
import { StepFooter } from './ApplicationEditor'

const HINTS: Record<DocumentKind, string> = {
  id_document: 'Your South African ID (both sides of a smart ID card) or passport photo page.',
  matric_results: 'Your NSC certificate or statement of results showing your subject marks.',
  teaching_qualification: 'Your degree or diploma certificate in education.',
  sace_certificate: 'Your current SACE registration certificate.',
}

type Props = {
  application: TutorApplication
  onChange: (a: TutorApplication) => void
  onNext: () => void
  onBack: () => void
}

export function DocumentsStep({ application, onChange, onNext, onBack }: Props) {
  // After each upload/delete, reload the application so checklist and lists stay in sync with the server.
  async function refresh() {
    const latest = await tutorApi.getApplication()
    if (latest) onChange(latest)
  }

  return (
    <div>
      <p className="max-w-2xl leading-relaxed text-slate-700">
        Upload clear photos or scans. PDF, JPG or PNG, up to {MAX_UPLOAD_MB} MB each. Only the Brights
        review team can see these. They are never shown on your profile.
      </p>
      <div className="mt-6 space-y-4">
        {application.required_documents.map((doc) => (
          <DocumentSlot
            key={doc.kind}
            kind={doc.kind}
            label={doc.label}
            files={application.documents.filter((d) => d.kind === doc.kind)}
            onChanged={refresh}
          />
        ))}
      </div>
      <StepFooter onBack={onBack} onNext={onNext} nextLabel="Continue" />
    </div>
  )
}

function DocumentSlot({ kind, label, files, onChanged }: {
  kind: DocumentKind
  label: string
  files: TutorApplication['documents']
  onChanged: () => Promise<void>
}) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputId = `upload-${kind}`

  async function handleFile(file: File | undefined) {
    if (!file) return
    setError(null)
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setError(`That file is ${formatBytes(file.size)}. Files must be ${MAX_UPLOAD_MB} MB or smaller.`)
      return
    }
    setBusy(true)
    try {
      await tutorApi.uploadDocument(kind, file)
      await onChanged()
    } catch (err) {
      // Prefer the server's specific reason (e.g. wrong file type) over the generic message.
      const reason = err instanceof ApiError ? (err.fieldErrors.file?.[0] ?? err.fieldErrors.kind?.[0] ?? err.message) : null
      setError(reason ?? 'Upload failed. Please try again.')
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  async function remove(id: number) {
    setBusy(true)
    setError(null)
    try {
      await tutorApi.deleteDocument(id)
      await onChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not remove the file.')
    } finally {
      setBusy(false)
    }
  }

  const done = files.length > 0
  return (
    <section className={`rounded-xl border bg-surface p-4 sm:p-5 ${done ? 'border-brand-teal/50' : 'border-slate-200'}`} aria-labelledby={`${inputId}-title`}>
      <div className="flex items-start gap-3">
        <span aria-hidden="true" className={`mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
          done ? 'bg-brand-teal text-white' : 'border-2 border-slate-300'
        }`}>{done ? '✓' : ''}</span>
        <div className="flex-1">
          <h3 id={`${inputId}-title`} className="font-sans font-semibold text-heading">{label}</h3>
          <p className="mt-0.5 text-sm text-slate-600">{HINTS[kind]}</p>

          {files.length > 0 && (
            <ul className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200">
              {files.map((f) => (
                <li key={f.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                  <span className="min-w-0 truncate text-slate-800">{f.original_name}</span>
                  <span className="flex shrink-0 items-center gap-3">
                    <span className="text-slate-500">{formatBytes(f.size)}</span>
                    <button type="button" disabled={busy} onClick={() => remove(f.id)}
                      className="rounded px-1.5 py-0.5 text-slate-500 hover:bg-slate-100 hover:text-red-700"
                      aria-label={`Remove ${f.original_name}`}>
                      Remove
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-3">
            <input ref={input} id={inputId} type="file" accept={ACCEPTED_FILES} className="peer sr-only"
              onChange={(e) => handleFile(e.target.files?.[0])} disabled={busy} />
            <label htmlFor={inputId}
              className={`inline-flex cursor-pointer items-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-heading transition hover:bg-slate-50 peer-focus-visible:ring-2 peer-focus-visible:ring-brand-blue/40 ${
                busy ? 'pointer-events-none opacity-60' : ''
              }`}>
              {busy ? 'Uploading…' : done ? 'Add another file' : 'Choose file'}
            </label>
          </div>
          {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
        </div>
      </div>
    </section>
  )
}
