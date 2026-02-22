import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchHealth, fetchUsage } from '../api'
import {
  Settings, Key, Server, CheckCircle2, XCircle,
  Loader2, Save, Eye, EyeOff, Trash2, BarChart3, Crown
} from 'lucide-react'

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [usage, setUsage] = useState(null)

  useEffect(() => {
    const stored = localStorage.getItem('cad_api_key') || ''
    setApiKey(stored)
    checkHealth()
    if (stored) {
      fetchUsage().then(setUsage).catch(() => {})
    }
  }, [])

  const checkHealth = async () => {
    setHealthLoading(true)
    try {
      const data = await fetchHealth()
      setHealth(data)
    } catch {
      setHealth(null)
    } finally {
      setHealthLoading(false)
    }
  }

  const saveKey = () => {
    if (apiKey.trim()) {
      localStorage.setItem('cad_api_key', apiKey.trim())
    } else {
      localStorage.removeItem('cad_api_key')
    }
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const clearKey = () => {
    setApiKey('')
    localStorage.removeItem('cad_api_key')
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-text-muted text-sm mt-1">Configure API access and view system status</p>
      </div>

      {/* Server Status */}
      <div className="bg-surface-light border border-border rounded-xl p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Server className="w-4 h-4 text-primary-400" /> Server Status
          </h2>
          <button
            onClick={checkHealth}
            className="text-xs text-primary-400 hover:text-primary-300 transition-colors cursor-pointer"
          >
            Refresh
          </button>
        </div>

        {healthLoading ? (
          <div className="flex items-center gap-2 text-text-muted text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Checking...
          </div>
        ) : health ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400 font-medium">Connected</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-surface rounded-lg p-3">
                <div className="text-xs text-text-muted mb-1">Version</div>
                <div className="text-sm font-medium">{health.version}</div>
              </div>
              <div className="bg-surface rounded-lg p-3">
                <div className="text-xs text-text-muted mb-1">Status</div>
                <div className="text-sm font-medium capitalize">{health.status}</div>
              </div>
              <div className="bg-surface rounded-lg p-3">
                <div className="text-xs text-text-muted mb-1">Uptime</div>
                <div className="text-sm font-medium">{Math.round(health.uptime_sec / 60)}m</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-400 font-medium">Cannot reach server</span>
          </div>
        )}
      </div>

      {/* Usage & Plan */}
      {usage && (
        <div className="bg-surface-light border border-border rounded-xl p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary-400" /> Usage & Plan
            </h2>
            <Link to="/pricing" className="text-xs text-primary-400 hover:text-primary-300 transition-colors flex items-center gap-1">
              <Crown className="w-3.5 h-3.5" /> Upgrade
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-surface rounded-lg p-3">
              <div className="text-xs text-text-muted mb-1">Plan</div>
              <div className="text-sm font-semibold">{usage.tier_label}</div>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <div className="text-xs text-text-muted mb-1">Jobs Used</div>
              <div className="text-sm font-semibold">{usage.jobs_used} / {usage.jobs_limit}</div>
            </div>
            <div className="bg-surface rounded-lg p-3">
              <div className="text-xs text-text-muted mb-1">
                {usage.days_remaining !== null ? 'Trial Days Left' : 'Remaining'}
              </div>
              <div className="text-sm font-semibold">
                {usage.days_remaining !== null ? `${usage.days_remaining} days` : `${usage.jobs_remaining} jobs`}
              </div>
            </div>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-surface rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                usage.jobs_used / usage.jobs_limit > 0.8 ? 'bg-red-500' :
                usage.jobs_used / usage.jobs_limit > 0.5 ? 'bg-yellow-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, (usage.jobs_used / usage.jobs_limit) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* API Key */}
      <div className="bg-surface-light border border-border rounded-xl p-5 mb-6">
        <h2 className="text-sm font-semibold flex items-center gap-2 mb-4">
          <Key className="w-4 h-4 text-primary-400" /> API Key
        </h2>
        <p className="text-xs text-text-muted mb-4">
          If the server requires authentication, enter your API key here.
          It will be stored locally in your browser and sent with every request.
        </p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter API key..."
              className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 pr-10 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text cursor-pointer"
            >
              {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <button
            onClick={saveKey}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium transition-colors cursor-pointer"
          >
            {saved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saved ? 'Saved' : 'Save'}
          </button>
          {apiKey && (
            <button
              onClick={clearKey}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-sm transition-colors cursor-pointer"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* About */}
      <div className="bg-surface-light border border-border rounded-xl p-5">
        <h2 className="text-sm font-semibold flex items-center gap-2 mb-4">
          <Settings className="w-4 h-4 text-primary-400" /> About
        </h2>
        <div className="space-y-2 text-sm text-text-muted">
          <p><strong className="text-text">CAD Builder</strong> v0.2.0</p>
          <p>AI-powered parametric CAD generation from text and images.</p>
          <p>Uses local LLM (Ollama) and GPU-accelerated vision models.</p>
          <p className="pt-2 text-xs">
            <a href="/docs" className="text-primary-400 hover:text-primary-300 transition-colors">API Documentation</a>
            {' · '}
            <a href="https://github.com" className="text-primary-400 hover:text-primary-300 transition-colors">GitHub</a>
          </p>
        </div>
      </div>
    </div>
  )
}
