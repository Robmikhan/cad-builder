import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, uploadImage } from '../api'
import {
  MessageSquare, Image, Video, Send, Loader2, AlertCircle,
  Ruler, Box, ArrowLeft, Upload, X
} from 'lucide-react'

const MODES = [
  {
    id: 'PROMPT',
    label: 'From Prompt',
    desc: 'Describe your part with dimensions',
    icon: MessageSquare,
    accent: 'border-primary-500 bg-primary-500/10',
  },
  {
    id: 'IMAGE',
    label: 'From Image',
    desc: 'Upload a photo of an existing part',
    icon: Image,
    accent: 'border-emerald-500 bg-emerald-500/10',
  },
  {
    id: 'VIDEO',
    label: 'From Video',
    desc: 'Reconstruct from video footage',
    icon: Video,
    accent: 'border-purple-500 bg-purple-500/10',
  },
]

const INITIAL = {
  part_name: '',
  mode: 'PROMPT',
  units: 'mm',
  tolerance_mm: 0.2,
  use_case: '',
  dimensions: { L: '', W: '', H: '' },
}

export default function NewJob() {
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef(null)

  const set = (key, val) => setForm(prev => ({ ...prev, [key]: val }))
  const setDim = (key, val) => setForm(prev => ({
    ...prev,
    dimensions: { ...prev.dimensions, [key]: val },
  }))

  const handleImageSelect = (file) => {
    if (!file) return
    setImageFile(file)
    const reader = new FileReader()
    reader.onload = (e) => setImagePreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const clearImage = () => {
    setImageFile(null)
    setImagePreview(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const spec = {
        part_name: form.part_name,
        mode: form.mode,
        units: form.units,
        tolerance_mm: parseFloat(form.tolerance_mm) || 0.2,
      }

      if (form.use_case) spec.use_case = form.use_case

      if (form.mode === 'PROMPT') {
        const dims = {}
        if (form.dimensions.L) dims.L = parseFloat(form.dimensions.L)
        if (form.dimensions.W) dims.W = parseFloat(form.dimensions.W)
        if (form.dimensions.H) dims.H = parseFloat(form.dimensions.H)
        if (Object.keys(dims).length > 0) spec.dimensions = dims
      }

      // Upload image first for IMAGE mode
      if (form.mode === 'IMAGE' && imageFile) {
        setUploading(true)
        const uploadResult = await uploadImage(imageFile)
        setUploading(false)
        spec.inputs = { image_paths: [uploadResult.path] }
      } else if (form.mode === 'IMAGE' && !imageFile) {
        throw new Error('Please upload an image for IMAGE mode')
      }

      const job = await createJob(spec)
      navigate(`/jobs/${job.job_id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
      setUploading(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-1.5 text-text-muted hover:text-text text-sm mb-6 transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </button>

      <h1 className="text-2xl font-bold mb-1">Create New Job</h1>
      <p className="text-text-muted text-sm mb-8">Configure your parametric CAD generation job</p>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Mode Selector */}
        <section>
          <label className="text-sm font-medium text-text-muted mb-3 block">Generation Mode</label>
          <div className="grid grid-cols-3 gap-3">
            {MODES.map((m) => {
              const Icon = m.icon
              const active = form.mode === m.id
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => set('mode', m.id)}
                  className={`relative p-4 rounded-xl border-2 text-left transition-all cursor-pointer ${
                    active ? m.accent : 'border-border bg-surface-light hover:border-surface-lighter'
                  }`}
                >
                  <Icon className={`w-6 h-6 mb-2 ${active ? 'text-white' : 'text-text-muted'}`} />
                  <div className="font-medium text-sm">{m.label}</div>
                  <div className="text-xs text-text-muted mt-0.5">{m.desc}</div>
                  {active && (
                    <div className="absolute top-3 right-3 w-2 h-2 rounded-full bg-white" />
                  )}
                </button>
              )
            })}
          </div>
        </section>

        {/* Part Name */}
        <section className="space-y-4">
          <label className="text-sm font-medium text-text-muted block">Part Details</label>
          <div className="bg-surface-light border border-border rounded-xl p-5 space-y-4">
            <div>
              <label className="text-xs text-text-muted mb-1.5 block">Part Name *</label>
              <input
                type="text"
                required
                value={form.part_name}
                onChange={(e) => set('part_name', e.target.value)}
                placeholder="e.g. Motor Bracket v2"
                className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">Units</label>
                <select
                  value={form.units}
                  onChange={(e) => set('units', e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all cursor-pointer"
                >
                  <option value="mm">Millimeters (mm)</option>
                  <option value="inch">Inches (in)</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-text-muted mb-1.5 block">
                  Tolerance ({form.units})
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.tolerance_mm}
                  onChange={(e) => set('tolerance_mm', e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-text-muted mb-1.5 block">Use Case (optional)</label>
              <input
                type="text"
                value={form.use_case}
                onChange={(e) => set('use_case', e.target.value)}
                placeholder="e.g. structural bracket for 3D printer frame"
                className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
            </div>
          </div>
        </section>

        {/* Dimensions (PROMPT mode) */}
        {form.mode === 'PROMPT' && (
          <section>
            <label className="text-sm font-medium text-text-muted mb-3 block">
              <Ruler className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Dimensions ({form.units})
            </label>
            <div className="bg-surface-light border border-border rounded-xl p-5">
              <div className="grid grid-cols-3 gap-4">
                {['L', 'W', 'H'].map((d) => (
                  <div key={d}>
                    <label className="text-xs text-text-muted mb-1.5 block">
                      {d === 'L' ? 'Length' : d === 'W' ? 'Width' : 'Height'} ({d})
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={form.dimensions[d]}
                      onChange={(e) => setDim(d, e.target.value)}
                      placeholder="0.0"
                      className="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                    />
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* IMAGE upload */}
        {form.mode === 'IMAGE' && (
          <section>
            <label className="text-sm font-medium text-text-muted mb-3 block">
              <Upload className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Upload Image
            </label>
            <div
              className="bg-surface-light border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary-500/50 transition-colors cursor-pointer"
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
              onDrop={(e) => { e.preventDefault(); handleImageSelect(e.dataTransfer.files[0]) }}
            >
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleImageSelect(e.target.files[0])}
              />
              {imagePreview ? (
                <div className="relative inline-block">
                  <img src={imagePreview} alt="Preview" className="max-h-48 rounded-lg mx-auto" />
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); clearImage() }}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white hover:bg-red-600 cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                  <p className="text-xs text-text-muted mt-3">{imageFile?.name}</p>
                </div>
              ) : (
                <>
                  <Image className="w-10 h-10 text-text-muted/40 mx-auto mb-3" />
                  <p className="text-sm text-text-muted">Drag & drop an image or click to browse</p>
                  <p className="text-xs text-text-muted/60 mt-1">PNG, JPG, WebP supported</p>
                </>
              )}
            </div>
            <p className="text-xs text-text-muted mt-2">
              The pipeline will remove the background, reconstruct a 3D mesh, then generate parametric CadQuery code.
            </p>
          </section>
        )}

        {/* VIDEO info */}
        {form.mode === 'VIDEO' && (
          <div className="bg-surface-light border border-border rounded-xl p-5 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
            <div className="text-sm text-text-muted">
              <p className="font-medium text-text mb-1">Video Mode</p>
              <p>Video mode uses COLMAP multi-view reconstruction and is not yet fully implemented.</p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 text-sm flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={submitting || !form.part_name}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors cursor-pointer"
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {submitting ? 'Creating...' : 'Create Job'}
          </button>
        </div>
      </form>
    </div>
  )
}
