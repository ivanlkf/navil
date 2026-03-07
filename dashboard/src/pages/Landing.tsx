import { Link } from 'react-router-dom'
import Icon, { type IconName } from '../components/Icon'
import SectionHeader from '../components/SectionHeader'
import NewsletterSignup from '../components/NewsletterSignup'
import MockTrafficMonitor from '../components/MockTrafficMonitor'
import MockAnomalyDashboard from '../components/MockAnomalyDashboard'
import MockRemediationEngine from '../components/MockRemediationEngine'

const features: { icon: IconName; title: string; description: string; pro?: boolean }[] = [
  {
    icon: 'scan',
    title: 'MCP Config Scanner',
    description: 'Deep security analysis of MCP server configs — credentials, permissions, protocols, and malicious patterns.',
  },
  {
    icon: 'shield',
    title: 'Policy Engine',
    description: 'Fine-grained access control with agent-level tool policies, rate limits, and data sensitivity rules.',
  },
  {
    icon: 'activity',
    title: 'Anomaly Detection',
    description: '12 behavioral detectors with adaptive baselines — rate spikes, data exfiltration, lateral movement, and more.',
  },
  {
    icon: 'sparkles',
    title: 'LLM-Powered Analysis',
    description: 'AI explains anomalies, generates policies, and auto-remediates threats with BYOK support.',
    pro: true,
  },
  {
    icon: 'pentest',
    title: 'Penetration Testing',
    description: '11 SAFE-MCP attack simulations that probe your defenses without touching real infrastructure.',
    pro: true,
  },
  {
    icon: 'gateway',
    title: 'Security Proxy',
    description: 'Real-time MCP traffic interception with JSON-RPC inspection, auth enforcement, and live monitoring.',
    pro: true,
  },
]

const steps = [
  {
    num: '01',
    icon: 'terminal' as IconName,
    title: 'Connect',
    description: 'Point the proxy at your MCP servers. Zero config changes needed.',
  },
  {
    num: '02',
    icon: 'eye' as IconName,
    title: 'Monitor',
    description: 'Behavioral baselines build automatically. Every tool call is analyzed in real time.',
  },
  {
    num: '03',
    icon: 'shield' as IconName,
    title: 'Protect',
    description: 'Threats are detected, explained, and auto-remediated before they cause damage.',
  },
]

const deepDive = [
  {
    heading: 'Monitor Every MCP Call',
    description:
      'The Navil security proxy sits between your clients and MCP servers, capturing every JSON-RPC message in real time. Get full visibility into tool invocations, argument payloads, and response data without modifying your existing stack.',
    bullets: [
      'Zero-config transparent proxy setup',
      'Full JSON-RPC request/response capture',
      'Live traffic dashboard with filtering',
      'Auth enforcement at the gateway layer',
    ],
    icon: 'gateway' as IconName,
    mockLabel: 'Live Traffic Monitor',
  },
  {
    heading: 'Detect Threats Automatically',
    description:
      'Twelve purpose-built behavioral detectors establish adaptive baselines for every agent and tool. When something deviates — a rate spike, an unusual data access pattern, lateral movement — Navil flags it instantly.',
    bullets: [
      '12 specialized anomaly detectors',
      'Adaptive baselines per agent and tool',
      'Real-time alerting with severity scoring',
      'Exfiltration and lateral movement detection',
    ],
    icon: 'alert' as IconName,
    mockLabel: 'Anomaly Detection Dashboard',
  },
  {
    heading: 'Remediate with AI',
    description:
      'When a threat is detected, Navil\'s LLM engine analyzes the full context — the anomaly, the agent history, and your policies — then recommends or auto-applies the right fix. From blocking a rogue tool call to tightening a policy, remediation happens in seconds.',
    bullets: [
      'LLM-powered root cause analysis',
      'Auto-generated policy recommendations',
      'One-click or fully automated remediation',
      'BYOK support for any OpenAI-compatible model',
    ],
    icon: 'sparkles' as IconName,
    mockLabel: 'AI Remediation Engine',
  },
]

const trustCards: { icon: IconName; title: string; description: string }[] = [
  {
    icon: 'heart',
    title: 'Open Source Core',
    description: 'Apache 2.0 licensed. Inspect every line of code.',
  },
  {
    icon: 'building',
    title: 'Self-Host Option',
    description: 'Deploy on your own infrastructure. Full control.',
  },
  {
    icon: 'shield',
    title: 'Security First',
    description: 'Built by security engineers, for security engineers.',
  },
]

