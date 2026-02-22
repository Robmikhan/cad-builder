import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { fetchJob, fetchJobEvents, downloadBundleUrl, downloadStepUrl, downloadStlUrl, glbPreviewUrl } from '../api'
import '@google/model-viewer'
import {
  ArrowLeft, Clock, CheckCircle2, XCircle, Loader2,
  Download, FileCode2, Box, Copy, Check, RefreshCw,
  ChevronRight, AlertCircle, Eye, FileDown
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
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${cfg.bg} ${cfg.color}`}>
      <Icon className={`w-4 h-4 ${cfg.spin ? 'animate-spin' : ''}`} />
      {cfg.label}
    </span>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between py-2.5 border-b border-border/50 last:border-0">
      <span className="text-text-muted text-sm">{label}</span>
      <span className="text-sm font-medium">{value || '—'}</span>
    </div>
  )
}

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <button
        onClick={copy}
        className="absolute top-3 right-3 p-1.5 rounded-md bg-surface-lighter/80 text-text-muted hover:text-text opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
      <pre className="bg-surface rounded-lg p-4 text-xs font-mono text-text-muted overflow-x-auto leading-relaxed whitespace-pre-wrap">
        {code}
      </pre>
    </div>
  )
}

export default function JobDetail() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  const load = async () => {
    try {
      const [j, e] = await Promise.all([fetchJob(jobId), fetchJobEvents(jobId)])
      setJob(j)
      setEvents(e)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [jobId])

  // Auto-refresh while running
  useEffect(() => {
    if (!job || (job.status !== 'RUNNING' && job.status !== 'QUEUED')) return
    const id = setInterval(load, 3000)
    return () => clearInterval(id)
  }, [job?.status])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32 text-text-muted">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading job...
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl">
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-1.5 text-text-muted hover:text-text text-sm mb-6 cursor-pointer">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 text-sm">{error}</div>
      </div>
    )
  }

  if (!job) return null

  const spec = job.part_spec || {}
  const artifacts = job.artifacts || {}
  const metrics = job.metrics || {}
  const cadScript = artifacts.cad_script_path ? true : false

  const hasGlb = artifacts.mesh_path || artifacts.glb_path
  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: '3dpreview', label: '3D Preview', disabled: !hasGlb && job.status !== 'DONE' },
    { id: 'cadscript', label: 'CAD Script' },
    { id: 'events', label: 'Events', count: events.length },
  ]

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-1.5 text-text-muted hover:text-text text-sm mb-6 transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </button>

      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">{spec.part_name || 'Untitled'}</h1>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-text-muted text-sm font-mono">{job.job_id}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={load}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-lighter text-text-muted hover:text-text text-sm transition-colors cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {artifacts.step_path && (
            <a
              href={downloadStepUrl(job.job_id)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-lighter text-text hover:text-white text-sm font-medium transition-colors"
            >
              <FileDown className="w-4 h-4" /> STEP
            </a>
          )}
          {artifacts.stl_path && (
            <a
              href={downloadStlUrl(job.job_id)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-lighter text-text hover:text-white text-sm font-medium transition-colors"
            >
              <FileDown className="w-4 h-4" /> STL
            </a>
          )}
          {artifacts.bundle_path && (
            <a
              href={downloadBundleUrl(job.job_id)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium transition-colors"
            >
              <Download className="w-4 h-4" /> Bundle
            </a>
          )}
        </div>
      </div>

      {/* Error banner */}
      {job.error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 mb-6 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <div className="font-medium mb-1">Job Failed</div>
            {job.error}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              activeTab === tab.id
                ? 'border-primary-500 text-primary-300'
                : 'border-transparent text-text-muted hover:text-text'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="ml-1.5 text-xs bg-surface-lighter rounded-full px-1.5 py-0.5">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 gap-6">
          {/* Part Spec */}
          <div className="bg-surface-light border border-border rounded-xl p-5">
            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
              <Box className="w-4 h-4 text-primary-400" /> Part Specification
            </h3>
            <InfoRow label="Mode" value={spec.mode} />
            <InfoRow label="Units" value={spec.units} />
            <InfoRow label="Tolerance" value={`${spec.tolerance_mm} ${spec.units === 'inch' ? 'in' : 'mm'}`} />
            {spec.use_case && <InfoRow label="Use Case" value={spec.use_case} />}
            {spec.dimensions && (
              <>
                {spec.dimensions.L != null && <InfoRow label="Length (L)" value={spec.dimensions.L} />}
                {spec.dimensions.W != null && <InfoRow label="Width (W)" value={spec.dimensions.W} />}
                {spec.dimensions.H != null && <InfoRow label="Height (H)" value={spec.dimensions.H} />}
              </>
            )}
          </div>

          {/* Metrics & Artifacts */}
          <div className="space-y-6">
            <div className="bg-surface-light border border-border rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary-400" /> Metrics
              </h3>
              <InfoRow label="Runtime" value={metrics.runtime_sec > 0 ? `${metrics.runtime_sec.toFixed(2)}s` : 'N/A'} />
              <InfoRow label="Iterations" value={metrics.num_iterations || 0} />
              <InfoRow label="Created" value={job.created_at ? new Date(job.created_at).toLocaleString() : '—'} />
            </div>

            <div className="bg-surface-light border border-border rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <FileCode2 className="w-4 h-4 text-primary-400" /> Artifacts
              </h3>
              {Object.keys(artifacts).length === 0 ? (
                <p className="text-sm text-text-muted">No artifacts yet</p>
              ) : (
                Object.entries(artifacts).map(([key, val]) => (
                  <InfoRow key={key} label={key} value={typeof val === 'string' ? val.split(/[/\\]/).pop() : JSON.stringify(val)} />
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === '3dpreview' && (
        <div className="bg-surface-light border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Eye className="w-4 h-4 text-primary-400" /> 3D Model Preview
            </h3>
            {hasGlb && (
              <a
                href={glbPreviewUrl(job.job_id)}
                download
                className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
              >
                Download GLB
              </a>
            )}
          </div>
          <div className="h-[500px] bg-surface">
            {hasGlb ? (
              <model-viewer
                src={glbPreviewUrl(job.job_id)}
                alt={`3D preview of ${spec.part_name || 'part'}`}
                camera-controls
                auto-rotate
                shadow-intensity="1"
                environment-image="neutral"
                style={{ width: '100%', height: '100%', backgroundColor: '#0f1117' }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-text-muted">
                <Box className="w-12 h-12 mb-3 opacity-30" />
                <p className="text-sm">
                  {job.status === 'RUNNING' || job.status === 'QUEUED'
                    ? 'Generating 3D model...'
                    : 'No 3D mesh available for this job'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'cadscript' && (
        <div className="bg-surface-light border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-primary-400" /> Generated CadQuery Script
          </h3>
          {artifacts.cad_script_path ? (
            <div>
              <div className="text-xs text-text-muted mb-3">
                File: <span className="font-mono">{artifacts.cad_script_path.split(/[/\\]/).pop()}</span>
              </div>
              <CodeBlock code={artifacts.cad_source || '# CAD script source not available in API response.\n# Check the file on disk at the path above.'} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <FileCode2 className="w-8 h-8 mb-2 opacity-40" />
              <p className="text-sm">
                {job.status === 'RUNNING' || job.status === 'QUEUED'
                  ? 'Waiting for pipeline to generate CAD script...'
                  : 'No CAD script generated for this job'}
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'events' && (
        <div className="bg-surface-light border border-border rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h3 className="text-sm font-semibold">Pipeline Events</h3>
          </div>
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Clock className="w-8 h-8 mb-2 opacity-40" />
              <p className="text-sm">No events recorded yet</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {events.map((ev, i) => (
                <div key={i} className="px-5 py-3.5 flex items-start gap-3">
                  <ChevronRight className="w-4 h-4 text-text-muted mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium font-mono">{ev.event_type}</span>
                      <span className="text-xs text-text-muted">
                        {ev.ts ? new Date(ev.ts).toLocaleTimeString() : ''}
                      </span>
                    </div>
                    {ev.payload && Object.keys(ev.payload).length > 0 && (
                      <pre className="text-xs text-text-muted font-mono bg-surface rounded p-2 mt-1 overflow-x-auto">
                        {JSON.stringify(ev.payload, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
