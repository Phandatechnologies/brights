import { Link } from 'react-router'
import type { PublicTutor } from '../api/profiles'
import { formatRand, lessonModes } from '../lib/format'

/** Search result: photo first (every listed tutor has an approved photo), then the essentials. */
export function TutorCard({ tutor }: { tutor: PublicTutor }) {
  const place = tutor.teaches_in_person && tutor.area ? tutor.area.name : null
  return (
    <Link to={`/tutors/${tutor.id}`}
      className="group block h-full overflow-hidden rounded-2xl border border-slate-200 bg-surface transition hover:border-brand/50 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40">
      <div className="relative aspect-[4/3] bg-chalk">
        {tutor.photo_url ? (
          // Faces sit in the upper part of most portraits, so crop from just above centre.
          <img src={tutor.photo_url} alt="" loading="lazy"
            className="h-full w-full object-cover object-[center_30%] transition duration-300 group-hover:scale-[1.02]" />
        ) : (
          <Initials name={tutor.full_name} />
        )}
        <span className="absolute right-3 top-3 rounded-full bg-surface/95 px-3 py-1 font-display text-sm font-bold text-ink shadow">
          {formatRand(tutor.hourly_rate)}<span className="font-sans text-xs font-normal text-slate-500">/hour</span>
        </span>
      </div>
      <div className="p-4">
        <h2 className="font-display text-xl font-semibold text-heading">{tutor.full_name}</h2>
        <p className="mt-0.5 line-clamp-2 text-sm text-slate-700">{tutor.subjects.map((s) => s.name).join(', ')}</p>
        <p className="mt-2 text-xs font-semibold text-pass">✓ {tutor.verification}</p>
        <p className="mt-1 text-xs text-slate-500">
          {lessonModes(tutor.teaches_online, tutor.teaches_in_person)}{place ? ` · ${place}` : ''}
        </p>
      </div>
    </Link>
  )
}

/** Fallback only: listed tutors always have a photo, but a slow or blocked image shouldn't leave a hole. */
function Initials({ name }: { name: string }) {
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('')
  return (
    <div aria-hidden="true" className="flex h-full w-full items-center justify-center bg-brand-deep font-display text-6xl font-bold text-white/90">
      {initials}
    </div>
  )
}
