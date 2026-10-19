import { Link } from 'react-router'
import { ThemeSwitch } from '../components/ThemeSwitch'
import { useAuth } from '../auth/AuthContext'
import { Spark } from '../components/Spark'

const HERO = '/images/hero-learner'

/* Fictional example used to explain the 60% rule. */
const SAMPLE_RESULTS = [
  { subject: 'Mathematics', mark: 74 },
  { subject: 'Physical Sciences', mark: 68 },
  { subject: 'Life Sciences', mark: 81 },
  { subject: 'English Home Language', mark: 57 },
]
const PASS_MARK = 60

const LEARNER_STEPS = [
  { title: 'Sign up free', body: 'Learners and parents create an account in a minute. Under 18? A parent or guardian agrees first.' },
  { title: 'Search your way', body: 'Filter tutors by subject, grade, area, price, and whether you want online or in-person lessons.' },
  { title: 'Message on WhatsApp', body: "Like someone's profile? Contact them on WhatsApp to ask questions and set up a first lesson." },
  { title: 'Agree on the details', body: "You and the tutor arrange times and payment directly. Brights doesn't handle payments." },
]

function Hero({ signedIn }: { signedIn: boolean }) {
  return (
    <section className="relative isolate overflow-hidden bg-chalk">
      {/* On phones the photo sits above the text; from md up it fills a right-hand panel. */}
      <div className="md:absolute md:inset-y-0 md:right-0 md:w-[64%] lg:w-[60%]">
        <picture>
          <source
            media="(max-width: 767px)"
            srcSet={`${HERO}-portrait-640.webp 640w, ${HERO}-portrait-1080.webp 1080w`}
            sizes="100vw"
          />
          <img
            src={`${HERO}-1600.webp`}
            srcSet={`${HERO}-960.webp 960w, ${HERO}-1600.webp 1600w, ${HERO}-2400.webp 2400w`}
            sizes="(min-width: 768px) 64vw, 100vw"
            alt="A high school learner at her desk, looking up from her notes"
            fetchPriority="high"
            className="block aspect-[4/5] max-h-[62vh] w-full object-cover object-top md:aspect-auto md:h-full md:max-h-none md:object-[48%_30%]"
          />
        </picture>
        {/* Blends the photo's white wall into the page background. */}
        <div
          aria-hidden="true"
          className="absolute inset-y-0 left-0 hidden w-1/3 bg-gradient-to-r from-chalk to-transparent md:block"
        />
      </div>

      <div className="relative mx-auto flex max-w-6xl px-4 pb-14 pt-8 md:min-h-[min(86vh,760px)] md:items-center md:py-24">
        <div className="relative max-w-xl md:max-w-[26rem] lg:max-w-[34rem]">
          <Spark className="spark absolute -top-10 right-0 h-12 w-12 text-brand-gold md:-right-14 md:-top-12 md:h-14 md:w-14 lg:-right-20 lg:h-16 lg:w-16" />

          <h1 className="text-[2.75rem] font-bold leading-[0.98] tracking-[-0.03em] text-heading sm:text-6xl lg:text-[4.75rem]">
            Find a tutor who's been where you are.
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-ink/80">
            Brights connects Grade 8–12 learners in Gauteng with tutors we check by hand: recent
            matriculants, university students and qualified teachers.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4">
            {signedIn ? (
              <Link
                to="/dashboard"
                className="rounded-full bg-brand-navy px-7 py-3.5 font-semibold text-white shadow-lg shadow-brand-navy/20 transition hover:bg-brand-blue focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-blue/30"
              >
                Go to your dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/tutors"
                  className="rounded-full bg-brand-navy px-7 py-3.5 font-semibold text-white shadow-lg shadow-brand-navy/20 transition hover:bg-brand-blue focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-blue/30"
                >
                  Find a tutor
                </Link>
                <Link
                  to="/register?as=tutor"
                  className="font-semibold text-heading underline decoration-brand-gold decoration-[3px] underline-offset-[6px] transition hover:decoration-brand-navy"
                >
                  I want to tutor
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

function ResultsSlip() {
  const canTutor = SAMPLE_RESULTS.filter((r) => r.mark >= PASS_MARK).length
  return (
    <figure className="mx-auto w-full max-w-md">
      <div className="rounded-2xl border border-slate-200 bg-surface p-6 shadow-[0_24px_60px_-28px_rgba(4,51,134,0.35)] md:-rotate-[1.5deg]">
        <div className="flex items-baseline justify-between border-b border-dashed border-slate-300 pb-4">
          <p className="font-display text-xl font-semibold text-heading">Thabo's Matric results</p>
          <p className="text-sm text-slate-500">Example</p>
        </div>
        <ul className="divide-y divide-slate-100">
          {SAMPLE_RESULTS.map(({ subject, mark }) => {
            const ok = mark >= PASS_MARK
            return (
              <li key={subject} className="flex items-center gap-3 py-3.5">
                <span className="flex-1 text-ink">{subject}</span>
                <span className="w-12 text-right font-display text-lg font-semibold tabular-nums text-ink">{mark}%</span>
                <span
                  className={`w-28 rounded-full px-3 py-1 text-center text-sm font-medium ${
                    ok ? 'bg-brand-teal/15 text-pass' : 'bg-brand-orange/10 text-below'
                  }`}
                >
                  {ok ? 'Can tutor' : 'Below 60%'}
                </span>
              </li>
            )
          })}
        </ul>
      </div>
      <figcaption className="mt-5 text-center text-slate-600 md:rotate-0">
        Thabo can tutor {canTutor} of these {SAMPLE_RESULTS.length} subjects.
      </figcaption>
    </figure>
  )
}

function Verification() {
  return (
    <section className="bg-surface py-20 md:py-28">
      <div className="mx-auto grid max-w-6xl items-center gap-14 px-4 md:grid-cols-2">
        <div className="max-w-lg">
          <h2 className="text-4xl font-bold leading-tight tracking-[-0.02em] text-heading md:text-5xl">
            Checked subject by subject, by a real person.
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-ink/80">
            Before a tutor appears in search, our team reviews their documents by hand. A tutor who
            matriculated can only offer subjects they passed with 60% or more, so a strong maths
            mark doesn't make someone an English tutor.
          </p>
          <p className="mt-4 text-lg leading-relaxed text-ink/80">
            Qualified teachers are checked against their teaching qualifications instead. Every
            tutor is 18 or older.
          </p>
        </div>
        <ResultsSlip />
      </div>
    </section>
  )
}

function HowItWorks() {
  return (
    <section className="bg-chalk py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-4">
        <h2 className="max-w-2xl text-4xl font-bold leading-tight tracking-[-0.02em] text-heading md:text-5xl">
          From sign-up to first lesson
        </h2>
        <ol className="mt-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          {LEARNER_STEPS.map((step, index) => (
            <li key={step.title} className="border-t-2 border-brand-navy/15 pt-5">
              <span className="font-display text-4xl font-bold text-link/80 tabular-nums">{index + 1}</span>
              <h3 className="mt-3 text-xl font-semibold text-heading">{step.title}</h3>
              <p className="mt-2 leading-relaxed text-ink/75">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function Safety() {
  const points = [
    { title: 'Guardians are part of it', body: 'Learners under 18 can only sign up once a parent or guardian has agreed.' },
    { title: 'Documents stay private', body: 'Matric results and qualifications are seen only by our review team, never shown on profiles.' },
    { title: 'Problems get looked at', body: 'Anyone can report a tutor. We investigate, and we suspend accounts that break the rules.' },
  ]
  return (
    <section className="bg-surface py-20 md:py-28">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 md:grid-cols-[1fr_1.4fr]">
        <h2 className="text-4xl font-bold leading-tight tracking-[-0.02em] text-heading md:text-5xl">
          Built with younger learners in mind
        </h2>
        <dl className="space-y-8">
          {points.map((point) => (
            <div key={point.title} className="flex gap-4">
              <Spark className="mt-1 h-5 w-5 shrink-0 text-brand-gold" />
              <div>
                <dt className="text-xl font-semibold text-heading">{point.title}</dt>
                <dd className="mt-1 leading-relaxed text-ink/75">{point.body}</dd>
              </div>
            </div>
          ))}
        </dl>
      </div>
    </section>
  )
}

function TutorInvite() {
  return (
    <section className="relative overflow-hidden bg-brand-navy py-20 text-white md:py-24">
      <Spark className="absolute -right-10 -top-10 h-56 w-56 text-white/5" />
      <div className="relative mx-auto flex max-w-6xl flex-col items-start gap-8 px-4 md:flex-row md:items-end md:justify-between">
        <div className="max-w-2xl">
          <h2 className="text-4xl font-bold leading-tight tracking-[-0.02em] md:text-5xl">
            Passed Matric with 60% or more? Get paid to teach it.
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-white/80">
            Set your own rate, choose online or in-person lessons, and tutor the subjects you know.
            You need to be 18 or older.
          </p>
        </div>
        <Link
          to="/register?as=tutor"
          className="shrink-0 rounded-full bg-brand-gold px-7 py-3.5 font-semibold text-[#043386] transition hover:bg-[#ffd36a] focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-gold/40"
        >
          Apply to tutor
        </Link>
      </div>
    </section>
  )
}

export function HomePage() {
  const { user } = useAuth()
  return (
    <>
      <Hero signedIn={Boolean(user)} />
      <Verification />
      <HowItWorks />
      <Safety />
      {!user && <TutorInvite />}
      <Footer />
    </>
  )
}

/** Only the landing page has a footer; app pages end with their content. */
function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p>Brights is a Phanda Technologies product.</p>
        <ThemeSwitch compact />
        <p>
          Photo by{' '}
          <a href="https://unsplash.com/@silverkblack" className="underline hover:text-slate-700" target="_blank" rel="noreferrer">
            Vitaly Gariev
          </a>{' '}
          on Unsplash
        </p>
      </div>
    </footer>
  )
}
