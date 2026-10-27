/**
 * Installing Brights as a phone app.
 * - Android (Chrome, Samsung Internet, Edge): the browser offers an install prompt we can show from a button.
 * - iPhone/iPad: there's no prompt; people use Share → "Add to Home Screen", so we show those steps.
 * - Already opened as the installed app: nothing to offer.
 */

/** Chrome's install-prompt event (not in TypeScript's built-in types yet). */
type InstallPromptEvent = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }> }

let promptEvent: InstallPromptEvent | null = null
let installed = false
const listeners = new Set<() => void>()
const notify = () => listeners.forEach((listener) => listener())

/** Call once at start-up: the browser sends the prompt event early, often before any page has drawn. */
export function listenForInstallPrompt() {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault() // we show our own button instead of the browser's mini bar
    promptEvent = event as InstallPromptEvent
    notify()
  })
  window.addEventListener('appinstalled', () => {
    installed = true
    promptEvent = null
    notify()
  })
}

/** Registers the service worker (production only: in development it would get in the way of live reloading). */
export function registerServiceWorker() {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => { /* the site works fine without it */ })
  })
}

export function subscribeInstall(listener: () => void) {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export function isRunningAsApp() {
  return window.matchMedia('(display-mode: standalone)').matches || (navigator as Navigator & { standalone?: boolean }).standalone === true
}

export function isAppleMobile() {
  const ua = navigator.userAgent
  // iPadOS reports itself as a Mac, so also check for a touch screen.
  return /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)
}

export type InstallOption = 'prompt' | 'apple' | 'none'

export function installOption(): InstallOption {
  if (installed || isRunningAsApp()) return 'none'
  if (promptEvent) return 'prompt'
  if (isAppleMobile()) return 'apple'
  return 'none'
}

/** Shows the browser's install dialog. Returns true if the person said yes. */
export async function promptInstall() {
  if (!promptEvent) return false
  const event = promptEvent
  promptEvent = null // a prompt can only be used once
  await event.prompt()
  const { outcome } = await event.userChoice
  notify()
  return outcome === 'accepted'
}
