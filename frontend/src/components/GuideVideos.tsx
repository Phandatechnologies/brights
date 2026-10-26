import { useEffect, useState } from 'react'
import { profilesApi, type GuideVideo, type GuideVideos as Guides } from '../api/profiles'

/**
 * How-to videos from Brights' YouTube channel. Each shows a thumbnail first; the YouTube
 * player (privacy-enhanced youtube-nocookie.com) only loads when the tutor taps play.
 * Hidden entirely until at least one video is published in the admin.
 */
export function GuideVideos() {
  const [data, setData] = useState<Guides | null>(null)

  useEffect(() => {
    let cancelled = false
    profilesApi.guides().then((d) => { if (!cancelled) setData(d) }).catch(() => {})
    return () => { cancelled = true }
  }, [])

  if (!data || data.videos.length === 0) return null

  return (
    <section className="rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm sm:p-6" aria-labelledby="guides-heading">
      <h2 id="guides-heading" className="font-semibold text-slate-900">Learn to tutor with Brights</h2>
      <p className="mt-1 text-sm text-slate-600">Short videos on running great lessons, in person and online.</p>
      <ul className="mt-4 grid gap-4 sm:grid-cols-2">
        {data.videos.map((v) => <li key={v.id}><VideoCard video={v} /></li>)}
      </ul>
      {data.channel_url && (
        <a href={data.channel_url} target="_blank" rel="noreferrer"
          className="mt-4 inline-block text-sm font-semibold text-link hover:underline">
          See all our videos on YouTube →
        </a>
      )}
    </section>
  )
}

function VideoCard({ video }: { video: GuideVideo }) {
  const [playing, setPlaying] = useState(false)
  const id = encodeURIComponent(video.youtube_id)

  return (
    <div>
      <div className="relative aspect-video overflow-hidden rounded-xl bg-slate-900">
        {playing ? (
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&modestbranding=1`}
            title={video.title}
            className="absolute inset-0 h-full w-full"
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
            referrerPolicy="strict-origin-when-cross-origin"
          />
        ) : (
          <button type="button" onClick={() => setPlaying(true)} aria-label={`Play video: ${video.title}`}
            className="group absolute inset-0 h-full w-full focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/40">
            <img src={`https://i.ytimg.com/vi/${id}/hqdefault.jpg`} alt="" loading="lazy"
              className="h-full w-full object-cover opacity-90 transition group-hover:opacity-100" />
            <span aria-hidden="true" className="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand-deep/90 shadow-lg transition group-hover:scale-105">
              <svg viewBox="0 0 24 24" className="ml-1 h-6 w-6 fill-white"><path d="M8 5v14l11-7z" /></svg>
            </span>
          </button>
        )}
      </div>
      <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-pass">{video.topic_label}</p>
      <p className="font-medium text-slate-900">{video.title}</p>
      {video.description && <p className="mt-0.5 text-sm text-slate-600">{video.description}</p>}
      <a href={`https://www.youtube.com/watch?v=${id}`} target="_blank" rel="noreferrer"
        className="mt-1 inline-block text-xs font-medium text-link hover:underline">Watch on YouTube</a>
    </div>
  )
}
