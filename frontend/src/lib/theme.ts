/**
 * Light / dark mode. "system" follows the phone or computer setting.
 * public/theme-init.js applies the saved choice before the page first draws;
 * this module handles changes after that.
 */
export type ThemeChoice = 'system' | 'light' | 'dark'

const KEY = 'brights-theme'
const darkQuery = () => window.matchMedia('(prefers-color-scheme: dark)')

export function getThemeChoice(): ThemeChoice {
  try {
    const saved = localStorage.getItem(KEY)
    return saved === 'light' || saved === 'dark' ? saved : 'system'
  } catch {
    return 'system' // storage blocked (private mode on some phones)
  }
}

function apply(choice: ThemeChoice) {
  const dark = choice === 'dark' || (choice === 'system' && darkQuery().matches)
  document.documentElement.classList.toggle('dark', dark)
  // Colour of the phone's browser bar.
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute('content', dark ? '#0b1120' : '#ffffff'))
}

export function setThemeChoice(choice: ThemeChoice) {
  try {
    if (choice === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, choice)
  } catch {
    // Can't remember it, but still apply it for this visit.
  }
  apply(choice)
}

/** Follow the device when it switches between light and dark (e.g. at sunset). */
export function watchSystemTheme() {
  darkQuery().addEventListener('change', () => {
    if (getThemeChoice() === 'system') apply('system')
  })
}
