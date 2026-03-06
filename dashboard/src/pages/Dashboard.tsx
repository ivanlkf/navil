import { useEffect, useState } from 'react'
import { api, Overview, Credential, PolicyDecision, FeedbackStats } from '../api'
import StatCard from '../components/StatCard'
import SeverityBadge from '../components/SeverityBadge'
import StatusBadge from '../components/StatusBadge'
import PageHeader from '../components/PageHeader'
import MiniBar from '../components/MiniBar'
import Icon from '../components/Icon'
import RelativeTime from '../components/RelativeTime'
import AnimatedNumber from '../components/AnimatedNumber'
import { SkeletonCard, SkeletonTable } from '../components/Skeleton'

const statusColor: Record<string, string> = {
  OK: 'bg-emerald-500',
  LOW: 'bg-blue-500',
  MEDIUM: 'bg-yellow-500',
  HIGH: 'bg-orange-500',
  CRITICAL: 'bg-red-500',
}

const statusGlow: Record<string, string> = {
  OK: 'shadow-[0_0_6px_rgba(52,211,153,0.5)]',
  LOW: 'shadow-[0_0_6px_rgba(59,130,246,0.5)]',
  MEDIUM: 'shadow-[0_0_6px_rgba(234,179,8,0.5)]',
  HIGH: 'shadow-[0_0_6px_rgba(249,115,22,0.5)]',
  CRITICAL: 'shadow-[0_0_6px_rgba(239,68,68,0.5)]',
}

const barColor: Record<string, string> = {
  OK: 'bg-emerald-500',
  LOW: 'bg-blue-500',
  MEDIUM: 'bg-yellow-500',
  HIGH: 'bg-orange-500',
  CRITICAL: 'bg-red-500',
}

