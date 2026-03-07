import { useState } from 'react'
import { Link } from 'react-router-dom'
import { isAuthEnabled } from '../auth/ClerkProviderWrapper'
import Icon from '../components/Icon'
import { api } from '../api'
import FeatureComparisonTable from '../components/FeatureComparisonTable'

interface Tier {
  name: string
  monthlyPrice: number | null
  annualPrice: number | null
  description: string
  features: string[]
  excluded?: string[]
  highlighted: boolean
  isEnterprise?: boolean
  badge?: string
}

const tiers: Tier[] = [
  {
    name: 'Free',
    monthlyPrice: 0,
    annualPrice: 0,
    description: 'Essential security monitoring for small teams.',
    features: [
      'Up to 3 agents',
      '1,000 events/month',
      'MCP Config Scanner',
      'Policy Engine',
      'Anomaly Detection',
      'Community support',
    ],
    excluded: [
      'Security Proxy',
      'Pentest Engine',
      'LLM Analysis',
    ],
    highlighted: false,
  },
  {
    name: 'Lite',
    monthlyPrice: 29,
    annualPrice: 24,
    description: 'Full-featured security for growing teams.',
    features: [
      'Up to 10 agents',
      '50,000 events/month',
      'Everything in Free',
      'Security Proxy',
      'Pentest Engine',
      'LLM Analysis',
      'Auto-Remediation',
    ],
    excluded: [
      'Agent Trust Score',
      'Risk Analytics',
    ],
    highlighted: false,
  },
  {
    name: 'Elite',
    monthlyPrice: 99,
    annualPrice: 79,
    description: 'Advanced analytics and trust scoring for security teams.',
    features: [
      'Up to 50 agents',
      '250,000 events/month',
      'Everything in Lite',
      'Agent Trust Score',
      'Risk Analytics Dashboard',
      'Behavioral Profiling',
      'Anomaly Trends',
      'SSO / SAML',
      'Priority support',
    ],
    highlighted: true,
    badge: 'Most Popular',
  },
  {
    name: 'Enterprise',
    monthlyPrice: null,
    annualPrice: null,
    description: 'Unlimited scale with dedicated support.',
    features: [
      'Everything in Elite',
      'Unlimited agents & events',
      'Self-host + support contract',
      'Dedicated cloud deployment',
      'Dedicated support engineer',
      'Custom policy templates',
      'SLA guarantees',
    ],
    highlighted: false,
    isEnterprise: true,
  },
]

const faqItems = [
  {
    question: 'Is there really a free tier?',
    answer:
      'Yes. The free cloud tier includes up to 3 agents and 1,000 events per month with access to the config scanner, policy engine, and anomaly detection. Alternatively, you can self-host for unlimited usage.',
  },
  {
    question: "What's the difference between Lite and Elite?",
    answer:
      'Lite gives you all core security features (proxy, pentest, LLM analysis) with usage limits of 10 agents and 50k events/month. Elite adds unlimited usage plus advanced analytics: Agent Trust Score, Risk Analytics, Behavioral Profiling, Anomaly Trends, and SSO/SAML.',
  },
  {
    question: 'What is Agent Trust Score?',
    answer:
      "Agent Trust Score is an Elite feature that assigns each MCP agent a trustworthiness rating (0-100) based on behavioral patterns, policy compliance, anomaly frequency, and data access patterns. It helps you answer: 'Is this agent safe to run in production?'",
  },
  {
    question: 'Can I self-host Navil?',
    answer:
      'Absolutely. Navil is open source under the Apache 2.0 license. Install it with pip install navil and run the full security toolkit on your own infrastructure with no limits or fees.',
  },
  {
    question: 'Do I need to provide my own LLM API key?',
    answer:
      'Lite and Elite plans include built-in AI features with no extra key required. Free tier users who want LLM-powered analysis can bring their own key (BYOK) for any OpenAI-compatible provider.',
  },
  {
    question: 'Is my data safe?',
    answer:
      'Yes. No data ever leaves your environment unless you explicitly configure external integrations. For maximum control, self-host Navil on your own infrastructure where you own every byte.',
  },
]

