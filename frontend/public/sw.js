// Brights service worker. It lets phones install Brights as an app, and shows a
// friendly "you're offline" page instead of the browser's error when there's no signal.
// It deliberately does NOT cache pages, logins or API answers: Brights always shows live data.
const CACHE = 'brights-offline-v1'
const OFFLINE_FILES = ['/offline.html', '/offline.css', '/brights-logo.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(OFFLINE_FILES)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (url.origin !== self.location.origin || request.method !== 'GET') return // the browser handles it as normal

  // Opening a page: go to the network; only if that fails, show the offline page.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/offline.html')))
    return
  }
  // The offline page's own files.
  if (OFFLINE_FILES.includes(url.pathname)) {
    event.respondWith(fetch(request).catch(() => caches.match(url.pathname)))
  }
})
