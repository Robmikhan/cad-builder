import { useState, useEffect } from 'react'
import { fetchModels } from '../api'
import {
  Cpu, CheckCircle2, XCircle, Loader2, RefreshCw,
  HardDrive, AlertCircle
} from 'lucide-react'

export default function ModelsPage() {
  const [models, setModels] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchModels()
      setModels(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Models</h1>
          <p className="text-text-muted text-sm mt-1">Installed AI models and their status</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-lighter text-text-muted hover:text-text text-sm font-medium transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 mb-6 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {loading && !models ? (
        <div className="flex items-center justify-center py-16 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading models...
        </div>
      ) : models ? (
        <div className="space-y-4">
          {Array.isArray(models) ? (
            models.map((model, i) => (
              <ModelCard key={i} model={model} />
            ))
          ) : typeof models === 'object' ? (
            Object.entries(models).map(([key, val]) => (
              <div key={key} className="bg-surface-light border border-border rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <Cpu className="w-5 h-5 text-primary-400" />
                  <h3 className="font-semibold text-sm">{key}</h3>
                </div>
                <pre className="text-xs text-text-muted font-mono bg-surface rounded-lg p-3 overflow-x-auto">
                  {typeof val === 'string' ? val : JSON.stringify(val, null, 2)}
                </pre>
              </div>
            ))
          ) : (
            <pre className="text-xs text-text-muted font-mono bg-surface-light border border-border rounded-xl p-5 overflow-x-auto">
              {JSON.stringify(models, null, 2)}
            </pre>
          )}
        </div>
      ) : null}
    </div>
  )
}

function ModelCard({ model }) {
  const name = model.name || model.model_name || 'Unknown'
  const ready = model.ready ?? model.installed ?? model.available ?? null

  return (
    <div className="bg-surface-light border border-border rounded-xl p-5 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-primary-600/20 flex items-center justify-center">
          <HardDrive className="w-5 h-5 text-primary-400" />
        </div>
        <div>
          <div className="font-medium text-sm">{name}</div>
          {model.version && <div className="text-xs text-text-muted mt-0.5">v{model.version}</div>}
        </div>
      </div>
      {ready !== null && (
        ready ? (
          <span className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4" /> Ready
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-red-400 text-xs font-medium">
            <XCircle className="w-4 h-4" /> Not installed
          </span>
        )
      )}
    </div>
  )
}
