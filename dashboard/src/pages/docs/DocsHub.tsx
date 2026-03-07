import { Link } from 'react-router-dom'
import Icon, { type IconName } from '../../components/Icon'

const quickStart = [
  {
    title: 'Install Navil',
    code: 'pip install navil',
    link: '/docs/getting-started',
  },
  {
    title: 'Scan a Config',
    code: 'navil scan config.json',
    link: '/docs/configuration',
  },
  {
    title: 'Start Dashboard',
    code: 'navil cloud serve',
    link: '/docs/getting-started',
  },
]

const featureDocs: {
  icon: IconName
  title: string
  description: string
  link: string
}[] = [
  {
    icon: 'shield',
    title: 'Policy Engine',
    description: 'YAML-based access control for MCP agent tool calls with rate limiting and sensitivity rules.',
    link: '/docs/policy-engine',
  },
  {
    icon: 'gateway',
    title: 'Security Proxy',
    description: 'Real-time traffic interception with JSON-RPC inspection and auth enforcement.',
    link: '/docs/proxy',
  },
  {
    icon: 'pentest',
    title: 'Pentest Engine',
    description: '11 SAFE-MCP attack simulations that probe defenses without touching real infrastructure.',
    link: '/docs/pentest',
  },
  {
    icon: 'sparkles',
    title: 'LLM Integration',
    description: 'AI-powered anomaly explanation, config analysis, policy generation, and auto-remediation.',
    link: '/docs/llm',
  },
  {
    icon: 'settings',
    title: 'Configuration',
    description: 'Environment variables, config file format, and policy YAML reference.',
    link: '/docs/configuration',
  },
  {
    icon: 'code',
    title: 'API Reference',
    description: 'Complete REST API documentation for all endpoints and integrations.',
    link: '/docs/api',
  },
]

export default function DocsHub() {
  return (
    <div className="animate-fadeIn">
      {/* Hero */}
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-white mb-3">Navil Documentation</h1>
        <p className="text-lg text-gray-400">
          Everything you need to secure your MCP agent fleet.
        </p>
      </div>

      {/* Quick Start */}
      <section className="mb-14">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Quick Start
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickStart.map((item) => (
            <Link
              key={item.title}
              to={item.link}
              className="glass-card p-5 hover:border-indigo-500/40 transition-colors group"
            >
              <h3 className="text-sm font-semibold text-white mb-3">{item.title}</h3>
              <div className="bg-gray-950/60 rounded-lg px-3 py-2 mb-4 font-mono text-sm text-indigo-300">
                $ {item.code}
              </div>
              <span className="text-xs text-indigo-400 group-hover:underline flex items-center gap-1">
                Learn more
                <Icon name="arrow-right" size={12} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Feature Docs Grid */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Feature Documentation
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {featureDocs.map((feature) => (
            <Link
              key={feature.title}
              to={feature.link}
              className="glass-card p-5 hover:border-indigo-500/40 transition-colors group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Icon name={feature.icon} size={18} />
                </div>
                <Icon
                  name="arrow-right"
                  size={16}
                  className="text-gray-600 group-hover:text-indigo-400 transition-colors mt-1"
                />
              </div>
              <h3 className="text-sm font-semibold text-white mb-1.5">{feature.title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{feature.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
