import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from './api/health'

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; health: HealthResponse }
  | { kind: 'error' }

function StatusRow({ label, ok, text }: { label: string; ok: boolean; text: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
      <span className="font-medium text-slate-700">{label}</span>
      <span className={`flex items-center gap-2 text-sm font-semibold ${ok ? 'text-emerald-700' : 'text-red-700'}`}>
        <span className={`h-2.5 w-2.5 rounded-full ${ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
        {text}
      </span>
    </div>
  )
}

export default function App() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    fetchHealth()
      .then((health) => setState({ kind: 'loaded', health }))
      .catch(() => setState({ kind: 'error' }))
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <img src="/brights-logo.png" alt="Brights logo" className="h-24 w-24" />
          <h1 className="mt-4 text-3xl font-bold text-brand-navy">Brights</h1>
          <p className="mt-1 text-slate-600">Development status</p>
        </div>

        {state.kind === 'loading' && <p className="text-center text-slate-500">Checking the API…</p>}

        {state.kind === 'error' && (
          <StatusRow label="API" ok={false} text="Unreachable — is Django running?" />
        )}

        {state.kind === 'loaded' && (
          <div className="space-y-3">
            <StatusRow label="API" ok text="OK" />
            <StatusRow
              label="Database"
              ok={state.health.database === 'connected'}
              text={state.health.database === 'connected' ? 'Connected' : 'Unavailable'}
            />
          </div>
        )}

        <div className="mt-8 h-1.5 rounded-full bg-gradient-to-r from-brand-navy via-brand-teal to-brand-orange" />
      </div>
    </main>
  )
}
