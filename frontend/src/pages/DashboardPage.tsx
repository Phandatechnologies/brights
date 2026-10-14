import { useAuth } from '../auth/AuthContext'

const TYPE_LABELS: Record<string, string> = {
  learner: 'Learner',
  parent: 'Parent or guardian',
  tutor: 'Tutor',
  '': 'Staff',
}

const NEXT_STEPS: Record<string, string> = {
  learner: 'Tutor search is coming soon. You will be able to filter by subject, grade, area and price.',
  parent: "Tutor search is coming soon. You'll be able to find verified tutors for your child.",
  tutor: 'Tutor applications open soon. You will upload your Matric results or teaching qualifications for review.',
  '': 'Use the Django admin to manage the platform.',
}

export function DashboardPage() {
  const { user } = useAuth()
  if (!user) return null // RequireAuth guarantees a user; this keeps TypeScript happy

  return (
    <section className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-bold text-brand-navy">Hi {user.first_name} 👋</h1>
      <p className="mt-1 text-slate-600">
        Signed in as {user.email} · <span className="font-medium">{TYPE_LABELS[user.account_type]}</span>
      </p>
      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-semibold text-slate-900">What's next</h2>
        <p className="mt-2 text-slate-600">{NEXT_STEPS[user.account_type]}</p>
      </div>
    </section>
  )
}