export default function Dashboard() {
  const [data, setData] = useState<Overview | null>(null)
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [decisions, setDecisions] = useState<PolicyDecision[]>([])
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.getOverview(),
      api.getCredentials(),
      api.getPolicyDecisions(),
      api.getFeedbackStats(),
    ])
      .then(([overview, creds, decs, fb]) => {
        setData(overview)
        setCredentials(creds)
        setDecisions(decs)
        setFeedbackStats(fb)
      })
      .catch(e => setError(e.message))
  }, [])

  if (error) return <p className="text-red-400">{error}</p>

  if (!data) return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" subtitle="Agent fleet security overview" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
      </div>
      <SkeletonTable rows={5} cols={5} />
    </div>
  )

  const maxAlerts = Math.max(...data.agent_health.map(h => h.alert_count), 1)

  // Credential status counts
  const credCounts = credentials.reduce(
    (acc, c) => {
      if (c.status === 'ACTIVE') acc.active++
      else if (c.status === 'EXPIRED') acc.expired++
      else if (c.status === 'REVOKED') acc.revoked++
      return acc
    },
    { active: 0, expired: 0, revoked: 0 }
  )
  const credTotal = Math.max(credentials.length, 1)

  // Recent decisions (last 5)
  const recentDecisions = decisions.slice(0, 5)

  return (
    <div className="space-y-8">
      <PageHeader title="Dashboard" subtitle="Agent fleet security overview" />

      {/* Stat cards — 6 cards in 3x2 grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard label="Agents" value={data.total_agents} icon="bot" accent="indigo" index={0} />
        <StatCard label="Active Alerts" value={data.total_alerts} icon="alert" accent={data.critical_alerts > 0 ? 'red' : 'amber'} index={1} />
        <StatCard label="Invocations" value={data.total_invocations} icon="signal" accent="emerald" index={2} />
        <StatCard label="Credentials" value={`${data.active_credentials}/${data.total_credentials}`} icon="key" accent="amber" index={3} />
        <StatCard label="Policy Decisions" value={decisions.length} icon="shield" accent="indigo" index={4} />
        <StatCard label="Feedback Entries" value={feedbackStats?.total_entries || 0} icon="activity" accent="emerald" index={5} />
      </div>

      {/* Agent health grid */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Agent Fleet Health</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {data.agent_health.map((a, i) => (
            <div
              key={a.name}
              className="glass-card p-4 animate-slideUp opacity-0"
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2.5 h-2.5 rounded-full ${statusColor[a.status] || statusColor.OK} ${statusGlow[a.status] || ''}`} />
                <span className="font-medium text-sm truncate">{a.name}</span>
              </div>
              <MiniBar
                value={a.alert_count}
                max={maxAlerts}
                color={barColor[a.status] || 'bg-emerald-500'}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>{a.observations} obs</span>
                {a.alert_count > 0 && <span className="text-orange-400">{a.alert_count} alerts</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two-column: Credential Status + Recent Policy Decisions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Credential Status */}
        <div className="glass-card p-5 animate-slideUp opacity-0" style={{ animationDelay: '0.1s' }}>
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Icon name="key" size={16} className="text-indigo-400" />
            Credential Status
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-sm text-gray-300">Active</span>
                </div>
                <AnimatedNumber value={credCounts.active} className="text-sm font-medium text-emerald-400 block" />
              </div>
              <MiniBar value={credCounts.active} max={credTotal} color="bg-emerald-500" height="h-1.5" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <span className="text-sm text-gray-300">Expired</span>
                </div>
                <AnimatedNumber value={credCounts.expired} className="text-sm font-medium text-amber-400 block" />
              </div>
              <MiniBar value={credCounts.expired} max={credTotal} color="bg-amber-500" height="h-1.5" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="text-sm text-gray-300">Revoked</span>
                </div>
                <AnimatedNumber value={credCounts.revoked} className="text-sm font-medium text-red-400 block" />
              </div>
              <MiniBar value={credCounts.revoked} max={credTotal} color="bg-red-500" height="h-1.5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between">
            <span className="text-xs text-gray-500">Total credentials</span>
            <span className="text-xs font-medium text-gray-400">{credentials.length}</span>
          </div>
        </div>

        {/* Recent Policy Decisions */}
        <div className="glass-card p-5 animate-slideUp opacity-0" style={{ animationDelay: '0.16s' }}>
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Icon name="shield" size={16} className="text-indigo-400" />
            Recent Policy Decisions
          </h3>
          {recentDecisions.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">No policy decisions recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {recentDecisions.map((d) => (
                <div
                  key={d.timestamp + d.tool + d.agent}
                  className="flex items-center gap-3 py-2 border-b border-gray-800/30 last:border-0"
                >
                  <StatusBadge status={d.decision} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="text-gray-300 font-medium truncate">{d.agent}</span>
                      <Icon name="chevron-right" size={12} className="text-gray-600 shrink-0" />
                      <span className="text-gray-400 truncate">{d.tool}</span>
                      <span className="text-gray-600">→</span>
                      <span className="text-indigo-300/80 text-xs font-mono">{d.action}</span>
                    </div>
                    <p className="text-xs text-gray-500 truncate mt-0.5">{d.reason}</p>
                  </div>
                  <RelativeTime timestamp={d.timestamp} className="text-gray-600 text-xs shrink-0" />
                </div>
              ))}
            </div>
          )}
          {decisions.length > 5 && (
            <div className="mt-3 pt-2 border-t border-gray-800/60 text-center">
              <span className="text-xs text-gray-500">{decisions.length - 5} more decisions</span>
            </div>
          )}
        </div>
      </div>

      {/* Recent alerts */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Recent Alerts</h3>
        {data.recent_alerts.length === 0 ? (
          <p className="text-gray-500 text-sm">No alerts. All clear.</p>
        ) : (
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800/60 text-gray-400 text-left bg-gray-900/40">
                  <th className="px-4 py-3 font-medium">Severity</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium">Description</th>
                  <th className="px-4 py-3 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_alerts.map((alert, i) => (
                  <tr
                    key={alert.timestamp + alert.anomaly_type + alert.agent}
                    className="border-b border-gray-800/30 hover:bg-indigo-500/[0.04] animate-fadeIn opacity-0"
                    style={{ animationDelay: `${i * 0.04}s` }}
                  >
                    <td className="px-4 py-3"><SeverityBadge severity={alert.severity} /></td>
                    <td className="px-4 py-3 text-gray-300 font-mono text-xs">{alert.anomaly_type}</td>
                    <td className="px-4 py-3 text-gray-300">{alert.agent}</td>
                    <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{alert.description}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <MiniBar value={alert.confidence * 100} max={100} color="bg-indigo-500" height="h-1" className="w-16" />
                        <span className="text-gray-300 text-xs">{(alert.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
