import type { ReactNode } from 'react'

/** Shared frame for the login and sign-up pages. */
export function AuthCard({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-10 sm:py-16">
      <h1 className="text-2xl font-bold text-heading">{title}</h1>
      <p className="mt-1 text-slate-600">{subtitle}</p>
      <div className="mt-6 rounded-2xl border border-slate-200 bg-surface p-6 shadow-sm">{children}</div>
    </div>
  )
}
