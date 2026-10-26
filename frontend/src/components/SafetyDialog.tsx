import { useEffect, useRef, useState } from 'react'

/**
 * Shown once to learners under 18 before they contact their first tutor.
 * Uses the native <dialog> element, which handles focus and the Escape key.
 */
export function SafetyDialog({ open, busy, onConfirm, onCancel }: {
  open: boolean
  busy: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog ref={ref} onCancel={onCancel} aria-labelledby="safety-title"
      className="m-auto w-[min(32rem,calc(100%-2rem))] rounded-2xl p-0 backdrop:bg-brand-deep/40">
      <div className="p-6 sm:p-7">
        <h2 id="safety-title" className="text-2xl font-bold text-heading">Before you message a tutor</h2>
        <p className="mt-2 text-slate-700">Because you're under 18, please read this first.</p>
        <ul className="mt-4 space-y-3 text-slate-800">
          <li><strong>Tell a parent or guardian</strong> which tutor you're contacting, and show them the chat if they ask.</li>
          <li><strong>Keep chats about schoolwork.</strong> A tutor should never ask for photos, personal secrets, or to keep things from your parents.</li>
          <li><strong>Meet safely.</strong> In-person lessons should be at home with an adult nearby, or in a public place like a library.</li>
          <li><strong>Never share passwords</strong> or send money without your parent or guardian's agreement.</li>
          <li>If anything makes you uncomfortable, <strong>stop replying and tell a trusted adult</strong>. You can also report the tutor to Brights.</li>
        </ul>
        <label className="mt-5 flex items-start gap-2 text-slate-800">
          <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} className="mt-1 accent-brand" />
          I've read this and I'll follow it.
        </label>
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button type="button" onClick={onCancel} className="rounded-full px-5 py-2.5 font-medium text-slate-700 hover:bg-slate-100">
            Not now
          </button>
          <button type="button" onClick={onConfirm} disabled={!checked || busy}
            className="rounded-full bg-brand-deep px-6 py-2.5 font-semibold text-white transition hover:bg-brand disabled:cursor-not-allowed disabled:opacity-50">
            {busy ? 'Please wait…' : 'Continue'}
          </button>
        </div>
      </div>
    </dialog>
  )
}
