import type { InputHTMLAttributes, ReactNode } from 'react'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  name: string
  errors?: string[]
  hint?: ReactNode
}

export function TextField({ label, name, errors, hint, className = '', ...props }: TextFieldProps) {
  const hasError = Boolean(errors?.length)
  const describedBy = hasError ? `${name}-error` : hint ? `${name}-hint` : undefined
  return (
    <div className={className}>
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={name}
        name={name}
        aria-invalid={hasError}
        aria-describedby={describedBy}
        className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-slate-900 shadow-sm outline-none transition focus:ring-2 ${
          hasError
            ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
            : 'border-slate-300 focus:border-brand-blue focus:ring-brand-blue/20'
        }`}
        {...props}
      />
      {hasError ? (
        <FieldError id={`${name}-error`} messages={errors!} />
      ) : (
        hint && <p id={`${name}-hint`} className="mt-1 text-sm text-slate-500">{hint}</p>
      )}
    </div>
  )
}

export function FieldError({ id, messages }: { id?: string; messages?: string[] }) {
  if (!messages?.length) return null
  return (
    <p id={id} className="mt-1 text-sm text-red-700">
      {messages.join(' ')}
    </p>
  )
}

export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  )
}

export function SubmitButton({ busy, children }: { busy: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full rounded-lg bg-brand-navy px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/40 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {busy ? 'Please wait…' : children}
    </button>
  )
}
