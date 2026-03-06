import { useEffect, useState } from 'react'
import { api, Alert, AnomalyExplanation } from '../api'
import SeverityBadge from '../components/SeverityBadge'
import PageHeader from '../components/PageHeader'
import Icon from '../components/Icon'
import RelativeTime from '../components/RelativeTime'
import LLMErrorCard from '../components/LLMErrorCard'
import UpgradePrompt from '../components/UpgradePrompt'
import useBilling from '../hooks/useBilling'

const severities = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function Alerts() {
  const { canUseLLM, setPlan } = useBilling()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [allAlerts, setAllAlerts] = useState<Alert[]>([])
  const [filter, setFilter] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [explaining, setExplaining] = useState<number | null>(null)
  const [explanations, setExplanations] = useState<Record<number, AnomalyExplanation>>({})
  const [llmError, setLlmError] = useState<Record<number, { message: string; type: string }>>({})

  // Fetch all alerts once for counts
  useEffect(() => {
    api.getAlerts().then(setAllAlerts).catch(e => setError(e.message))
  }, [])

  useEffect(() => {
    api.getAlerts(filter || undefined)
      .then(setAlerts)
      .catch(e => setError(e.message))
  }, [filter])

  // Compute counts per severity
  const alertCounts: Record<string, number> = { '': allAlerts.length }
  for (const a of allAlerts) {
    alertCounts[a.severity] = (alertCounts[a.severity] || 0) + 1
  }

  if (error) return <p className="text-red-400">{error}</p>

  return (
    <div className="space-y-6">
      <PageHeader title="Alerts" subtitle={`${alerts.length} alert${alerts.length !== 1 ? 's' : ''} detected`}>
        <div className="flex gap-2">
          {severities.map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 text-xs rounded-lg border flex items-center gap-1.5 ${
                filter === s
                  ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300 shadow-[0_0_8px_rgba(99,102,241,0.15)]'
                  : 'bg-gray-900/60 border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300'
              }`}
            >
              {s || 'All'}
              {alertCounts[s] !== undefined && (
                <span className="bg-gray-800 text-gray-400 text-[10px] px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
                  {alertCounts[s]}
                </span>
              )}
            </button>
          ))}
        </div>
      </PageHeader>

      {alerts.length === 0 ? (
        <div className="text-center py-16 animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4">
            <Icon name="check" size={32} className="text-emerald-400" />
          </div>
          <p className="text-gray-400">No alerts{filter ? ` with severity ${filter}` : ''}. Looking good!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert, i) => (
            <div
              key={alert.timestamp + alert.anomaly_type + alert.agent}
              className="glass-card overflow-hidden animate-slideUp opacity-0"
              style={{ animationDelay: `${i * 0.03}s` }}
            >
              <div
                onClick={() => setExpanded(expanded === i ? null : i)}
                className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-gray-800/30"
              >
                <SeverityBadge severity={alert.severity} />
                <span className="font-mono text-xs text-gray-400 w-40 shrink-0">{alert.anomaly_type}</span>
                <span className="text-sm text-gray-300 w-32 shrink-0">{alert.agent}</span>
                <span className="text-sm text-gray-400 flex-1 truncate">{alert.description}</span>
                <span className="text-sm text-gray-500 w-16 text-right">{(alert.confidence * 100).toFixed(0)}%</span>
                <Icon
                  name="chevron-down"
                  size={16}
                  className={`text-gray-500 transition-transform duration-200 ${expanded === i ? 'rotate-0' : '-rotate-90'}`}
                />
              </div>

              {/* Animated expand section */}
              <div
                className={`overflow-hidden transition-all duration-300 ease-out ${
                  expanded === i ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                }`}
              >
                <div className="px-4 pb-4 pt-2 border-t border-gray-800/60 space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Evidence</p>
                    <ul className="space-y-1">
                      {alert.evidence.map((e, j) => (
                        <li key={j} className="text-sm text-gray-400 flex items-start gap-2">
                          <Icon name="chevron-right" size={12} className="text-gray-600 mt-0.5 shrink-0" />
                          {e}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Recommended Action</p>
                    <p className="text-sm text-indigo-400">{alert.recommended_action}</p>
                  </div>
                  {/* AI Explanation */}
                  <div className="pt-2 border-t border-gray-800/30">
                    {!explanations[i] ? (
                      canUseLLM ? (
                        <button
                          onClick={async (e) => {
                            e.stopPropagation()
                            setExplaining(i)
                            setLlmError(prev => { const next = { ...prev }; delete next[i]; return next })
                            try {
                              const result = await api.explainAnomaly(alert)
                              setExplanations(prev => ({ ...prev, [i]: result }))
                            } catch (err: unknown) {
                              const msg = err instanceof Error ? err.message : String(err)
                              const errType = err instanceof Error && 'errorType' in err ? (err as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                              setLlmError(prev => ({ ...prev, [i]: { message: msg, type: errType } }))
                            } finally {
                              setExplaining(null)
                            }
                          }}
                          disabled={explaining === i}
                          className="px-3 py-1.5 text-xs bg-violet-500/15 text-violet-400 border border-violet-500/30 rounded-lg hover:bg-violet-500/25 flex items-center gap-1.5 disabled:opacity-50"
                        >
                          <Icon name="sparkles" size={13} className={explaining === i ? 'animate-spin' : ''} />
                          {explaining === i ? 'Analyzing...' : 'Explain with AI'}
                        </button>
                      ) : (
                        <UpgradePrompt feature="AI-powered alert analysis" onUpgrade={() => setPlan('pro')} compact />
                      )
                    ) : (
                      <div className="space-y-2 animate-fadeIn">
                        <div className="flex items-center gap-2">
                          <Icon name="sparkles" size={14} className="text-violet-400" />
                          <span className="text-xs font-medium text-violet-400">AI Analysis</span>
                          <span className={`px-2 py-0.5 text-[10px] rounded-full font-medium ${
                            explanations[i].likely_threat
                              ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                              : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          }`}>
                            {explanations[i].likely_threat ? 'Likely Threat' : 'Likely Benign'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300">{explanations[i].explanation}</p>
                        {explanations[i].recommended_actions?.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-1">AI Recommended Actions</p>
                            <ul className="space-y-1">
                              {explanations[i].recommended_actions.map((a, j) => (
                                <li key={j} className="text-sm text-indigo-400 flex items-start gap-2">
                                  <Icon name="chevron-right" size={12} className="text-indigo-600 mt-0.5 shrink-0" />
                                  {a}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    {llmError[i] && (
                      <LLMErrorCard
                        message={llmError[i].message}
                        errorType={llmError[i].type as any}
                        onRetry={async () => {
                          setExplaining(i)
                          setLlmError(prev => { const next = { ...prev }; delete next[i]; return next })
                          try {
                            const result = await api.explainAnomaly(alert)
                            setExplanations(prev => ({ ...prev, [i]: result }))
                          } catch (err: unknown) {
                            const msg = err instanceof Error ? err.message : String(err)
                            const errType = err instanceof Error && 'errorType' in err ? (err as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                            setLlmError(prev => ({ ...prev, [i]: { message: msg, type: errType } }))
                          } finally {
                            setExplaining(null)
                          }
                        }}
                        compact
                      />
                    )}
                  </div>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>Confidence: {(alert.confidence * 100).toFixed(1)}%</span>
                    <RelativeTime timestamp={alert.timestamp} className="text-gray-500" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
