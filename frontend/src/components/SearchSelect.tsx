import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'

export type SelectOption = { value: string; label: string }

type Props = {
  id: string
  options: SelectOption[]
  value: string
  onChange: (value: string) => void
  /** Text shown when nothing is chosen, e.g. "Choose a subject…". */
  placeholder?: string
  /** If given, adds a first option that clears the choice, e.g. "Any subject". */
  emptyLabel?: string
  /** Clear the box after a pick (for "add another" pickers). */
  resetOnSelect?: boolean
  className?: string
}

/** Lower-case and strip accents so "eish" finds "Éish" and "isizulu" finds "isiZulu". */
function normalise(text: string) {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

/**
 * A dropdown you can type into to filter (an accessible "combobox").
 * Keyboard: type to filter, ↑/↓ to move, Enter to choose, Esc to close.
 */
export function SearchSelect({ id, options, value, onChange, placeholder, emptyLabel, resetOnSelect, className }: Props) {
  const listId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)

  const selected = options.find((o) => o.value === value)
  const allOptions = useMemo(
    () => (emptyLabel ? [{ value: '', label: emptyLabel }, ...options] : options),
    [options, emptyLabel],
  )
  const matches = useMemo(() => {
    const words = normalise(query).split(/\s+/).filter(Boolean)
    if (words.length === 0) return allOptions
    // Every typed word must appear somewhere in the name, in any order.
    return options.filter((o) => {
      const label = normalise(o.label)
      return words.every((w) => label.includes(w))
    })
  }, [query, options, allOptions])

  // Keep the highlighted option visible while scrolling with the keyboard.
  useEffect(() => {
    if (!open) return
    listRef.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active, open])

  function openList() {
    setQuery('')
    const index = allOptions.findIndex((o) => o.value === value)
    setActive(index >= 0 ? index : 0)
    setOpen(true)
  }

  function choose(option: SelectOption) {
    onChange(option.value)
    setOpen(false)
    setQuery('')
    if (resetOnSelect) inputRef.current?.focus()
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      if (!open) return openList()
      const step = event.key === 'ArrowDown' ? 1 : -1
      setActive((i) => Math.min(Math.max(i + step, 0), Math.max(matches.length - 1, 0)))
    } else if (event.key === 'Enter') {
      if (open && matches[active]) {
        event.preventDefault() // don't submit the surrounding form
        choose(matches[active])
      }
    } else if (event.key === 'Escape') {
      if (open) {
        event.preventDefault()
        setOpen(false)
        setQuery('')
      }
    }
  }

  // Closed: show the chosen name. Open: show what the person is typing.
  const shown = open ? query : resetOnSelect ? '' : (selected?.label ?? '')

  return (
    <div className={`relative ${className ?? ''}`}>
      <input
        ref={inputRef}
        id={id}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && matches[active] ? `${listId}-${active}` : undefined}
        autoComplete="off"
        spellCheck={false}
        value={shown}
        placeholder={open ? 'Type to search…' : (emptyLabel ?? placeholder)}
        onFocus={openList}
        onClick={() => { if (!open) openList() }}
        onBlur={() => { setOpen(false); setQuery('') }}
        onChange={(e) => { setQuery(e.target.value); setActive(0); setOpen(true) }}
        onKeyDown={onKeyDown}
        className="w-full rounded-lg border border-slate-300 bg-surface py-2.5 pl-3 pr-9 text-slate-900 outline-none placeholder:text-slate-500 focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20"
      />
      <svg aria-hidden="true" viewBox="0 0 20 20" className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400">
        <path fill="currentColor" d="M8.5 3a5.5 5.5 0 0 1 4.38 8.83l3.65 3.64a.75.75 0 1 1-1.06 1.06l-3.64-3.65A5.5 5.5 0 1 1 8.5 3Zm0 1.5a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />
      </svg>
      {open && (
        <ul
          ref={listRef}
          id={listId}
          role="listbox"
          className="absolute z-30 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-surface py-1 shadow-lg"
        >
          {matches.length === 0 && <li className="px-3 py-2 text-sm text-slate-500">No matches for “{query}”</li>}
          {matches.map((option, index) => (
            <li
              key={option.value || '__empty'}
              id={`${listId}-${index}`}
              data-index={index}
              role="option"
              aria-selected={option.value === value}
              // mousedown, not click: runs before the input's blur closes the list
              onMouseDown={(e) => { e.preventDefault(); choose(option) }}
              onMouseEnter={() => setActive(index)}
              className={`cursor-pointer px-3 py-2 text-sm ${index === active ? 'bg-brand-blue/10 text-heading' : 'text-slate-800'} ${
                option.value === value ? 'font-semibold' : ''
              } ${option.value === '' ? 'text-slate-500' : ''}`}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
