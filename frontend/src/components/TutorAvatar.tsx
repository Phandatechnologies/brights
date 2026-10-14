/** Approved photo if there is one, otherwise the tutor's initials. */
export function TutorAvatar({ name, photoUrl, size = 'md' }: { name: string; photoUrl: string | null; size?: 'md' | 'lg' }) {
  const box = size === 'lg' ? 'h-28 w-28 text-3xl' : 'h-14 w-14 text-lg'
  if (photoUrl) {
    return <img src={photoUrl} alt="" className={`${box} shrink-0 rounded-full object-cover`} />
  }
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('')
  return (
    <span aria-hidden="true" className={`${box} flex shrink-0 items-center justify-center rounded-full bg-brand-navy/10 font-display font-semibold text-brand-navy`}>
      {initials}
    </span>
  )
}
