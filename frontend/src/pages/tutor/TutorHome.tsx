import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { profilesApi, type OwnProfile, type TutorInsights } from '../../api/profiles'
import { tutorApi, type TutorApplication } from '../../api/tutor'
import type { User } from '../../api/auth'
import { GuideVideos } from '../../components/GuideVideos'

type Loaded = {
  application: TutorApplication | null
  profile: OwnProfile | null
  insights: TutorInsights | null
}

const card = 'rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm sm:p-6'
const primaryButton =
  'inline-block rounded-full bg-brand-deep px-6 py-3 font-semibold text-white transition hover:bg-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30'

/** The tutor's Home: status, this month's numbers, what to fix, and sharing. */
export function TutorHome({ user }: { user: User }) {
  const [data, setData] = useState<Loaded | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      tutorApi.getApplication().catch(() => null), // 404 = not started yet
      profilesApi.ownProfile().catch(() => null),
      profilesApi.insights().catch(() => null),
    ]).then(([application, profile, insights]) => {
      if (!cancelled) setData({ application, profile, insights })
    })
    return () => { cancelled = true }
  }, [])

  if (!data) return <p className="mt-8 text-slate-500">Loading your home…</p>

  const { application, profile, insights } = data
  const approved = application?.status === 'approved'
  const setProfile = (next: OwnProfile) => setData((d) => (d ? { ...d, profile: next } : d))

  return (
    <div className="mt-6 space-y-5">
      {approved && profile ? (
        <ListingSwitch profile={profile} onChange={setProfile} />
      ) : (
        <ApplicationCard application={application} emailVerified={user.email_verified} />
      )}

      {approved && insights && <MonthNumbers insights={insights} />}

      {profile && application && <Checklist profile={profile} approved={approved} />}

      <GuideVideos />

      {approved && profile?.is_listed && <ShareProfile profileId={profile.id} firstName={user.first_name} />}

      {approved && (
        <p className="px-1 text-sm text-slate-500">
          Application approved.{' '}
          <Link to="/tutor/apply" className="font-medium text-link hover:underline">See your approved subjects</Link>
        </p>
      )}
    </div>
  )
}

/* ---------------------------------------------------------------- status ---- */

function ApplicationCard({ application, emailVerified }: { application: TutorApplication | null; emailVerified: boolean }) {
  // Tutors confirm their email before they can start; the banner above has the resend link.
  if (!application && !emailVerified) {
    return (
      <div className={card}>
        <h2 className="font-semibold text-slate-900">Your tutor application</h2>
        <p className="mt-2 text-slate-600">Confirm your email address first. Once it's confirmed, you can start your tutor application here.</p>
      </div>
    )
  }

  const content: { text: string; action: string } = (() => {
    if (!application) return {
      text: 'Apply to become a Brights tutor. It takes about 10 minutes if you have your documents ready.',
      action: 'Start your application',
    }
    switch (application.status) {
      case 'draft': return { text: "You've started your application. Finish it and submit it for review.", action: 'Continue application' }
      case 'more_info': return { text: 'Our team needs more information from you before they can decide.', action: 'See what is needed' }
      case 'pending': return { text: "Your application is with our review team. We'll update you here.", action: 'View application' }
      case 'rejected': return { text: 'Your application was not approved. See the note from our team.', action: 'View application' }
      case 'suspended': return { text: 'Your tutor account is suspended. See the note from our team.', action: 'View application' }
      default: return { text: `Application status: ${application.status_label}.`, action: 'View application' }
    }
  })()

  return (
    <div className={card}>
      <h2 className="font-semibold text-slate-900">Your tutor application</h2>
      <p className="mt-2 text-slate-600">{content.text}</p>
      <Link to="/tutor/apply" className={`mt-5 ${primaryButton}`}>{content.action}</Link>
    </div>
  )
}

