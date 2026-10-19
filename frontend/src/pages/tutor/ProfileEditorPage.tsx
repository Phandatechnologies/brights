import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { ApiError, type FieldErrors } from '../../api/client'
import { profilesApi, type Area, type OwnProfile, type Province } from '../../api/profiles'
import { tutorApi, type TutorApplication } from '../../api/tutor'
import { useAuth } from '../../auth/AuthContext'
import { FieldError, FormAlert, TextField } from '../../components/Form'
import { FullPageSpinner } from '../../components/FullPageSpinner'
import { SearchSelect } from '../../components/SearchSelect'

const MAX_BIO = 1000
const PHOTO_COPY: Record<string, string> = {
  pending: "Waiting for approval. You'll appear in search once our team approves it (usually within a day).",
  approved: 'Approved and showing on your profile.',
  rejected: 'Not approved. Please upload a different photo.',
}

type Loaded = { profile: OwnProfile; application: TutorApplication | null; provinces: Province[]; areas: Area[] }

/** /tutor/profile — the tutor's public profile editor. */
export function ProfileEditorPage() {
  const { user } = useAuth()
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const isTutor = user?.account_type === 'tutor'

  useEffect(() => {
    if (!isTutor) return
    let cancelled = false
    Promise.all([profilesApi.ownProfile(), tutorApi.getApplication(), profilesApi.areas()])
      .then(([profile, application, places]) => {
        if (!cancelled) setLoaded({ profile, application, provinces: places.provinces, areas: places.areas })
      })
      .catch(() => { if (!cancelled) setLoadError('Could not load your profile.') })
    return () => { cancelled = true }
  }, [isTutor])

  if (!isTutor) {
    return <Shell><p className="text-slate-700">Only tutor accounts have a tutor profile.</p></Shell>
  }
  if (loadError) return <Shell><FormAlert message={loadError} /></Shell>
  if (!loaded) return <FullPageSpinner />

  return (
    <Shell>
      <ListingBanner profile={loaded.profile} application={loaded.application} />
      <ProfileForm loaded={loaded} onSaved={(profile) => setLoaded({ ...loaded, profile })} />
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
      <h1 className="text-3xl font-bold tracking-[-0.02em] text-heading sm:text-4xl">Your tutor profile</h1>
      <div className="mt-8">{children}</div>
    </section>
  )
}

function ListingBanner({ profile, application }: { profile: OwnProfile; application: TutorApplication | null }) {
  if (profile.is_listed) {
    return (
      <div role="status" className="rounded-xl border border-brand-teal/50 bg-brand-teal/10 p-5">
        <p className="font-semibold text-heading">Your profile is live in search</p>
        <p className="mt-1 text-slate-700">Learners and parents can find you for your approved subjects.</p>
        <Link to={`/tutors/${profile.id}`} state={{ preview: true }} className="mt-3 inline-block font-semibold text-link hover:underline">
          Preview as a learner →
        </Link>
      </div>
    )
  }
  const approved = application?.status === 'approved'
  if (approved && !profile.accepting_learners) {
    return (
      <div role="status" className="rounded-xl border border-slate-200 bg-chalk p-5">
        <p className="font-semibold text-heading">You've paused new learners</p>
        <p className="mt-1 text-slate-700">
          You're hidden from search until you switch "Taking new learners" back on from your{' '}
          <Link to="/dashboard" className="font-medium text-link hover:underline">Home</Link>.
        </p>
      </div>
    )
  }
  return (
    <div role="status" className="rounded-xl border border-slate-200 bg-chalk p-5">
      <p className="font-semibold text-heading">Your profile isn't in search yet</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">
        {!approved && (
          <li>
            Your tutor application needs to be approved.{' '}
            <Link to="/tutor/apply" className="font-medium text-link hover:underline">Check your application</Link>
          </li>
        )}
        {profile.missing_fields.map((item) => <li key={item}>{item}</li>)}
        {profile.photo_status === 'pending' && <li>Your photo is waiting for approval</li>}
      </ul>
    </div>
  )
}

