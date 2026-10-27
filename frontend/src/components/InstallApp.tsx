import { useEffect, useState } from 'react'
import { installOption, promptInstall, subscribeInstall, type InstallOption } from '../lib/install'

function useInstallOption() {
  const [option, setOption] = useState<InstallOption>(installOption)
  useEffect(() => subscribeInstall(() => setOption(installOption())), [])
  return option
}

/** iOS's Share icon (a box with an arrow), so the steps match what people see. */
function ShareIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" className="inline h-4 w-4 -translate-y-px">
      <path fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
        d="M10 12.5V2.5M6.5 6 10 2.5 13.5 6M7 9H5.5A1.5 1.5 0 0 0 4 10.5v6A1.5 1.5 0 0 0 5.5 18h9a1.5 1.5 0 0 0 1.5-1.5v-6A1.5 1.5 0 0 0 14.5 9H13" />
    </svg>
  )
}

/**
 * "Get the Brights app" card. Shows an Install button where the browser supports it,
 * the Add to Home Screen steps on iPhone, and nothing once Brights is installed.
 */
export function InstallApp({ compact = false }: { compact?: boolean }) {
  const option = useInstallOption()
  const [showSteps, setShowSteps] = useState(false)
  if (option === 'none') return null

  const button = 'rounded-full bg-brand-deep px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/30'

  const steps = (
    <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-slate-700">
      <li>Tap the <strong>Share</strong> button <ShareIcon /> in your browser.</li>
      <li>Scroll down and tap <strong>Add to Home Screen</strong>.</li>
      <li>Tap <strong>Add</strong>. Brights appears with your other apps.</li>
    </ol>
  )

  if (compact) {
    return option === 'prompt' ? (
      <button type="button" onClick={promptInstall} className={button}>Install the app</button>
    ) : (
      <div>
        <button type="button" onClick={() => setShowSteps((s) => !s)} aria-expanded={showSteps} className={button}>
          Add Brights to your Home Screen
        </button>
        {showSteps && steps}
      </div>
    )
  }

  return (
    <div className="mt-6 flex gap-4 rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm">
      <img src="/brights-logo.svg" alt="" width="48" height="48" className="h-12 w-12 shrink-0" />
      <div className="min-w-0">
        <h2 className="font-semibold text-slate-900">Get the Brights app</h2>
        <p className="mt-1 text-sm text-slate-600">Open Brights from your home screen, full screen, like any other app. It's free and uses almost no space on your phone.</p>
        {option === 'prompt' ? (
          <button type="button" onClick={promptInstall} className={`mt-3 ${button}`}>Install the app</button>
        ) : (
          steps
        )}
      </div>
    </div>
  )
}
