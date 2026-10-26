import { useState } from 'react'
import { getThemeChoice, setThemeChoice, type ThemeChoice } from '../lib/theme'

const OPTIONS: { value: ThemeChoice; label: string }[] = [
  { value: 'system', label: 'Automatic' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
]

/** Automatic / Light / Dark. Remembered on this device. */
export function ThemeSwitch({ compact = false }: { compact?: boolean }) {
  const [choice, setChoice] = useState<ThemeChoice>(getThemeChoice)

  function choose(next: ThemeChoice) {
    setChoice(next)
    setThemeChoice(next)
  }

  return (
    <div role="radiogroup" aria-label="Appearance"
      className={`inline-grid grid-cols-3 rounded-full border border-slate-300 bg-surface p-1 ${compact ? 'text-xs' : 'text-sm'}`}>
      {OPTIONS.map((o) => {
        const active = o.value === choice
        return (
          <button key={o.value} type="button" role="radio" aria-checked={active} onClick={() => choose(o.value)}
            className={`rounded-full font-semibold transition ${compact ? 'px-3 py-1' : 'px-4 py-1.5'} ${
              active ? 'bg-brand-deep text-white' : 'text-slate-600 hover:text-slate-900'}`}>
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