function ProfileForm({ loaded, onSaved }: { loaded: Loaded; onSaved: (p: OwnProfile) => void }) {
  const { profile, provinces, areas } = loaded
  const [bio, setBio] = useState(profile.bio)
  const [rate, setRate] = useState(profile.hourly_rate ? String(profile.hourly_rate) : '')
  const [online, setOnline] = useState(profile.teaches_online)
  const [inPerson, setInPerson] = useState(profile.teaches_in_person)
  const [province, setProvince] = useState(profile.area_detail?.province ?? 'gauteng')
  const [area, setArea] = useState(profile.area ? String(profile.area) : '')
  const [availability, setAvailability] = useState(profile.availability)
  const [whatsapp, setWhatsapp] = useState(profile.whatsapp_number)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    setSaved(false)
    try {
      const updated = await profilesApi.updateOwnProfile({
        bio,
        hourly_rate: rate ? Number(rate) : null,
        teaches_online: online,
        teaches_in_person: inPerson,
        area: inPerson && area ? Number(area) : null,
        availability,
        whatsapp_number: whatsapp,
      })
      onSaved(updated)
      setWhatsapp(updated.whatsapp_number)
      setSaved(true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
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
    <div className="mt-8 space-y-10">
      <PhotoSection profile={profile} onChange={onSaved} />

      <form onSubmit={save} className="space-y-6" noValidate>
        {saved && <p role="status" className="rounded-lg bg-brand-teal/10 px-4 py-3 text-sm font-medium text-pass">Profile saved.</p>}
        <FormAlert message={error} />

        <div>
          <label htmlFor="bio" className="mb-1 block text-sm font-medium text-slate-700">About you</label>
          <textarea id="bio" rows={6} value={bio} maxLength={MAX_BIO} onChange={(e) => setBio(e.target.value)}
            aria-describedby="bio-hint"
            placeholder="How you teach, what learners can expect, and anything that makes you a good fit."
            className="block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 leading-relaxed outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
          <p id="bio-hint" className="mt-1 text-right text-xs text-slate-500">{bio.length} / {MAX_BIO}</p>
          <FieldError messages={errors.bio} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Hourly rate (R)" name="hourly_rate" inputMode="numeric" value={rate}
            hint="Between R50 and R2,000." errors={errors.hourly_rate}
            onChange={(e) => setRate(e.target.value.replace(/[^0-9]/g, '').slice(0, 4))} />
          <TextField label="WhatsApp number" name="whatsapp_number" type="tel" autoComplete="tel" value={whatsapp}
            placeholder="082 123 4567" errors={errors.whatsapp_number}
            hint="Never shown publicly. Only shared when you're contacted through Brights."
            onChange={(e) => setWhatsapp(e.target.value)} />
        </div>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">How do you teach?</legend>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2"><input type="checkbox" checked={online} onChange={(e) => setOnline(e.target.checked)} className="accent-brand-blue" /> Online</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={inPerson} onChange={(e) => setInPerson(e.target.checked)} className="accent-brand-blue" /> In person</label>
          </div>
          <p className="mt-1 text-sm text-slate-500">Online tutors can be found anywhere in South Africa.</p>
        </fieldset>

        {inPerson && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="province" className="mb-1 block text-sm font-medium text-slate-700">Province</label>
              <select id="province" value={province} onChange={(e) => { setProvince(e.target.value); setArea('') }}
                className="w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5">
                {provinces.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="area" className="mb-1 block text-sm font-medium text-slate-700">Area</label>
              <SearchSelect id="area" value={area} placeholder="Search areas, e.g. Soshanguve"
                options={areas.filter((a) => a.province === province).map((a) => ({ value: String(a.id), label: a.name }))}
                onChange={setArea} />
              <p className="mt-1 text-sm text-slate-500">A general area only. Never share your address.</p>
              <FieldError messages={errors.area} />
            </div>
          </div>
        )}

        <TextField label="Availability (optional)" name="availability" value={availability} maxLength={300}
          placeholder="e.g. Weekday afternoons and Saturday mornings" errors={errors.availability}
          onChange={(e) => setAvailability(e.target.value)} />

        <div className="flex justify-end border-t border-slate-200 pt-6">
          <button type="submit" disabled={busy}
            className="rounded-full bg-brand-navy px-6 py-3 font-semibold text-white transition hover:bg-brand-blue disabled:opacity-60">
            {busy ? 'Saving…' : 'Save profile'}
          </button>
        </div>
      </form>
    </div>
  )
}

function PhotoSection({ profile, onChange }: { profile: OwnProfile; onChange: (p: OwnProfile) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function upload(file: File | undefined) {
    if (!file) return
    setError(null)
    if (file.size > 3 * 1024 * 1024) return setError('Photos must be 3 MB or smaller.')
    setBusy(true)
    try {
      onChange(await profilesApi.uploadPhoto(file))
    } catch (err) {
      setError(err instanceof ApiError ? (err.fieldErrors.photo?.[0] ?? err.message) : 'Upload failed.')
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  async function remove() {
    setBusy(true)
    setError(null)
    try {
      await profilesApi.deletePhoto()
      onChange(await profilesApi.ownProfile())
    } catch {
      setError('Could not remove the photo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-labelledby="photo-heading" className="flex flex-col gap-5 sm:flex-row sm:items-center">
      {profile.photo_url ? (
        <img src={profile.photo_url} alt="Your profile photo" className="h-28 w-28 rounded-full object-cover" />
      ) : (
        <span className="flex h-28 w-28 items-center justify-center rounded-full bg-brand-navy/10 text-sm text-slate-500">No photo</span>
      )}
      <div className="flex-1">
        <h2 id="photo-heading" className="font-sans text-lg font-semibold text-heading">Profile photo (required)</h2>
        <p className="mt-1 text-sm text-slate-600">
          {profile.photo_status === 'none'
            ? 'Learners see your photo first, and you need one to appear in search. Our team approves every photo.'
            : PHOTO_COPY[profile.photo_status]}
        </p>
        <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-slate-500">
          <li>Just you, head and shoulders, facing the camera</li>
          <li>Good light, no sunglasses, no filters or group photos</li>
        </ul>
        {profile.photo_status === 'approved' && (
          <p className="mt-2 text-xs text-slate-500">
            Replacing or removing your photo hides you from search until a new photo is approved.
          </p>
        )}
        {profile.photo_status === 'rejected' && profile.photo_note && (
          <p className="mt-1 text-sm text-below">Reason: {profile.photo_note}</p>
        )}
        <div className="mt-3 flex flex-wrap gap-3">
          <input ref={input} id="photo-input" type="file" accept="image/jpeg,image/png" className="peer sr-only"
            onChange={(e) => upload(e.target.files?.[0])} disabled={busy} />
          <label htmlFor="photo-input"
            className={`cursor-pointer rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-heading hover:bg-slate-50 peer-focus-visible:ring-2 peer-focus-visible:ring-brand-blue/40 ${busy ? 'pointer-events-none opacity-60' : ''}`}>
            {busy ? 'Uploading…' : profile.photo_url ? 'Replace photo' : 'Upload photo'}
          </label>
          {profile.photo_url && (
            <button type="button" onClick={remove} disabled={busy} className="rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 hover:text-red-700">
              Remove
            </button>
          )}
        </div>
        {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
      </div>
    </section>
  )
}
