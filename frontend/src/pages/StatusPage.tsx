import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from '../api/health'

type State = { kind: 'loading' } | { kind: 'loaded'; health: HealthResponse } | { kind: 'error' }

function StatusRow({ label, ok, text }: { label: string; ok: boolean; text: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-surface px-4 py-3">
      <span className="font-medium text-slate-700">{label}</span>
      <span className={`flex items-center gap-2 text-sm font-semibold ${ok ? 'text-emerald-700' : 'text-red-700'}`}>
        <span className={`h-2.5 w-2.5 rounded-full ${ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
        {text}
      </span>
    </div>
  )
}

/** Developer page at /status: is the API up and connected to the database? */
export function StatusPage() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    fetchHealth()
      .then((health) => setState({ kind: 'loaded', health }))
      .catch(() => setState({ kind: 'error' }))
  }, [])

  return (
    <section className="mx-auto max-w-sm px-4 py-16">
      <h1 className="mb-6 text-center text-2xl font-bold text-heading">System status</h1>
      {state.kind === 'loading' && <p className="text-center text-slate-500">Checking the API…</p>}
      {state.kind === 'error' && <StatusRow label="API" ok={false} text="Unreachable — is Django running?" />}
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
    </section>
  )
}
