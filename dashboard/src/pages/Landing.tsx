import { Link } from 'react-router-dom'
import Icon, { type IconName } from '../components/Icon'
import SectionHeader from '../components/SectionHeader'
import NewsletterSignup from '../components/NewsletterSignup'
import LogoCloud from '../components/LogoCloud'
import TestimonialCard from '../components/TestimonialCard'
import FeatureComparisonTable from '../components/FeatureComparisonTable'
import MockTrafficMonitor from '../components/MockTrafficMonitor'
import MockAnomalyDashboard from '../components/MockAnomalyDashboard'
import MockRemediationEngine from '../components/MockRemediationEngine'

/* ─── Data ───────────────────────────────────────────────────────── */

const heroStats = [
  { value: '12', label: 'Anomaly Detectors' },
  { value: '11', label: 'Pentest Simulations' },
  { value: '<5min', label: 'Setup Time' },
  { value: '100%', label: 'Open Source Core' },
]

const primaryFeatures: {
  icon: IconName
  title: string
  description: string
  bullets: string[]
  accent: string
}[] = [
  {
    icon: 'gateway',
    title: 'Security Proxy',
    description:
      'Sits between your clients and MCP servers, capturing every JSON-RPC message in real time with zero config changes.',
    bullets: [
      'Transparent traffic interception',
      'Auth enforcement at the gateway',
      'Live request/response inspection',
      'Rate limiting & payload filtering',
    ],
    accent: 'emerald',
  },
  {
    icon: 'activity',
    title: 'Anomaly Detection',
    description:
      '12 behavioral detectors establish adaptive baselines per agent. When something deviates, Navil flags it instantly.',
    bullets: [
      'Rate spikes & brute-force detection',
      'Data exfiltration patterns',
      'Lateral movement tracking',
      'Privilege escalation alerts',
    ],
    accent: 'amber',
  },
]

const secondaryFeatures: { icon: IconName; title: string; description: string; tag?: string }[] = [
  {
    icon: 'scan',
    title: 'Config Scanner',
    description: 'Deep analysis of MCP configs for credentials, dangerous permissions, and unsigned server URLs.',
  },
  {
    icon: 'shield',
    title: 'Policy Engine',
    description: 'Agent-level tool policies with allowlists, denylists, rate limits, and data sensitivity rules.',
  },
  {
    icon: 'sparkles',
    title: 'AI Remediation',
    description: 'LLM explains anomalies, generates policies, and auto-fixes threats. Bring your own key.',
    tag: 'AI',
  },
  {
    icon: 'pentest',
    title: 'Pentest Engine',
    description: '11 SAFE-MCP attack simulations probe your defenses without touching real infrastructure.',
    tag: 'PRO',
  },
]

