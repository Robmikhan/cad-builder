import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchJobs } from '../api'
import {
  Clock, CheckCircle2, XCircle, Loader2, RefreshCw,
  ArrowRight, Box, Layers
} from 'lucide-react'

const STATUS_CONFIG = {
  QUEUED: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/10', label: 'Queued' },
  RUNNING: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-400/10', label: 'Running', spin: true },
  DONE: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-400/10', label: 'Done' },
  FAILED: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10', label: 'Failed' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.QUEUED
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
      <Icon className={`w-3.5 h-3.5 ${cfg.spin ? 'animate-spin' : ''}`} />
      {cfg.label}
    </span>
  )
}

function StatCard({ label, value, icon: Icon, accent }) {
  return (
    <div className="bg-surface-light border border-border rounded-xl p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-lg flex items-center justify-center ${accent}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs text-text-muted mt-0.5">{label}</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchJobs()
      setJobs(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  // Auto-refresh every 5s if any jobs are running
  useEffect(() => {
    const hasActive = jobs.some(j => j.status === 'RUNNING' || j.status === 'QUEUED')
    if (!hasActive) return
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [jobs])

  const counts = {
    total: jobs.length,
    done: jobs.filter(j => j.status === 'DONE').length,
    running: jobs.filter(j => j.status === 'RUNNING' || j.status === 'QUEUED').length,
    failed: jobs.filter(j => j.status === 'FAILED').length,
  }

  return (
    <div className="max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-text-muted text-sm mt-1">Monitor your CAD generation jobs</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={load}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-lighter text-text-muted hover:text-text text-sm font-medium transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link
            to="/new"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium transition-colors"
          >
            New Job
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Jobs" value={counts.total} icon={Layers} accent="bg-primary-600/20 text-primary-400" />
        <StatCard label="Completed" value={counts.done} icon={CheckCircle2} accent="bg-emerald-500/20 text-emerald-400" />
        <StatCard label="In Progress" value={counts.running} icon={Loader2} accent="bg-blue-500/20 text-blue-400" />
        <StatCard label="Failed" value={counts.failed} icon={XCircle} accent="bg-red-500/20 text-red-400" />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 mb-6 text-sm">
          {error}
        </div>
      )}

      {/* Jobs Table */}
      <div className="bg-surface-light border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-border">
          <h2 className="font-semibold text-sm">Recent Jobs</h2>
        </div>

        {loading && jobs.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-text-muted">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading...
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Box className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm">No jobs yet</p>
            <Link to="/new" className="text-primary-400 text-sm mt-1 hover:underline">
              Create your first job
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-text-muted border-b border-border">
                <th className="px-5 py-3 font-medium">Part Name</th>
                <th className="px-5 py-3 font-medium">Mode</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Units</th>
                <th className="px-5 py-3 font-medium">Runtime</th>
                <th className="px-5 py-3 font-medium">Created</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id} className="border-b border-border/50 hover:bg-surface-lighter/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <span className="font-medium text-sm">{job.part_spec?.part_name || '—'}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-xs px-2 py-0.5 rounded bg-surface-lighter text-text-muted font-mono">
                      {job.part_spec?.mode}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-5 py-3.5 text-sm text-text-muted">
                    {job.part_spec?.units}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-text-muted">
                    {job.metrics?.runtime_sec > 0
                      ? `${job.metrics.runtime_sec.toFixed(1)}s`
                      : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-text-muted">
                    {job.created_at
                      ? new Date(job.created_at).toLocaleString()
                      : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/jobs/${job.job_id}`}
                      className="text-primary-400 hover:text-primary-300 transition-colors"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
