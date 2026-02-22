import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchTiers, requestTrial } from '../api'
import {
  Check, Zap, ArrowRight, Loader2, Box, Crown,
  Rocket, Building2, AlertCircle, Copy, CheckCircle2
} from 'lucide-react'

const TIER_ICONS = {
  free_trial: Zap,
  starter: Rocket,
  pro: Crown,
  business: Building2,
}

const TIER_ACCENTS = {
  free_trial: 'border-text-muted/30',
  starter: 'border-primary-500 ring-2 ring-primary-500/20',
  pro: 'border-emerald-500 ring-2 ring-emerald-500/20',
  business: 'border-purple-500 ring-2 ring-purple-500/20',
}

export default function PricingPage() {
  const navigate = useNavigate()
  const [tiers, setTiers] = useState([])
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [trialResult, setTrialResult] = useState(null)
  const [trialLoading, setTrialLoading] = useState(false)
  const [trialError, setTrialError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchTiers().then(setTiers).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleTrial = async (e) => {
    e.preventDefault()
    setTrialLoading(true)
    setTrialError(null)
    try {
      const result = await requestTrial(email)
      setTrialResult(result)
      // Auto-save to localStorage
      if (result.api_key) {
        localStorage.setItem('cad_api_key', result.api_key)
      }
    } catch (err) {
      setTrialError(err.message)
    } finally {
      setTrialLoading(false)
    }
  }

  const copyKey = () => {
    if (trialResult?.api_key) {
      navigator.clipboard.writeText(trialResult.api_key)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface">
      {/* Nav */}
      <nav className="border-b border-border bg-surface-light/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <Box className="w-7 h-7 text-primary-400" />
            <span className="text-lg font-bold tracking-tight">CAD Builder</span>
          </Link>
          <Link
            to="/dashboard"
            className="px-4 py-2 rounded-lg bg-surface-lighter text-sm text-text-muted hover:text-text transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </nav>

      {/* Header */}
      <div className="max-w-5xl mx-auto px-6 pt-16 pb-12 text-center">
        <h1 className="text-4xl font-extrabold mb-4">Simple, Transparent Pricing</h1>
        <p className="text-text-muted text-lg max-w-xl mx-auto">
          Start free. Upgrade when you need more. No hidden fees.
        </p>
      </div>

      {/* Tier Cards */}
      <div className="max-w-5xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-4 gap-5">
          {tiers.map((tier) => {
            const Icon = TIER_ICONS[tier.id] || Zap
            const accent = TIER_ACCENTS[tier.id] || 'border-border'
            const isPopular = tier.id === 'pro'

            return (
              <div
                key={tier.id}
                className={`relative bg-surface-light border-2 rounded-2xl p-6 flex flex-col ${accent}`}
              >
                {isPopular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-emerald-500 text-white text-xs font-bold">
                    Most Popular
                  </div>
                )}
                <Icon className="w-8 h-8 text-primary-400 mb-4" />
                <h3 className="text-lg font-bold mb-1">{tier.label}</h3>
                <div className="mb-4">
                  {tier.price_monthly === 0 ? (
                    <span className="text-3xl font-extrabold">Free</span>
                  ) : (
                    <>
                      <span className="text-3xl font-extrabold">${tier.price_monthly}</span>
                      <span className="text-text-muted text-sm">/mo</span>
                    </>
                  )}
                </div>
                <ul className="space-y-2.5 mb-6 flex-1">
                  <li className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{tier.max_jobs_per_month} jobs / month</span>
                  </li>
                  {tier.pipelines.map((p) => (
                    <li key={p} className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                      <span>{p} pipeline</span>
                    </li>
                  ))}
                  <li className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>STEP + STL export</span>
                  </li>
                  {tier.trial_days > 0 && (
                    <li className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                      <span>{tier.trial_days}-day free trial</span>
                    </li>
                  )}
                  {tier.id !== 'free_trial' && (
                    <li className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                      <span>3D preview</span>
                    </li>
                  )}
                  {tier.id === 'business' && (
                    <li className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                      <span>API access + batch</span>
                    </li>
                  )}
                </ul>
                {tier.id === 'free_trial' ? (
                  <button
                    onClick={() => document.getElementById('trial-form')?.scrollIntoView({ behavior: 'smooth' })}
                    className="w-full py-2.5 rounded-xl bg-surface-lighter hover:bg-surface text-sm font-medium transition-colors cursor-pointer"
                  >
                    Start Free Trial
                  </button>
                ) : tier.stripe_link ? (
                  <a
                    href={tier.stripe_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`w-full py-2.5 rounded-xl text-center text-sm font-semibold transition-colors block ${
                      isPopular
                        ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        : 'bg-primary-600 hover:bg-primary-700 text-white'
                    }`}
                  >
                    Subscribe
                  </a>
                ) : (
                  <button
                    disabled
                    className="w-full py-2.5 rounded-xl bg-surface-lighter text-text-muted text-sm font-medium cursor-not-allowed"
                  >
                    Coming Soon
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Trial Signup */}
      <section id="trial-form" className="border-t border-border bg-surface-light/50">
        <div className="max-w-lg mx-auto px-6 py-16 text-center">
          <Zap className="w-8 h-8 text-primary-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Start Your Free Trial</h2>
          <p className="text-text-muted text-sm mb-8">
            Get 10 free jobs over 14 days. No credit card required.
          </p>

          {trialResult ? (
            <div className="bg-surface border border-emerald-500/30 rounded-xl p-6 text-left">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-semibold text-emerald-400">Trial Activated!</span>
              </div>
              <p className="text-sm text-text-muted mb-3">Your API key has been saved automatically. You can also copy it:</p>
              <div className="flex gap-2 mb-4">
                <code className="flex-1 bg-surface-lighter rounded-lg px-3 py-2 text-xs font-mono text-text break-all">
                  {trialResult.api_key}
                </code>
                <button
                  onClick={copyKey}
                  className="px-3 py-2 rounded-lg bg-surface-lighter text-text-muted hover:text-text transition-colors cursor-pointer"
                >
                  {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <button
                onClick={() => navigate('/new')}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors cursor-pointer"
              >
                Create Your First Part <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <form onSubmit={handleTrial} className="space-y-4">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com (optional)"
                className="w-full bg-surface border border-border rounded-xl px-4 py-3 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
              {trialError && (
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" /> {trialError}
                </div>
              )}
              <button
                type="submit"
                disabled={trialLoading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white font-semibold transition-colors cursor-pointer"
              >
                {trialLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                {trialLoading ? 'Generating...' : 'Get Free API Key'}
              </button>
            </form>
          )}
        </div>
      </section>

      <footer className="border-t border-border py-8 text-center text-xs text-text-muted">
        <p>CAD Builder v0.2.0 — AI-powered parametric CAD generation</p>
      </footer>
    </div>
  )
}