const deepDive = [
  {
    heading: 'Monitor Every MCP Call',
    description:
      'The Navil security proxy sits between your clients and MCP servers, capturing every JSON-RPC message in real time. Get full visibility into tool invocations, argument payloads, and response data — without modifying your existing stack.',
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
      "When a threat is detected, Navil's LLM engine analyzes the full context — the anomaly, the agent history, and your policies — then recommends or auto-applies the right fix. Remediation happens in seconds, not hours.",
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

const steps = [
  {
    num: '01',
    icon: 'terminal' as IconName,
    title: 'Install & Connect',
    description: 'pip install navil, point the proxy at your MCP servers. One command, zero config changes.',
    code: 'navil proxy start --target localhost:3000',
  },
  {
    num: '02',
    icon: 'eye' as IconName,
    title: 'Baselines Build',
    description: 'Behavioral models calibrate automatically within minutes. Every tool call is profiled.',
    code: '[navil] 12 detectors active, 5 agents profiled',
  },
  {
    num: '03',
    icon: 'shield' as IconName,
    title: 'Threats Blocked',
    description: 'Anomalies are detected, explained by AI, and auto-remediated before damage occurs.',
    code: '[alert] Exfiltration blocked → policy applied',
  },
]

const testimonials = [
  {
    quote: 'Navil caught a credential exfiltration pattern in our staging environment that our existing monitoring completely missed. The behavioral detection is genuinely impressive.',
    author: 'Sarah Chen',
    role: 'Head of Security',
    company: 'Sentinel AI',
  },
  {
    quote: 'We went from zero visibility into our MCP tool calls to full observability in under 5 minutes. The proxy setup is dead simple and the dashboard is beautiful.',
    author: 'Marcus Johnson',
    role: 'Platform Lead',
    company: 'TechFlow',
  },
  {
    quote: "The auto-remediation feature is a game changer. It blocked a rogue agent and tightened our policy before we even saw the alert. That's the kind of security tooling we need.",
    author: 'Elena Rodriguez',
    role: 'CTO',
    company: 'CloudSec',
  },
]

const trustBadges = [
  { icon: 'heart' as IconName, label: 'Apache 2.0 Licensed' },
  { icon: 'lock' as IconName, label: 'SOC 2 Ready' },
  { icon: 'building' as IconName, label: 'Self-Host Available' },
  { icon: 'globe' as IconName, label: 'GDPR Compliant' },
]

/* ─── Component ──────────────────────────────────────────────────── */

export default function Landing() {
  const ctaLink = '/sign-up'
  const ctaLabel = 'Get Started Free'

  return (
    <div className="bg-gray-950">
      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Gradient mesh background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="hero-glow" />
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-indigo-600/8 rounded-full blur-[120px]" />
          <div className="absolute top-40 right-1/4 w-80 h-80 bg-violet-600/6 rounded-full blur-[100px]" />
          <div className="absolute -bottom-20 left-1/2 w-[600px] h-64 bg-indigo-500/5 rounded-full blur-[80px] -translate-x-1/2" />
        </div>

        <div className="max-w-5xl mx-auto px-6 pt-28 pb-8 text-center relative">
          {/* Eyebrow badge */}
          <div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-400 mb-8 animate-fadeIn"
          >
            <Icon name="shield" size={12} />
            Supply-chain security for MCP agents
            <span className="w-px h-3 bg-indigo-500/30" />
            <span className="text-indigo-300 font-medium">Now in public beta</span>
          </div>

          <h1
            className="text-4xl sm:text-5xl md:text-7xl font-bold text-white mb-6 leading-[1.1] tracking-tight animate-slideUp opacity-0"
            style={{ animationDelay: '0.1s' }}
          >
            Stop Threats Before
            <br />
            <span className="text-gradient">They Reach Your Agents</span>
          </h1>

          <p
            className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 animate-slideUp opacity-0"
            style={{ animationDelay: '0.2s' }}
          >
            Real-time monitoring, behavioral anomaly detection, and AI-powered remediation
            for every MCP server in your stack.
          </p>

          {/* CTA buttons */}
          <div
            className="flex items-center justify-center gap-4 flex-wrap animate-slideUp opacity-0"
            style={{ animationDelay: '0.3s' }}
          >
            <Link
              to={ctaLink}
              className="group px-7 py-3.5 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500 transition-all hover:shadow-lg hover:shadow-indigo-500/25 flex items-center gap-2"
            >
              {ctaLabel}
              <Icon name="arrow-right" size={16} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link
              to="/docs/getting-started"
              className="px-7 py-3.5 bg-white/5 text-gray-300 border border-gray-700/80 rounded-lg text-sm font-medium hover:bg-white/10 hover:border-gray-600 transition-all flex items-center gap-2"
            >
              <Icon name="code" size={16} />
              View Documentation
            </Link>
          </div>

          <p
            className="text-xs text-gray-600 mt-4 animate-slideUp opacity-0"
            style={{ animationDelay: '0.35s' }}
          >
            Free forever for up to 3 agents. No credit card required.
          </p>
        </div>

        {/* Terminal mock — elevated with glow */}
        <div className="max-w-3xl mx-auto px-6 pb-20 relative">
          <div
            className="animate-slideUp opacity-0"
            style={{ animationDelay: '0.45s' }}
          >
            {/* Glow behind terminal */}
            <div className="absolute inset-x-10 top-10 bottom-10 bg-indigo-500/10 rounded-3xl blur-3xl" />

            <div className="relative rounded-xl border border-gray-700/60 bg-gray-900/90 backdrop-blur-sm overflow-hidden shadow-2xl shadow-black/50">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800/80 bg-gray-900/50">
                <span className="w-3 h-3 rounded-full bg-red-500/80" />
                <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <span className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-3 text-xs text-gray-500 font-mono">terminal</span>
              </div>
              <div className="p-6 font-mono text-sm leading-relaxed text-left">
                <p className="text-gray-500">
                  <span className="text-emerald-400">$</span>{' '}
                  <span className="text-gray-300">pip install navil</span>
                </p>
                <p className="text-gray-500 mt-1">
                  <span className="text-emerald-400">$</span>{' '}
                  <span className="text-gray-300">navil proxy start --target mcp://localhost:3000</span>
                </p>
                <p className="mt-4 text-indigo-400">[navil] Proxy listening on :8484</p>
                <p className="text-indigo-400">[navil] 12 anomaly detectors active</p>
                <p className="text-indigo-400">[navil] Behavioral baselines initializing...</p>
                <p className="mt-3 text-yellow-400">[warn] Rate spike detected: data-reader (42 calls/min vs baseline 8)</p>
                <p className="text-red-400">[crit] Potential exfiltration: data-reader accessing /etc/passwd</p>
                <p className="mt-3 text-emerald-400">[auto] Agent blocked. Policy updated. Incident logged.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats Bar ──────────────────────────────────────────── */}
      <section className="border-y border-gray-800/60 bg-gray-900/30">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {heroStats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-2xl sm:text-3xl font-bold text-white">{s.value}</p>
                <p className="text-xs sm:text-sm text-gray-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Social Proof ───────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <LogoCloud title="Trusted by security-conscious teams" />
      </section>

      {/* ── Primary Features (2-up) ────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <SectionHeader
          eyebrow="Core Platform"
          title="Real-time protection for your agent fleet"
          subtitle="Two foundational layers that work together: intercept everything, detect anything."
          centered
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-14">
          {primaryFeatures.map((f, i) => (
            <div
              key={f.title}
              className={`glass-card p-8 border ${
                f.accent === 'emerald' ? 'border-emerald-500/10 hover:border-emerald-500/20' : 'border-amber-500/10 hover:border-amber-500/20'
              } transition-colors`}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  f.accent === 'emerald' ? 'bg-emerald-500/10' : 'bg-amber-500/10'
                }`}>
                  <Icon name={f.icon} size={20} className={
                    f.accent === 'emerald' ? 'text-emerald-400' : 'text-amber-400'
                  } />
                </div>
                <h3 className="text-lg font-semibold text-white">{f.title}</h3>
              </div>
              <p className="text-gray-400 mb-6 leading-relaxed">{f.description}</p>
              <ul className="space-y-2.5">
                {f.bullets.map((b) => (
                  <li key={b} className="flex items-center gap-2.5 text-sm text-gray-300">
                    <Icon name="check" size={14} className={
                      f.accent === 'emerald' ? 'text-emerald-400' : 'text-amber-400'
                    } />
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ── Secondary Features (4-grid) ────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {secondaryFeatures.map((f, i) => (
            <div
              key={f.title}
              className="glass-card p-6 group hover:border-indigo-500/20 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center group-hover:bg-indigo-500/15 transition-colors">
                  <Icon name={f.icon} size={20} className="text-indigo-400" />
                </div>
                {f.tag && (
                  <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${
                    f.tag === 'AI'
                      ? 'bg-violet-500/15 text-violet-400 border border-violet-500/30'
                      : 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                  }`}>
                    {f.tag}
                  </span>
                )}
              </div>
              <h3 className="text-sm font-semibold text-gray-200 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Product Deep-Dive ──────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 border-t border-gray-800/40">
        <SectionHeader
          eyebrow="Deep Dive"
          title="Purpose-built for MCP security"
          subtitle="From traffic inspection to AI-powered remediation, Navil covers every layer of the agent stack."
          centered
        />

        <div className="mt-20 space-y-28">
          {deepDive.map((item, idx) => {
            const reversed = idx % 2 !== 0
            return (
              <div
                key={item.heading}
                className={`flex flex-col ${reversed ? 'lg:flex-row-reverse' : 'lg:flex-row'} gap-12 lg:gap-16 items-center`}
              >
                <div className="flex-1 space-y-5">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                    <Icon name={item.icon} size={20} className="text-indigo-400" />
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-bold text-white">{item.heading}</h3>
                  <p className="text-gray-400 leading-relaxed">{item.description}</p>
                  <ul className="space-y-2.5 pt-2">
                    {item.bullets.map((b) => (
                      <li key={b} className="flex items-center gap-2.5 text-sm text-gray-300">
                        <Icon name="check" size={14} className="text-indigo-400 shrink-0" />
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex-1 w-full">
                  <div className="glass-card p-1 rounded-xl shadow-xl shadow-black/20">
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

      {/* ── How It Works ───────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-t border-gray-800/40">
        <SectionHeader
          title="Secured in three commands"
          subtitle="From zero to protected in under 5 minutes."
          centered
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-14">
          {steps.map((s, i) => (
            <div
              key={s.num}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <Icon name={s.icon} size={20} className="text-indigo-400" />
                </div>
                <span className="text-xs text-indigo-400 font-mono font-bold">{s.num}</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-200 mb-2">{s.title}</h3>
              <p className="text-sm text-gray-500 mb-4">{s.description}</p>
              <div className="bg-gray-900/80 rounded-lg px-3 py-2 font-mono text-xs text-indigo-400 border border-gray-800/60">
                {s.code}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Testimonials ───────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 border-t border-gray-800/40">
        <SectionHeader
          eyebrow="What Teams Say"
          title="Trusted by security engineers"
          centered
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-14">
          {testimonials.map((t, i) => (
            <div
              key={t.author}
            >
              <TestimonialCard {...t} />
            </div>
          ))}
        </div>
      </section>

      {/* ── Feature Comparison ─────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-t border-gray-800/40">
        <SectionHeader
          eyebrow="Plans"
          title="Compare features across plans"
          subtitle="Start free. Scale as your agent fleet grows."
          centered
        />

        <div className="mt-14">
          <FeatureComparisonTable />
        </div>

        <div className="text-center mt-8">
          <Link
            to="/pricing"
            className="text-sm text-indigo-400 hover:text-indigo-300 font-medium"
          >
            View detailed pricing &rarr;
          </Link>
        </div>
      </section>

      {/* ── Trust Badges ───────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-16 border-t border-gray-800/40">
        <div className="flex items-center justify-center gap-8 flex-wrap">
          {trustBadges.map((badge) => (
            <div key={badge.label} className="flex items-center gap-2 text-gray-500">
              <Icon name={badge.icon} size={16} className="text-gray-600" />
              <span className="text-xs font-medium">{badge.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Bottom CTA ─────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 pb-12">
        <div className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-gray-900 to-violet-500/10 p-12 text-center">
          {/* Decorative glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-indigo-500/15 rounded-full blur-3xl" />

          <div className="relative">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to secure your agents?
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Join hundreds of teams protecting their MCP infrastructure.
              Start monitoring in minutes.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link
                to={ctaLink}
                className="group px-7 py-3.5 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500 transition-all hover:shadow-lg hover:shadow-indigo-500/25 flex items-center gap-2"
              >
                {ctaLabel}
                <Icon name="arrow-right" size={16} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                to="/pricing"
                className="px-7 py-3.5 bg-white/5 text-gray-300 border border-gray-700/80 rounded-lg text-sm font-medium hover:bg-white/10 transition-all"
              >
                View Pricing
              </Link>
            </div>
            <p className="text-xs text-gray-600 mt-4">
              Free forever for small teams. No credit card required.
            </p>
          </div>
        </div>
      </section>

      {/* ── Newsletter ─────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <NewsletterSignup />
      </section>
    </div>
  )
}
