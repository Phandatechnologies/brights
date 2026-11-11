import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../../api/client'
import { videoApi, type Video, type VideoInput } from '../../api/staff'
import { Card, ErrorList } from './StaffUi'

type Topic = { value: string; label: string }

/** /staff/videos — the how-to videos on every tutor's Home. Drafts stay hidden until published. */
export function VideosPage() {
  const [videos, setVideos] = useState<Video[] | null>(null)
  const [topics, setTopics] = useState<Topic[]>([])
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)

  const load = useCallback(() => {
    videoApi.list()
      .then((d) => { setVideos(d.videos); setTopics(d.topics); setError('') })
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load videos.'))
  }, [])
  useEffect(load, [load])

  async function move(index: number, step: -1 | 1) {
    if (!videos) return
    const list = [...videos]
    const [moved] = list.splice(index, 1)
    list.splice(index + step, 0, moved)
    setVideos(list)
    // Renumber 10, 20, 30… and save only the ones that changed.
    try {
      await Promise.all(list.map((v, i) => ((i + 1) * 10 !== v.order ? videoApi.update(v.id, { order: (i + 1) * 10 }) : null)))
    } catch {
      setError('Could not save the new order. Please try again.')
    }
    load()
  }

  return (
    <section className="mx-auto max-w-4xl px-4 py-8 sm:py-10">
      <Link to="/staff/more" className="text-sm font-medium text-link hover:underline">← More</Link>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-heading">How-to videos</h1>
          <p className="mt-1 text-slate-600">Shown on every tutor's Home, in this order. Upload to YouTube first, then paste the link here.</p>
        </div>
        {!adding && (
          <button type="button" onClick={() => { setAdding(true); setEditing(null) }}
            className="rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand">+ Add a video</button>
        )}
      </div>

      {error && <div className="mt-6"><ErrorList messages={[error]} /></div>}
      {adding && (
        <Card title="Add a video" className="mt-6">
          <VideoForm topics={topics} onCancel={() => setAdding(false)}
            onSave={async (input) => { await videoApi.add(input); setAdding(false); load() }} saveLabel="Add video" />
        </Card>
      )}

      <div className="mt-6">
        {!videos && !error && <p className="text-slate-500">Loading…</p>}
        {videos && videos.length === 0 && !adding && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            No videos yet. The videos section stays hidden on tutors’ Home until you publish one.
          </div>
        )}
        {videos && videos.length > 0 && (
          <ol className="space-y-3">
            {videos.map((video, index) => (
              <li key={video.id} className="rounded-2xl border border-slate-200 bg-surface p-4 shadow-sm">
                {editing === video.id ? (
                  <VideoForm topics={topics} initial={video} saveLabel="Save changes" onCancel={() => setEditing(null)}
                    onSave={async (input) => { await videoApi.update(video.id, input); setEditing(null); load() }} />
                ) : (
                  <VideoRow video={video} first={index === 0} last={index === videos.length - 1}
                    onMove={(step) => move(index, step)} onEdit={() => { setEditing(video.id); setAdding(false) }} onChanged={load} />
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  )
}

function VideoRow({ video, first, last, onMove, onEdit, onChanged }: {
  video: Video; first: boolean; last: boolean; onMove: (step: -1 | 1) => void; onEdit: () => void; onChanged: () => void
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [busy, setBusy] = useState(false)
  const small = 'rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-brand disabled:opacity-40'

  async function togglePublished() {
    setBusy(true)
    try { await videoApi.update(video.id, { is_published: !video.is_published }) } finally { setBusy(false); onChanged() }
  }
  async function remove() {
    setBusy(true)
    try { await videoApi.remove(video.id) } finally { setBusy(false); onChanged() }
  }

  return (
    <div className="flex flex-col gap-4 sm:flex-row">
      <a href={`https://www.youtube.com/watch?v=${video.youtube_id}`} target="_blank" rel="noopener" className="shrink-0">
        <img src={`https://i.ytimg.com/vi/${video.youtube_id}/mqdefault.jpg`} alt={`Thumbnail for ${video.title}`} loading="lazy"
          className="aspect-video w-full rounded-lg bg-chalk object-cover sm:w-48" />
      </a>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${video.is_published ? 'bg-brand-soft/20 text-pass' : 'bg-slate-100 text-slate-700'}`}>
            {video.is_published ? 'Published' : 'Draft (tutors can’t see it)'}
          </span>
          <span className="text-xs text-slate-500">{video.topic_label}</span>
        </div>
        <p className="mt-1 font-semibold text-slate-900">{video.title}</p>
        {video.description && <p className="mt-1 text-sm text-slate-600">{video.description}</p>}
        {confirmDelete ? (
          <div role="alertdialog" aria-label="Confirm" className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-slate-800">Remove “{video.title}” from Brights? It stays on YouTube.</p>
            <div className="mt-2 flex gap-2">
              <button type="button" disabled={busy} onClick={remove} className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700">Yes, remove</button>
              <button type="button" onClick={() => setConfirmDelete(false)} className={small}>Cancel</button>
            </div>
          </div>
        ) : (
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" disabled={busy} onClick={togglePublished}
              className={video.is_published ? small : 'rounded-lg bg-brand-deep px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand disabled:opacity-40'}>
              {video.is_published ? 'Unpublish' : 'Publish'}
            </button>
            <button type="button" onClick={onEdit} className={small}>Edit</button>
            <button type="button" disabled={first} onClick={() => onMove(-1)} className={small} aria-label={`Move ${video.title} up`}>↑</button>
            <button type="button" disabled={last} onClick={() => onMove(1)} className={small} aria-label={`Move ${video.title} down`}>↓</button>
            <button type="button" onClick={() => setConfirmDelete(true)} className="rounded-lg px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50">Remove</button>
          </div>
        )}
      </div>
    </div>
  )
}

function VideoForm({ topics, initial, saveLabel, onSave, onCancel }: {
  topics: Topic[]; initial?: Video; saveLabel: string; onSave: (input: VideoInput) => Promise<void>; onCancel: () => void
}) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [topic, setTopic] = useState(initial?.topic ?? topics[0]?.value ?? 'getting_started')
  const [link, setLink] = useState(initial ? `https://youtu.be/${initial.youtube_id}` : '')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    try {
      await onSave({ title, description, topic, youtube_id: link })
    } catch (e) {
      setErrors(e instanceof ApiError ? e.fieldErrors : { non_field_errors: ['Something went wrong. Please try again.'] })
    } finally {
      setBusy(false)
    }
  }

  const field = 'mt-1 block w-full rounded-lg border border-slate-300 bg-surface px-3 py-2.5 text-slate-900 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20'
  const fieldError = (name: string) => errors[name]?.[0] && <p className="mt-1 text-sm text-red-700">{errors[name][0]}</p>

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <ErrorList messages={errors.non_field_errors ?? []} />
      <div>
        <label htmlFor="video-link" className="block text-sm font-medium text-slate-700">YouTube link</label>
        <input id="video-link" value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://youtu.be/…" className={field} />
        {fieldError('youtube_id')}
      </div>
      <div>
        <label htmlFor="video-title" className="block text-sm font-medium text-slate-700">Title</label>
        <input id="video-title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Your first online lesson" className={field} />
        {fieldError('title')}
      </div>
      <div>
        <label htmlFor="video-description" className="block text-sm font-medium text-slate-700">Short description (optional)</label>
        <input id="video-description" value={description} maxLength={300} onChange={(e) => setDescription(e.target.value)} className={field} />
        {fieldError('description')}
      </div>
      <div>
        <label htmlFor="video-topic" className="block text-sm font-medium text-slate-700">Topic</label>
        <select id="video-topic" value={topic} onChange={(e) => setTopic(e.target.value)} className={field}>
          {topics.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>
      {!initial && <p className="text-sm text-slate-500">New videos start as drafts. Publish when the video is public on YouTube.</p>}
      <div className="flex flex-wrap gap-3">
        <button disabled={busy} className="rounded-full bg-brand-deep px-5 py-2.5 font-semibold text-white hover:bg-brand disabled:opacity-50">{busy ? 'Saving…' : saveLabel}</button>
        <button type="button" onClick={onCancel} className="rounded-full border border-slate-300 px-5 py-2.5 font-semibold text-slate-700">Cancel</button>
      </div>
    </form>
  )
}
