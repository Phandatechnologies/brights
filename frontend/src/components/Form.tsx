import { useState, type InputHTMLAttributes, type ReactNode } from 'react'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  name: string
  errors?: string[]
  hint?: ReactNode
  /** Optional element shown inside the right edge of the input (e.g. a show-password button). */
  trailing?: ReactNode
}

export function TextField({ label, name, errors, hint, trailing, className = '', ...props }: TextFieldProps) {
  const hasError = Boolean(errors?.length)
  const describedBy = hasError ? `${name}-error` : hint ? `${name}-hint` : undefined
  return (
    <div className={className}>
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <input
          id={name}
          name={name}
          aria-invalid={hasError}
          aria-describedby={describedBy}
          className={`block w-full rounded-lg border bg-surface px-3 py-2.5 text-slate-900 shadow-sm outline-none transition focus:ring-2 ${
            trailing ? 'pr-12' : ''
          } ${
            hasError
              ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
              : 'border-slate-300 focus:border-brand-blue focus:ring-brand-blue/20'
          }`}
          {...props}
        />
        {trailing && <div className="absolute inset-y-0 right-0 flex items-center pr-1.5">{trailing}</div>}
      </div>
      {hasError ? (
        <FieldError id={`${name}-error`} messages={errors!} />
      ) : (
        hint && <p id={`${name}-hint`} className="mt-1 text-sm text-slate-500">{hint}</p>
      )}
    </div>
  )
}

type PasswordFieldProps = Omit<TextFieldProps, 'type' | 'trailing'>

/**
 * A password input with a show/hide toggle.
 * The toggle is type="button" so clicking it never submits the form.
 */
export function PasswordField(props: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)
  return (
    <TextField
      {...props}
      type={visible ? 'text' : 'password'}
      autoCapitalize="none"
      autoCorrect="off"
      spellCheck={false}
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
          aria-controls={props.name}
          className="rounded-md p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-blue/30"
        >
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      }
    />
  )
}

function EyeIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeOffIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M10.7 5.1A10.4 10.4 0 0 1 12 5c6.4 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.2" />
      <path d="M6.6 6.6C3.9 8.4 2 12 2 12s3.6 7 10 7a9.7 9.7 0 0 0 5.4-1.6" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      <path d="m2 2 20 20" />
    </svg>
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
