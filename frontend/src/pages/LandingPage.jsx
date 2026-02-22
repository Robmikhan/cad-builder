import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { fetchHealth } from '../api'
import {
  Box, ArrowRight, Zap, Shield, Eye, Code2,
  FileOutput, Image, MessageSquare, Cpu, CheckCircle2
} from 'lucide-react'

const FEATURES = [
  {
    icon: MessageSquare,
    title: 'Text to CAD',
    desc: 'Describe your part in plain English with dimensions — AI generates parametric CadQuery code.',
  },
  {
    icon: Image,
    title: 'Image to CAD',
    desc: 'Upload a photo of any part. Background removal, 3D mesh reconstruction, then parametric code.',
  },
  {
    icon: Code2,
    title: 'Auto-Repair',
    desc: 'LLM automatically validates and fixes generated CadQuery code until it compiles correctly.',
  },
  {
    icon: FileOutput,
    title: 'STEP / STL Export',
    desc: 'Production-ready STEP and STL files for CNC, 3D printing, or further CAD editing.',
  },
  {
    icon: Eye,
    title: '3D Preview',
    desc: 'Interactive 3D viewer right in your browser. Rotate, zoom, and inspect before downloading.',
  },
  {
    icon: Shield,
    title: 'Sandboxed Execution',
    desc: 'AI-generated code runs in a restricted sandbox — no file system or network access.',
  },
]

const STEPS = [
  { num: '1', title: 'Describe or Upload', desc: 'Enter part dimensions or upload a photo' },
  { num: '2', title: 'AI Generates', desc: 'LLM creates parametric CadQuery code' },
  { num: '3', title: 'Validate & Repair', desc: 'Auto-repair loop fixes any issues' },
  { num: '4', title: 'Download', desc: 'Get your STEP, STL, or GLB file' },
]

export default function LandingPage() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-surface">
      {/* Nav */}
      <nav className="border-b border-border bg-surface-light/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Box className="w-7 h-7 text-primary-400" />
            <span className="text-lg font-bold tracking-tight">CAD Builder</span>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <span className="flex items-center gap-1.5 text-emerald-400 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5" /> Online
              </span>
            )}
            <Link
              to="/dashboard"
              className="px-4 py-2 rounded-lg bg-surface-lighter text-sm text-text-muted hover:text-text transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/new"
              className="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-600/5 to-transparent" />
        <div className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-600/10 border border-primary-500/20 text-primary-300 text-xs font-medium mb-8">
            <Zap className="w-3.5 h-3.5" />
            Powered by Local AI — Your Data Never Leaves Your Machine
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight leading-tight mb-6">
            Turn Words & Photos<br />
            <span className="text-primary-400">Into Production CAD Files</span>
          </h1>
          <p className="text-lg text-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Describe a part or upload a photo. CAD Builder uses local AI to generate
            parametric CadQuery code, validate it, and export production-ready STEP and STL files.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              to="/new"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-semibold transition-colors shadow-lg shadow-primary-600/25"
            >
              Create Your First Part <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-surface-lighter hover:bg-surface-light text-text-muted hover:text-text font-medium transition-colors"
            >
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <h2 className="text-2xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid grid-cols-4 gap-6">
          {STEPS.map((step) => (
            <div key={step.num} className="text-center">
              <div className="w-12 h-12 rounded-full bg-primary-600/20 text-primary-400 font-bold text-lg flex items-center justify-center mx-auto mb-4">
                {step.num}
              </div>
              <h3 className="font-semibold text-sm mb-1">{step.title}</h3>
              <p className="text-xs text-text-muted">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border bg-surface-light/50">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-2xl font-bold text-center mb-4">Features</h2>
          <p className="text-text-muted text-center mb-12 max-w-xl mx-auto">
            Everything you need to go from idea to manufactured part.
          </p>
          <div className="grid grid-cols-3 gap-6">
            {FEATURES.map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title} className="bg-surface border border-border rounded-xl p-6 hover:border-primary-500/30 transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-primary-600/15 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-primary-400" />
                  </div>
                  <h3 className="font-semibold text-sm mb-2">{f.title}</h3>
                  <p className="text-xs text-text-muted leading-relaxed">{f.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border">
        <div className="max-w-3xl mx-auto px-6 py-20 text-center">
          <Cpu className="w-10 h-10 text-primary-400 mx-auto mb-6" />
          <h2 className="text-2xl font-bold mb-4">Ready to Build?</h2>
          <p className="text-text-muted mb-8">
            No cloud required. Run entirely on your hardware with your GPU.
          </p>
          <Link
            to="/new"
            className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-semibold transition-colors shadow-lg shadow-primary-600/25"
          >
            Start Building <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 text-center text-xs text-text-muted">
        <p>CAD Builder v0.2.0 — Open-source AI-powered CAD generation</p>
      </footer>
    </div>
  )
}
