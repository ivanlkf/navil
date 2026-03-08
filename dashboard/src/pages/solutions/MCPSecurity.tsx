import { Link } from 'react-router-dom'
import Icon, { type IconName } from '../../components/Icon'
import { isAuthEnabled } from '../../auth/ClerkProviderWrapper'

const problems: { icon: IconName; title: string; description: string }[] = [
  {
    icon: 'eye',
    title: 'Blind Spots',
    description:
      'MCP traffic flows between agents and servers with no visibility. Malicious tool calls, data exfiltration, and policy violations go unnoticed.',
  },
  {
    icon: 'chart',
    title: 'No Baselines',
    description:
      'Without behavioral baselines, you cannot distinguish normal agent activity from anomalous behavior or active attacks.',
  },
  {
    icon: 'clock',
    title: 'Manual Response',
    description:
      'Security teams discover threats hours or days after the fact, relying on manual log review instead of real-time automated detection.',
  },
]

const solutions: { icon: IconName; title: string; description: string }[] = [
  {
    icon: 'gateway',
    title: 'Security Proxy',
    description:
      'Intercept and inspect all MCP traffic in real time. Full JSON-RPC visibility with zero changes to your existing agent configuration.',
  },
  {
    icon: 'activity',
    title: 'Anomaly Detection',
    description:
      '12 behavioral detectors with adaptive baselines that learn your fleet\'s normal patterns and flag deviations instantly.',
  },
  {
    icon: 'alert',
    title: 'Real-time Alerts',
    description:
      'Instant notification of security events with severity scoring, contextual explanations, and automated response recommendations.',
  },
]

export default function MCPSecurity() {
  const ctaLink = isAuthEnabled() ? '/sign-up' : '/dashboard'

  return (
    <div className="bg-gray-950">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="hero-glow absolute inset-0 pointer-events-none" />
        <div className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center relative">
          <div
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-400 mb-6 animate-fadeIn"
          >
            <Icon name="shield" size={12} />
            Solution
          </div>
          <h1
            className="text-4xl sm:text-5xl font-bold text-white mb-6 leading-tight animate-slideUp opacity-0"
            style={{ animationDelay: '0.1s' }}
          >
            MCP Security{' '}
            <span className="text-gradient">Monitoring</span>
          </h1>
          <p
            className="text-lg text-gray-400 max-w-2xl mx-auto mb-10 animate-slideUp opacity-0"
            style={{ animationDelay: '0.2s' }}
          >
            Real-time threat detection and behavioral analysis for your entire MCP infrastructure.
            See every tool call, detect anomalies, and respond before damage is done.
          </p>
          <div
            className="flex items-center justify-center gap-4 flex-wrap animate-slideUp opacity-0"
            style={{ animationDelay: '0.3s' }}
          >
            <Link
              to="/docs/getting-started"
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              Get Started
              <Icon name="arrow-right" size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2
            className="text-3xl font-bold text-white mb-3 animate-slideUp opacity-0"
            style={{ animationDelay: '0.1s' }}
          >
            The Problem
          </h2>
          <p
            className="text-gray-400 animate-slideUp opacity-0"
            style={{ animationDelay: '0.15s' }}
          >
            MCP infrastructure is growing faster than security tooling can keep up.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {problems.map((p, i) => (
            <div
              key={p.title}
              className="glass-card p-6 animate-slideUp opacity-0"
              style={{ animationDelay: `${0.1 + i * 0.08}s` }}
            >
              <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center mb-4">
                <Icon name={p.icon} size={20} className="text-red-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-200 mb-2">{p.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{p.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Solution */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2
            className="text-3xl font-bold text-white mb-3 animate-slideUp opacity-0"
            style={{ animationDelay: '0.1s' }}
          >
            The Solution
          </h2>
          <p
            className="text-gray-400 animate-slideUp opacity-0"
            style={{ animationDelay: '0.15s' }}
          >
            Three layers of defense, working together in real time.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {solutions.map((s, i) => (
            <div
              key={s.title}
              className="glass-card p-6 animate-slideUp opacity-0"
              style={{ animationDelay: `${0.1 + i * 0.08}s` }}
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center mb-4">
                <Icon name={s.icon} size={20} className="text-indigo-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-200 mb-2">{s.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div
          className="glass-card p-10 text-center animate-fadeIn"
        >
          <h2 className="text-2xl font-bold text-white mb-3">
            Start monitoring your MCP fleet
          </h2>
          <p className="text-gray-400 mb-8">
            Deploy in minutes. Get full visibility from day one.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/pricing"
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
            >
              View Pricing
              <Icon name="arrow-right" size={16} />
            </Link>
            <Link
              to="/docs"
              className="px-6 py-3 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700"
            >
              Read the Docs
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
