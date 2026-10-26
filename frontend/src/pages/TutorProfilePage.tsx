import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { profilesApi, type PublicTutor } from '../api/profiles'
import { FullPageSpinner } from '../components/FullPageSpinner'
import { Spark } from '../components/Spark'
import { TutorAvatar } from '../components/TutorAvatar'
import { formatRand, gradeRange, lessonModes } from '../lib/format'
import { ContactPanel } from './ContactPanel'

type State = { id: string; tutor: PublicTutor } | { id: string; error: string }

/** /tutors/:id — a tutor's public profile. */
export function TutorProfilePage() {
  // Set by the tutor's own "Preview as a learner" link.
  const preview = Boolean((useLocation().state as { preview?: boolean } | null)?.preview)
  const { id = '' } = useParams()
  const [state, setState] = useState<State | null>(null)

  useEffect(() => {
    let cancelled = false
    profilesApi.tutor(id)
      .then((tutor) => { if (!cancelled) setState({ id, tutor }) })
      .catch((err) => {
        if (cancelled) return
        const missing = err instanceof ApiError && err.status === 404
        setState({ id, error: missing ? "This tutor isn't available right now." : 'Could not load this profile.' })
      })
    return () => { cancelled = true }
  }, [id])

  if (!state || state.id !== id) return <FullPageSpinner />
  if ('error' in state) {
    return (
      <section className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="font-display text-2xl font-semibold text-heading">{state.error}</p>
        <Link to="/tutors" className="mt-4 inline-block font-medium text-link hover:underline">Back to search</Link>
      </section>
    )
  }

  const { tutor } = state
  return (
    <section className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
      {preview ? (
        <div role="status" className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-brand-soft/50 bg-brand-soft/10 px-4 py-3">
          <p className="text-sm font-medium text-heading">Preview: this is what learners and parents see.</p>
          <Link to="/tutor/profile" className="text-sm font-semibold text-link hover:underline">Back to my profile</Link>
        </div>
      ) : (
        <Link to="/tutors" className="text-sm font-medium text-link hover:underline">Back to search</Link>
      )}

      <div className="mt-6 grid gap-10 md:grid-cols-[1fr_18rem]">
        <div>
          <div className="flex items-center gap-5">
            <TutorAvatar name={tutor.full_name} photoUrl={tutor.photo_url} size="lg" />
            <div>
              <h1 className="text-3xl font-bold tracking-[-0.02em] text-heading sm:text-4xl">{tutor.full_name}</h1>
              <p className="mt-1 flex items-center gap-1.5 font-medium text-pass">
                <Spark className="h-4 w-4 text-brand-sun" />{tutor.verification}
              </p>
            </div>
          </div>

          <h2 className="mt-10 text-xl font-semibold text-heading">About</h2>
          <p className="mt-2 whitespace-pre-line leading-relaxed text-ink/85">{tutor.bio}</p>

          <h2 className="mt-10 text-xl font-semibold text-heading">Subjects</h2>
          <ul className="mt-3 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-surface">
            {tutor.subjects.map((s) => (
              <li key={s.id} className="flex flex-wrap justify-between gap-x-4 px-5 py-3">
                <span className="font-medium text-ink">{s.name}</span>
                <span className="text-slate-600">{gradeRange(s.grades)}</span>
              </li>
            ))}
          </ul>
        </div>

        <aside className="md:pt-2">
          <div className="rounded-2xl border border-slate-200 bg-surface p-6 md:sticky md:top-24">
            <p className="font-display text-3xl font-semibold text-ink">
              {formatRand(tutor.hourly_rate)}<span className="text-base font-normal text-slate-500"> / hour</span>
            </p>
            <dl className="mt-5 space-y-3 text-sm">
              <div>
                <dt className="text-slate-500">Lessons</dt>
                <dd className="font-medium text-ink">{lessonModes(tutor.teaches_online, tutor.teaches_in_person)}</dd>
              </div>
              {tutor.teaches_in_person && tutor.area && (
                <div>
                  <dt className="text-slate-500">Area</dt>
                  <dd className="font-medium text-ink">{tutor.area.name}, {tutor.area.province_label}</dd>
                </div>
              )}
              {tutor.availability && (
                <div>
                  <dt className="text-slate-500">Availability</dt>
                  <dd className="font-medium text-ink">{tutor.availability}</dd>
                </div>
              )}
            </dl>
            <div className="mt-6">
              <ContactPanel tutor={tutor} />
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                Lessons and payment are arranged directly with the tutor. Brights doesn't handle payments.
              </p>
              <Link to={`/tutors/${tutor.id}/report`} state={{ tutorName: tutor.full_name }}
                className="mt-4 inline-block text-sm text-slate-500 underline-offset-2 hover:text-red-700 hover:underline">
                Report this tutor
              </Link>
            </div>
          </div>
        </aside>
      </div>
    </section>
  )
}