export default function Landing() {
  const ctaLink = '/sign-up'
  const ctaLabel = 'Get Started Free'

  return (
    <div className="bg-gray-950">
      {/* ── 1. Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="hero-glow absolute inset-0 pointer-events-none" />
        <div className="max-w-5xl mx-auto px-6 pt-24 pb-20 text-center relative">
          <div
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-400 mb-6 animate-fadeIn"
          >
            <Icon name="shield" size={12} />
            Supply-chain security for MCP agents
          </div>

          <h1
            className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6 leading-tight animate-slideUp opacity-0"
            style={{ animationDelay: '0.1s' }}
          >
            Secure Your{' '}
            <span className="text-gradient">AI Agent Fleet</span>
          </h1>

          <p
            className="text-lg text-gray-400 max-w-2xl mx-auto mb-10 animate-slideUp opacity-0"
            style={{ animationDelay: '0.2s' }}
          >
            Monitor, detect, and remediate threats across your MCP servers in real time.
            From anomaly detection to automated pentesting — protect your agents at every layer.
          </p>

          <div
            className="flex items-center justify-center gap-4 flex-wrap animate-slideUp opacity-0"
            style={{ animationDelay: '0.3s' }}
          >
            <Link
              to={ctaLink}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              {ctaLabel}
              <Icon name="arrow-right" size={16} />
            </Link>
            <Link
              to="/pricing"
              className="px-6 py-3 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700"
            >
              View Pricing
            </Link>
          </div>

          {/* Terminal mock */}
          <div
            className="max-w-2xl mx-auto mt-14 animate-slideUp opacity-0"
            style={{ animationDelay: '0.45s' }}
          >
            <div className="rounded-xl border border-gray-700/60 bg-gray-900/80 backdrop-blur-sm overflow-hidden shadow-2xl">
              {/* Window chrome */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
                <span className="w-3 h-3 rounded-full bg-red-500/80" />
                <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <span className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-3 text-xs text-gray-500 font-mono">terminal</span>
              </div>
              {/* Terminal body */}
              <div className="p-5 font-mono text-sm leading-relaxed text-left">
                <p className="text-gray-400">
                  <span className="text-green-400">$</span> navil scan config.json
                </p>
                <p className="mt-3 text-indigo-400">
                  [navil] Scanning MCP server configuration...
                </p>
                <p className="text-yellow-400">
                  [warn] Credential exposed in env block &mdash; line 14
                </p>
                <p className="text-yellow-400">
                  [warn] Wildcard tool permission detected &mdash; line 28
                </p>
                <p className="text-red-400">
                  [crit] Unsigned remote server URL &mdash; line 33
                </p>
                <p className="mt-3 text-emerald-400">
                  Scan complete: 2 warnings, 1 critical. Remediation plan ready.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. Features Grid ────────────────────────────────────── */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <SectionHeader
          title="Everything you need to secure MCP"
          subtitle="Six layers of defense, one unified dashboard."
          centered
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-14">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="glass-card p-6 animate-slideUp opacity-0"
              style={{ animationDelay: `${0.1 + i * 0.08}s` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                  <Icon name={f.icon} size={20} className="text-indigo-400" />
                </div>
                {f.pro && (
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-violet-500/15 text-violet-400 border border-violet-500/30 rounded-full">
                    PAID
                  </span>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-200 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 4. Product Deep-Dive ────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <SectionHeader
          eyebrow="Deep Dive"
          title="Purpose-built for MCP security"
          subtitle="From traffic inspection to AI-powered remediation, Navil covers every layer of the agent stack."
          centered
        />

        <div className="mt-16 space-y-24">
          {deepDive.map((item, idx) => {
            const reversed = idx % 2 !== 0
            return (
              <div
                key={item.heading}
                className={`flex flex-col ${reversed ? 'lg:flex-row-reverse' : 'lg:flex-row'} gap-10 lg:gap-16 items-center`}
              >
                {/* Text side */}
                <div className="flex-1 space-y-5">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                    <Icon name={item.icon} size={20} className="text-indigo-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white">{item.heading}</h3>
                  <p className="text-gray-400 leading-relaxed">{item.description}</p>
                  <ul className="space-y-2">
                    {item.bullets.map((b) => (
                      <li key={b} className="flex items-center gap-2 text-sm text-gray-300">
                        <Icon name="check" size={14} className="text-indigo-400 shrink-0" />
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Mock UI side */}
                <div className="flex-1 w-full">
                  <div className="glass-card p-1 rounded-xl">
                    <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-700/50">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
                      <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
                      <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
                      <span className="ml-2 text-xs text-gray-500">{item.mockLabel}</span>
                    </div>
                    <div className="bg-gray-900/50 rounded-b-lg overflow-hidden">
                      {idx === 0 && <MockTrafficMonitor />}
                      {idx === 1 && <MockAnomalyDashboard />}
                      {idx === 2 && <MockRemediationEngine />}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── 5. How It Works ─────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-20">
        <SectionHeader
          title="How it works"
          subtitle="Three steps to a secured agent fleet."
          centered
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-14">
          {steps.map((s, i) => (
            <div
              key={s.num}
              className="text-center animate-slideUp opacity-0"
              style={{ animationDelay: `${0.1 + i * 0.1}s` }}
            >
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-4">
                <Icon name={s.icon} size={24} className="text-indigo-400" />
              </div>
              <div className="text-xs text-indigo-400 font-mono mb-2">{s.num}</div>
              <h3 className="text-lg font-medium text-gray-200 mb-2">{s.title}</h3>
              <p className="text-sm text-gray-500">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 6. Security / Trust Messaging ───────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {trustCards.map((card, i) => (
            <div
              key={card.title}
              className="glass-card p-8 text-center animate-slideUp opacity-0"
              style={{ animationDelay: `${0.1 + i * 0.1}s` }}
            >
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-5">
                <Icon name={card.icon} size={22} className="text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{card.title}</h3>
              <p className="text-sm text-gray-400">{card.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 8. Bottom CTA + Newsletter ──────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 pb-20 space-y-10">
        <div className="glass-card p-10 text-center animate-fadeIn">
          <h2 className="text-2xl font-bold text-white mb-3">
            Ready to secure your agents?
          </h2>
          <p className="text-gray-400 mb-8">
            Start monitoring in minutes. No credit card required.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to={ctaLink}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              {ctaLabel}
              <Icon name="arrow-right" size={16} />
            </Link>
            <Link
              to="/pricing"
              className="px-6 py-3 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700"
            >
              View Pricing
            </Link>
          </div>
        </div>

        <NewsletterSignup />
      </section>
    </div>
  )
}
