import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { VerifyEmailBanner } from '../components/VerifyEmailBanner'
import { TutorHome } from './tutor/TutorHome'

const TYPE_LABELS: Record<string, string> = {
  learner: 'Learner',
  parent: 'Parent or guardian',
  tutor: 'Tutor',
  '': 'Staff',
}

const NEXT_STEPS: Record<string, string> = {
  learner: 'Search verified tutors by subject, grade, area and price. Tutors you contact are saved under My tutors.',
  parent: 'Find a verified tutor for your child by subject, grade, area and price. Tutors you contact are saved under My tutors.',
  '': 'Use the Django admin to manage the platform.',
}

export function DashboardPage() {
  const { user } = useAuth()
  if (!user) return null // RequireAuth guarantees a user; this keeps TypeScript happy

  return (
    <section className="mx-auto max-w-3xl px-4 py-8 sm:py-10">
      <h1 className="text-3xl font-bold text-heading">Hi {user.first_name} 👋</h1>
      {user.account_type === 'tutor' ? (
        <>
          <VerifyEmailBanner />
          <TutorHome user={user} />
        </>
      ) : (
        <>
          <p className="mt-1 text-slate-600">
            Signed in as <span className="[overflow-wrap:anywhere]">{user.email}</span>{' '}
            <span className="whitespace-nowrap">({TYPE_LABELS[user.account_type]})</span>
          </p>
          <VerifyEmailBanner />
          <div className="mt-8 rounded-2xl border border-slate-200 bg-surface p-6 shadow-sm">
            <h2 className="font-semibold text-slate-900">What's next</h2>
            <p className="mt-2 text-slate-600">{NEXT_STEPS[user.account_type]}</p>
            {user.account_type !== '' && (
              <Link to="/tutors" className="mt-5 inline-block rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand">
                Find a tutor
              </Link>
            )}
          </div>
        </>
      )}
    </section>
  )
}