/** "Taking new learners" switch, plus whether the tutor is actually visible in search. */
function ListingSwitch({ profile, onChange }: { profile: OwnProfile; onChange: (p: OwnProfile) => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const on = profile.accepting_learners

  async function toggle() {
    setBusy(true)
    setError(null)
    try {
      onChange(await profilesApi.updateOwnProfile({ accepting_learners: !on }))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save. Check your connection and try again.')
    } finally {
      setBusy(false)
    }
  }

  const status = profile.is_listed
    ? { dot: 'bg-pass', title: 'Live in search', text: 'Learners and parents can find and contact you.' }
    : !on
      ? { dot: 'bg-slate-400', title: 'Paused', text: "You're hidden from search and new learners can't contact you. Your profile and numbers are kept." }
      : { dot: 'bg-brand-sun', title: 'Not in search yet', text: 'Finish the steps below so learners can find you.' }

  return (
    <div className={card}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 font-semibold text-slate-900">
            <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-full ${status.dot}`} />
            {status.title}
          </p>
          <p className="mt-1 text-sm text-slate-600">{status.text}</p>
        </div>
        <button type="button" role="switch" aria-checked={on} aria-label="Taking new learners" onClick={toggle} disabled={busy}
          className={`relative mt-0.5 h-8 w-14 shrink-0 rounded-full transition focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30 disabled:opacity-60 ${on ? 'bg-brand' : 'bg-slate-300'}`}>
          <span className={`absolute top-1 h-6 w-6 rounded-full bg-[#ffffff] shadow transition-all ${on ? 'left-7' : 'left-1'}`} />
        </button>
      </div>
      <p className="mt-3 text-sm font-medium text-slate-700">
        Taking new learners: <span className={on ? 'text-pass' : 'text-slate-500'}>{on ? 'On' : 'Off'}</span>
      </p>
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  )
}

/* --------------------------------------------------------------- numbers ---- */

function Comparison({ now, before }: { now: number; before: number }) {
  // Words carry the meaning; the arrow is only a visual hint.
  if (now === before) return <>Same as last month</>
  const up = now > before
  return (
    <>
      <span aria-hidden="true">{up ? '↑' : '↓'} </span>
      {Math.abs(now - before)} {up ? 'more' : 'fewer'} than last month ({before})
    </>
  )
}

function Stat({ label, now, before }: { label: string; now: number; before: number }) {
  return (
    <div className="rounded-xl bg-chalk p-4">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className="mt-1 text-4xl font-bold tracking-tight text-slate-900 tabular-nums">{now}</p>
      <p className="mt-1 text-xs text-slate-500"><Comparison now={now} before={before} /></p>
    </div>
  )
}

function MonthNumbers({ insights }: { insights: TutorInsights }) {
  return (
    <section className={card} aria-labelledby="numbers-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="numbers-heading" className="font-semibold text-slate-900">Your numbers</h2>
        <span className="text-sm text-slate-500">{insights.month_label}</span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Stat label="Profile views" now={insights.views_this_month} before={insights.views_last_month} />
        <Stat label="Learners who contacted you" now={insights.contacts_this_month} before={insights.contacts_last_month} />
      </div>
      {insights.top_requests.length > 0 ? (
        <div className="mt-5">
          <h3 className="text-sm font-semibold text-slate-700">Most asked for this month</h3>
          <ul className="mt-2 divide-y divide-slate-100">
            {insights.top_requests.map((r) => (
              <li key={`${r.subject}-${r.grade}`} className="flex justify-between gap-3 py-2 text-sm">
                <span className="text-slate-800">{r.subject}{r.grade ? `, Grade ${r.grade}` : ''}</span>
                <span className="shrink-0 tabular-nums text-slate-600">{r.count} {r.count === 1 ? 'request' : 'requests'}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">When learners contact you, you'll see which subjects and grades they ask for here.</p>
      )}
      <p className="mt-4 text-xs text-slate-500">
        {insights.contacts_all_time} {insights.contacts_all_time === 1 ? 'learner has' : 'learners have'} contacted you in total.
        Brights shows numbers only, never who viewed your profile.
      </p>
    </section>
  )
}

/* ------------------------------------------------------------- checklist ---- */

type Item = { text: string; done: boolean; note?: string; action?: { label: string; to: string } }

function Checklist({ profile, approved }: { profile: OwnProfile; approved: boolean }) {
  const fix = { label: 'Fix', to: '/tutor/profile' }
  const missing = new Set(profile.missing_fields)
  const items: Item[] = [
    { text: 'A short bio', done: !missing.has('A short bio'), action: fix },
    { text: 'Your hourly rate', done: !missing.has('Your hourly rate'), action: fix },
    { text: 'Online and/or in-person lessons', done: !missing.has('Online and/or in-person lessons'), action: fix },
    ...(profile.teaches_in_person ? [{ text: 'The area you tutor in', done: !missing.has('The area you tutor in'), action: fix }] : []),
    { text: 'Your WhatsApp number', done: !missing.has('Your WhatsApp number'), action: fix },
  ]

  // A photo is required to appear in search; say where it stands.
  if (profile.photo_status === 'none') items.push({ text: 'A profile photo', done: false, action: { label: 'Add', to: '/tutor/profile' } })
  if (profile.photo_status === 'pending') items.push({ text: 'Profile photo', done: false, note: "Waiting for our team to approve it. You'll appear in search once it's approved." })
  if (profile.photo_status === 'rejected') items.push({ text: 'Profile photo', done: false, note: profile.photo_note || 'Not approved. Please upload a different photo.', action: { label: 'Replace', to: '/tutor/profile' } })
  if (profile.photo_status === 'approved') items.push({ text: 'Profile photo', done: true })

  const todo = items.filter((i) => !i.done)
  if (todo.length === 0) {
    return (
      <div className={card}>
        <p className="font-semibold text-slate-900">Your profile is complete ✓</p>
        <p className="mt-1 text-sm text-slate-600">
          Keep your availability up to date. <Link to="/tutor/profile" className="font-medium text-link hover:underline">Edit profile</Link>
        </p>
      </div>
    )
  }

  return (
    <section className={card} aria-labelledby="checklist-heading">
      <h2 id="checklist-heading" className="font-semibold text-slate-900">
        {approved ? 'Your profile checklist' : 'Get your profile ready while you wait'}
      </h2>
      <p className="mt-1 text-sm text-slate-600">{items.length - todo.length} of {items.length} done</p>
      <ul className="mt-3 divide-y divide-slate-100">
        {items.map((item) => (
          <li key={item.text} className="flex items-center gap-3 py-2.5">
            <span aria-hidden="true"
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${item.done ? 'bg-brand-soft/20 text-pass' : 'border-2 border-slate-300'}`}>
              {item.done ? '✓' : ''}
            </span>
            <div className="min-w-0 flex-1">
              <p className={`text-sm ${item.done ? 'text-slate-500' : 'font-medium text-slate-900'}`}>
                {item.text}<span className="sr-only">{item.done ? ' (done)' : ' (to do)'}</span>
              </p>
              {item.note && <p className="text-xs text-slate-500">{item.note}</p>}
            </div>
            {!item.done && item.action && (
              <Link to={item.action.to} className="shrink-0 rounded-full border border-slate-300 px-3 py-1 text-sm font-semibold text-heading hover:bg-slate-50">
                {item.action.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

/* ----------------------------------------------------------------- share ---- */

function ShareProfile({ profileId, firstName }: { profileId: number; firstName: string }) {
  const url = `${window.location.origin}/tutors/${profileId}`
  const message = `Hi! I'm ${firstName}, a verified tutor on Brights. See my subjects and rates, and message me here: ${url}`
  const inputRef = useRef<HTMLInputElement>(null)
  const [copied, setCopied] = useState(false)
  const canShare = typeof navigator.share === 'function'

  async function copy() {
    try {
      await navigator.clipboard.writeText(url)
    } catch {
      // The clipboard API needs HTTPS; on a plain-HTTP test address fall back to selecting the text.
      inputRef.current?.select()
      document.execCommand('copy')
    }
    setCopied(true)
    window.setTimeout(() => setCopied(false), 2500)
  }

  async function nativeShare() {
    try {
      await navigator.share({ title: 'My Brights tutor profile', text: message, url })
    } catch {
      // Cancelled by the user: nothing to do.
    }
  }

  return (
    <section className={card} aria-labelledby="share-heading">
      <h2 id="share-heading" className="font-semibold text-slate-900">Share your profile</h2>
      <p className="mt-1 text-sm text-slate-600">Post it on your WhatsApp Status or send it to parents who ask about lessons.</p>
      <div className="mt-4 flex gap-2">
        <input ref={inputRef} readOnly value={url} aria-label="Your profile link" onFocus={(e) => e.currentTarget.select()}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-chalk px-3 py-2.5 text-sm text-slate-700" />
        <button type="button" onClick={copy}
          className="shrink-0 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-heading hover:bg-slate-50">
          {copied ? 'Copied ✓' : 'Copy'}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <a href={`https://wa.me/?text=${encodeURIComponent(message)}`} target="_blank" rel="noreferrer"
          className="rounded-full bg-[#157a3f] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#106333]">
          Share on WhatsApp
        </a>
        {canShare && (
          <button type="button" onClick={nativeShare}
            className="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-heading hover:bg-slate-50">
            More ways to share
          </button>
        )}
        <Link to={`/tutors/${profileId}`} state={{ preview: true }}
          className="rounded-full px-3 py-2.5 text-sm font-semibold text-link hover:underline">
          Preview as a learner
        </Link>
      </div>
    </section>
  )
}
