import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { tutorApi, type Subject, type TutorApplication } from '../../api/tutor'
import { useAuth } from '../../auth/AuthContext'
import { FormAlert } from '../../components/Form'
import { FullPageSpinner } from '../../components/FullPageSpinner'
import { ApplicationEditor } from './ApplicationEditor'
import { ApplicationStatusView } from './ApplicationStatusView'
import { PathwayChooser } from './PathwayChooser'

type LoadState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; application: TutorApplication | null; subjects: Subject[] }

/** /tutor/apply — start, continue, or check the status of a tutor application. */
export function ApplyPage() {
  const { user } = useAuth()
  const [state, setState] = useState<LoadState>({ kind: 'loading' })

  const isTutor = user?.account_type === 'tutor'

  useEffect(() => {
    if (!isTutor) return
    let cancelled = false // ignore results if the page is left before they arrive
    Promise.all([tutorApi.getApplication(), tutorApi.subjects()])
      .then(([application, subjects]) => {
        if (!cancelled) setState({ kind: 'ready', application, subjects })
      })
      .catch((err) => {
        if (!cancelled) setState({ kind: 'error', message: err instanceof ApiError ? err.message : 'Could not load your application.' })
      })
    return () => { cancelled = true }
  }, [isTutor])

  if (!isTutor) {
    return (
      <Shell>
        <p className="text-slate-700">Only tutor accounts can apply to tutor.</p>
        <Link to="/dashboard" className="mt-4 inline-block font-medium text-link hover:underline">Back to dashboard</Link>
      </Shell>
    )
  }
  if (state.kind === 'loading') return <FullPageSpinner />
  if (state.kind === 'error') return <Shell><FormAlert message={state.message} /></Shell>

  const setApplication = (application: TutorApplication) =>
    setState((current) => (current.kind === 'ready' ? { ...current, application } : current))

  const { application, subjects } = state
  return (
    <Shell>
      {!application && !user?.email_verified && (
        <div role="status" className="rounded-xl border border-brand-gold/60 bg-brand-gold/10 p-5">
          <p className="font-semibold text-heading">Confirm your email to start</p>
          <p className="mt-1 text-slate-700">
            We sent a confirmation link to <strong>{user?.email}</strong>. Open it, then come back here to start your application.
          </p>
          <Link to="/dashboard" className="mt-3 inline-block font-medium text-link hover:underline">
            Back to dashboard (resend the link there)
          </Link>
        </div>
      )}
      {!application && user?.email_verified && <PathwayChooser onStarted={setApplication} />}
      {application && application.is_editable && (
        <ApplicationEditor application={application} subjects={subjects} onChange={setApplication} />
      )}
      {application && !application.is_editable && <ApplicationStatusView application={application} onChange={setApplication} />}
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
      <h1 className="text-3xl font-bold tracking-[-0.02em] text-heading sm:text-4xl">Tutor application</h1>
      <div className="mt-8">{children}</div>
    </section>
  )
}
