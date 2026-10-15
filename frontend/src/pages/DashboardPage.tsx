import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { contactApi, type ContactHistoryItem } from '../api/contact'
import { tutorApi, type TutorApplication } from '../api/tutor'
import { useAuth } from '../auth/AuthContext'

const TYPE_LABELS: Record<string, string> = {
  learner: 'Learner',
  parent: 'Parent or guardian',
  tutor: 'Tutor',
  '': 'Staff',
}

const NEXT_STEPS: Record<string, string> = {
  learner: 'Search verified tutors by subject, grade, area and price.',
  parent: 'Find a verified tutor for your child by subject, grade, area and price.',
  '': 'Use the Django admin to manage the platform.',
}

/** What a tutor sees about their application on the dashboard. */
function TutorApplicationCard() {
  const [application, setApplication] = useState<TutorApplication | null | undefined>(undefined)

  useEffect(() => {
    tutorApi.getApplication().then(setApplication).catch(() => setApplication(null))
  }, [])

  if (application === undefined) return <p className="text-slate-500">Loading your application…</p>

  const content: { text: string; action: string; to?: string } = (() => {
    if (!application) return {
      text: 'Apply to become a Brights tutor. It takes about 10 minutes if you have your documents ready.',
      action: 'Start your application',
    }
    switch (application.status) {
      case 'draft': return { text: "You've started your application. Finish it and submit it for review.", action: 'Continue application' }
      case 'more_info': return { text: 'Our team needs more information from you before they can decide.', action: 'See what is needed' }
      case 'pending': return { text: "Your application is with our review team. We'll update you here.", action: 'View application' }
      case 'approved': return { text: "You're approved. Complete your profile so learners can find you.", action: 'Edit your profile', to: '/tutor/profile' }
      case 'rejected': return { text: 'Your application was not approved. See the note from our team.', action: 'View application' }
      case 'suspended': return { text: 'Your tutor account is suspended. See the note from our team.', action: 'View application' }
      default: return { text: `Application status: ${application.status_label}.`, action: 'View application' }
    }
  })()

  return (
    <>
      <p className="mt-2 text-slate-600">{content.text}</p>
      <Link to={content.to ?? '/tutor/apply'}
        className="mt-5 inline-block rounded-full bg-brand-navy px-6 py-3 font-semibold text-white transition hover:bg-brand-blue focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-blue/30">
        {content.action}
      </Link>
    </>
  )
}

/** Learners and parents: tutors they've contacted through Brights. */
function ContactedTutors() {
  const [items, setItems] = useState<ContactHistoryItem[] | null>(null)
  useEffect(() => {
    contactApi.history().then(setItems).catch(() => setItems([]))
  }, [])
  if (!items || items.length === 0) return null
  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="font-semibold text-slate-900">Tutors you've contacted</h2>
      <ul className="mt-3 divide-y divide-slate-100">
        {items.map((item) => (
          <li key={item.tutor_id} className="flex flex-wrap items-center justify-between gap-2 py-3">
            {item.available ? (
              <Link to={`/tutors/${item.tutor_id}`} className="font-medium text-brand-blue hover:underline">{item.name}</Link>
            ) : (
              <span className="text-slate-500">{item.name} (no longer available)</span>
            )}
            <span className="flex items-center gap-4 text-sm text-slate-500">
              {new Date(item.last_contacted).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' })}
              <Link to={`/tutors/${item.tutor_id}/report`} state={{ tutorName: item.name }} className="hover:text-red-700 hover:underline">
                Report
              </Link>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  if (!user) return null // RequireAuth guarantees a user; this keeps TypeScript happy

  return (
    <section className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-bold text-brand-navy">Hi {user.first_name} 👋</h1>
      <p className="mt-1 text-slate-600">
        Signed in as {user.email} ({TYPE_LABELS[user.account_type]})
      </p>
      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-semibold text-slate-900">
          {user.account_type === 'tutor' ? 'Your tutor application' : "What's next"}
        </h2>
        {user.account_type === 'tutor' ? <TutorApplicationCard /> : (
          <>
            <p className="mt-2 text-slate-600">{NEXT_STEPS[user.account_type]}</p>
            {user.account_type !== '' && (
              <Link to="/tutors" className="mt-5 inline-block rounded-full bg-brand-navy px-6 py-3 font-semibold text-white transition hover:bg-brand-blue">
                Find a tutor
              </Link>
            )}
          </>
        )}
      </div>
      {(user.account_type === 'learner' || user.account_type === 'parent') && <ContactedTutors />}
    </section>
  )
}