export default function Pricing() {
  const [loading, setLoading] = useState('')
  const [annual, setAnnual] = useState(false)
  const ctaLink = isAuthEnabled() ? '/sign-up' : '/dashboard'

  const handleCheckout = async (plan: 'lite' | 'elite') => {
    setLoading(plan)
    try {
      const res = await api.createCheckout({
        success_url: `${window.location.origin}/dashboard/settings?checkout=success`,
        cancel_url: `${window.location.origin}/pricing`,
      })
      window.location.href = res.checkout_url
    } catch {
      window.location.href = '/dashboard/settings'
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-24">
      {/* ── 1. Header ───────────────────────────────────────────── */}
      <div className="text-center mb-12 animate-fadeIn">
        <h1 className="text-4xl font-bold text-white mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-lg text-gray-400 mb-8">
          Start free. Upgrade when you need more power.
        </p>

        {/* Annual/Monthly toggle */}
        <div className="inline-flex items-center gap-3 bg-gray-900/60 border border-gray-800/60 rounded-full px-1.5 py-1.5">
          <button
            onClick={() => setAnnual(false)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              !annual
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setAnnual(true)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1.5 ${
              annual
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Annual
            <span className="text-[10px] font-bold bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full">
              Save 20%
            </span>
          </button>
        </div>
      </div>

      {/* ── 2. Tier Cards ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {tiers.map((tier, i) => {
          const price = annual ? tier.annualPrice : tier.monthlyPrice
          const monthlyFull = tier.monthlyPrice
          const showDiscount = annual && monthlyFull && price && monthlyFull > price

          return (
            <div
              key={tier.name}
              className={`glass-card p-6 flex flex-col animate-slideUp opacity-0 ${
                tier.highlighted
                  ? 'border-indigo-500/40 ring-1 ring-indigo-500/20 relative'
                  : ''
              }`}
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              {tier.badge && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-semibold bg-indigo-600 text-white rounded-full whitespace-nowrap">
                  {tier.badge}
                </span>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-200 mb-1">{tier.name}</h3>
                <div className="flex items-baseline gap-1 mb-2">
                  {price !== null ? (
                    <>
                      {showDiscount && (
                        <span className="text-lg text-gray-600 line-through mr-1">${monthlyFull}</span>
                      )}
                      <span className="text-3xl font-bold text-white">${price}</span>
                      <span className="text-sm text-gray-500">/month</span>
                    </>
                  ) : (
                    <span className="text-3xl font-bold text-white">Custom</span>
                  )}
                </div>
                {annual && price !== null && price > 0 && (
                  <p className="text-xs text-emerald-400/80">
                    Billed ${price * 12}/year
                  </p>
                )}
                <p className="text-sm text-gray-500 mt-1">{tier.description}</p>
              </div>

              <ul className="space-y-3 mb-4 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <Icon name="check" size={16} className="text-indigo-400 shrink-0 mt-0.5" />
                    <span className="text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              {tier.excluded && (
                <ul className="space-y-3 mb-6">
                  {tier.excluded.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm">
                      <Icon name="x" size={16} className="text-gray-600 shrink-0 mt-0.5" />
                      <span className="text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
              )}

              {!tier.excluded && <div className="mb-6" />}

              {tier.isEnterprise ? (
                <a
                  href="mailto:info@pantheonlab.ai?subject=Navil Enterprise"
                  className="w-full py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 text-center block"
                >
                  Contact Sales
                </a>
              ) : tier.name === 'Elite' ? (
                <button
                  onClick={() => handleCheckout('elite')}
                  disabled={!!loading}
                  className="w-full py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Icon name="sparkles" size={14} />
                  {loading === 'elite' ? 'Redirecting...' : 'Start Elite Trial'}
                </button>
              ) : tier.name === 'Lite' ? (
                <button
                  onClick={() => handleCheckout('lite')}
                  disabled={!!loading}
                  className="w-full py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading === 'lite' ? 'Redirecting...' : 'Start Lite Trial'}
                </button>
              ) : (
                <Link
                  to={ctaLink}
                  className="w-full py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 text-center block"
                >
                  Get Started Free
                </Link>
              )}
            </div>
          )
        })}
      </div>

      {/* ── 3. Self-Host Callout ─────────────────────────────────── */}
      <div className="mt-16 animate-fadeIn">
        <div className="glass-card p-8 border-indigo-500/30 flex flex-col md:flex-row items-center gap-6">
          <div className="flex items-center justify-center w-14 h-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 shrink-0">
            <Icon name="github" size={26} className="text-indigo-400" />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h3 className="text-lg font-semibold text-white mb-1">Prefer to self-host?</h3>
            <p className="text-sm text-gray-400">
              Navil is open source. Run the full security toolkit on your own infrastructure with no limits.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <a
              href="https://github.com/anthropics/navil"
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 flex items-center gap-2"
            >
              <Icon name="github" size={16} />
              View on GitHub
              <Icon name="external-link" size={14} />
            </a>
            <Link
              to="/docs/getting-started"
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              Self-hosting guide
              <Icon name="arrow-right" size={14} />
            </Link>
          </div>
        </div>
      </div>

      {/* ── 4. Feature Comparison Table ──────────────────────────── */}
      <div className="mt-20">
        <h2 className="text-2xl font-bold text-white text-center mb-10">
          Compare plans in detail
        </h2>
        <FeatureComparisonTable />
      </div>

      {/* ── 5. FAQ ──────────────────────────────────────────────── */}
      <div className="mt-20">
        <h2 className="text-2xl font-bold text-white text-center mb-10">
          Frequently asked questions
        </h2>
        <div className="max-w-3xl mx-auto space-y-3">
          {faqItems.map((item) => (
            <details key={item.question} className="faq-item group">
              <summary className="flex items-center justify-between cursor-pointer px-6 py-4 text-sm font-medium text-gray-200 hover:text-white">
                {item.question}
                <Icon
                  name="chevron-down"
                  size={16}
                  className="text-gray-500 transition-transform group-open:rotate-180"
                />
              </summary>
              <div className="px-6 pb-4 text-sm text-gray-400 leading-relaxed">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>

      {/* ── 6. Bottom Note ──────────────────────────────────────── */}
      <div className="mt-16 text-center">
        <p className="text-sm text-gray-500">
          All paid plans include a 14-day free trial. No credit card required to start.
        </p>
      </div>
    </div>
  )
}
