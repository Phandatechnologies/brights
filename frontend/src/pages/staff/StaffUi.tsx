import type { ReactNode } from 'react'
import type { ApplicationStatus } from '../../api/staff'

/** Small building blocks shared by the staff pages. */

const STATUS_STYLES: Record<ApplicationStatus, string> = {
  draft: 'bg-slate-100 text-slate-700',
  pending: 'bg-brand-sun/25 text-heading',
  more_info: 'bg-brand-warm/15 text-[#a3400f] dark:text-[#ffb48a]',
  approved: 'bg-brand-soft/20 text-pass',
  rejected: 'bg-red-50 text-red-800',
  suspended: 'bg-red-50 text-red-800',
}

export function StatusPill({ status, label }: { status: ApplicationStatus; label: string }) {
  return <span className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]}`}>{label}</span>
}

export function Card({ title, children, className = '', action }: { title?: string; children: ReactNode; className?: string; action?: ReactNode }) {
  return (
    <section className={`rounded-2xl border border-slate-200 bg-surface p-5 shadow-sm ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-3">
          {title && <h2 className="font-semibold text-slate-900">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function ErrorList({ messages }: { messages: string[] }) {
  if (messages.length === 0) return null
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      {messages.length === 1 ? messages[0] : (
        <ul className="list-disc space-y-1 pl-5">{messages.map((m) => <li key={m}>{m}</li>)}</ul>
      )}
    </div>
  )
}
