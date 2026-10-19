// Runs before the page is drawn, so dark mode never flashes white first.
// It's a separate file (not inline) because the site's security policy blocks inline scripts.
(function () {
  var choice = null
  try { choice = localStorage.getItem('brights-theme') } catch { /* storage blocked: follow the device */ }
  var dark = choice === 'dark' || (choice !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
  // Browser bar colour on phones (the meta tags come before this script in <head>).
  var metas = document.querySelectorAll('meta[name="theme-color"]')
  for (var i = 0; i < metas.length; i++) metas[i].setAttribute('content', dark ? '#0b1120' : '#ffffff')
})()
