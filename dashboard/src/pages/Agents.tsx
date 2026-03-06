import { useEffect, useState } from 'react'
import { api, Agent, AgentDetail } from '../api'
import SeverityBadge from '../components/SeverityBadge'
import PageHeader from '../components/PageHeader'
import MiniBar from '../components/MiniBar'
import Icon from '../components/Icon'
import { SkeletonCard, SkeletonTable } from '../components/Skeleton'

const anomalyBarColor: Record<string, string> = {
  OK: 'bg-emerald-500',
  LOW: 'bg-blue-500',
  MEDIUM: 'bg-yellow-500',
  HIGH: 'bg-orange-500',
  CRITICAL: 'bg-red-500',
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<AgentDetail | null>(null)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.getAgents().then(a => { setAgents(a); setLoaded(true) }).catch(e => setError(e.message))
  }, [])

  useEffect(() => {
    if (selected) {
      setDetail(null)
      api.getAgent(selected).then(setDetail).catch(e => setError(e.message))
    }
  }, [selected])

  if (error) return <p className="text-red-400">{error}</p>

  if (!loaded) return (
    <div className="space-y-6">
      <PageHeader title="Agent Fleet" subtitle="Monitor and inspect agent behavior" />
      <SkeletonTable rows={6} cols={5} />
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader title="Agent Fleet" subtitle="Monitor and inspect agent behavior" />

      {/* Agent table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800/60 text-gray-400 text-left bg-gray-900/40">
              <th className="px-4 py-3 font-medium">Agent</th>
              <th className="px-4 py-3 font-medium">Observations</th>
              <th className="px-4 py-3 font-medium">Alerts</th>
              <th className="px-4 py-3 font-medium">Tools</th>
              <th className="px-4 py-3 font-medium">Avg Duration</th>
              <th className="px-4 py-3 font-medium">Avg Data</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a, i) => (
              <tr
                key={a.name}
                onClick={() => setSelected(a.name)}
                className={`border-b border-gray-800/30 cursor-pointer transition-colors animate-fadeIn opacity-0 ${
                  selected === a.name
                    ? 'bg-indigo-500/10 border-l-2 border-l-indigo-500'
                    : 'hover:bg-indigo-500/[0.04]'
                }`}
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                <td className="px-4 py-3 font-medium text-gray-200">{a.name}</td>
                <td className="px-4 py-3 text-gray-400">{a.observations}</td>
                <td className="px-4 py-3">
                  {a.alert_count > 0 ? (
                    <span className="text-orange-400 font-medium">{a.alert_count}</span>
                  ) : (
                    <span className="text-gray-600">0</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 flex-wrap">
                    {a.known_tools.slice(0, 4).map(t => (
                      <span key={t} className="px-2 py-0.5 bg-indigo-500/10 text-indigo-300/80 border border-indigo-500/20 rounded-full text-xs">
                        {t}
                      </span>
                    ))}
                    {a.known_tools.length > 4 && <span className="text-xs text-gray-600">+{a.known_tools.length - 4}</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{a.duration_mean}ms</td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{a.data_volume_mean}B</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agent detail panel */}
      {selected && (
        <div className="space-y-4 animate-slideUp">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Icon name="bot" size={20} className="text-indigo-400" />
            {selected}
            <button
              onClick={() => setSelected(null)}
              className="ml-auto flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
            >
              <Icon name="x" size={14} /> close
            </button>
          </h3>

          {!detail ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Baseline info */}
              <div className="glass-card p-4">
                <h4 className="font-medium text-gray-300 mb-4">Adaptive Baseline</h4>
                <div className="space-y-3">
                  {(() => {
                    const entries = Object.entries(detail.baseline).filter(([, v]) => typeof v === 'number')
                    const maxVal = Math.max(...entries.map(([, v]) => Math.abs(v as number)), 1)
                    return entries.map(([k, v]) => {
                      const numVal = v as number
                      return (
                        <div key={k}>
                          <div className="flex justify-between mb-1">
                            <p className="text-gray-500 text-xs">{k.replace(/_/g, ' ')}</p>
                            <p className="text-gray-300 font-mono text-xs">{numVal.toFixed(2)}</p>
                          </div>
                          <MiniBar value={Math.abs(numVal)} max={maxVal} color="bg-indigo-500/60" height="h-1" />
                        </div>
                      )
                    })
                  })()}
                </div>
              </div>

              {/* Anomaly scores */}
              <div className="glass-card p-4">
                <h4 className="font-medium text-gray-300 mb-4">Anomaly Scores</h4>
                {detail.anomaly_scores.length === 0 ? (
                  <p className="text-gray-500 text-sm">No anomaly scores computed yet.</p>
                ) : (
                  <div className="space-y-3">
                    {detail.anomaly_scores.map((s) => (
                      <div key={`${s.anomaly_type}-${s.level}`}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <SeverityBadge severity={s.level} />
                            <span className="text-sm text-gray-300 font-mono">{s.anomaly_type}</span>
                          </div>
                          <span className="text-sm font-medium text-gray-400">{(s.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <MiniBar
                          value={s.confidence * 100}
                          max={100}
                          color={anomalyBarColor[s.level] || 'bg-gray-500'}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Agent alerts */}
              {detail.alerts.length > 0 && (
                <div className="lg:col-span-2 glass-card p-4">
                  <h4 className="font-medium text-gray-300 mb-3">Active Alerts ({detail.alerts.length})</h4>
                  <div className="space-y-2">
                    {detail.alerts.map((alert) => (
                      <div key={`${alert.severity}-${alert.timestamp}-${alert.description.slice(0, 40)}`} className="flex items-start gap-3 py-2 border-b border-gray-800/30 last:border-0">
                        <SeverityBadge severity={alert.severity} />
                        <div className="flex-1">
                          <p className="text-sm text-gray-300">{alert.description}</p>
                          <p className="text-xs text-gray-500 mt-1">{alert.recommended_action}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
