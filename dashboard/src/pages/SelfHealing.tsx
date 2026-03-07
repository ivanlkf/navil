import { useEffect, useState, useRef } from 'react'
import { api, RemediationSuggestion, RemediationAction, AutoRemediateResult, LLMConfig } from '../api'
import useSessionState from '../hooks/useSessionState'
import PageHeader from '../components/PageHeader'
import SeverityBadge from '../components/SeverityBadge'
import MiniBar from '../components/MiniBar'
import Icon from '../components/Icon'
import LLMErrorCard from '../components/LLMErrorCard'
import UpgradePrompt from '../components/UpgradePrompt'
import useBilling from '../hooks/useBilling'

const actionTypeColors: Record<string, string> = {
  policy_update: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
  threshold_adjustment: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  credential_rotation: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  agent_block: 'bg-red-500/15 text-red-400 border-red-500/30',
  alert_escalation: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
}

const actionTypeDescriptions: Record<string, string> = {
  policy_update: 'Updates the security policy for this agent — changes what tools, data, or actions are allowed.',
  threshold_adjustment: 'Adjusts anomaly detection thresholds — makes the system more or less sensitive to deviations.',
  credential_rotation: 'Rotates credentials for this agent — revokes current access tokens and issues new ones.',
  agent_block: 'Blocks this agent entirely — denies all tool access until manually unblocked.',
  alert_escalation: 'Escalates to human review — flags these alerts for manual investigation by security team.',
}

const PHASES = ['analyzing', 'applying', 'verifying'] as const
type Phase = typeof PHASES[number]

export default function SelfHealing() {
  const { canUseLLM, setPlan } = useBilling()
  const [llmConfig, setLlmConfig] = useState<LLMConfig | null>(null)
  const [error, setError] = useState<{ message: string; type: string } | null>(null)

  // Manual flow state
  const [analyzing, setAnalyzing] = useState(false)
  const [suggestion, setSuggestion] = useSessionState<RemediationSuggestion | null>('healing_suggestion', null)
  const [applying, setApplying] = useState<number | null>(null)
  const [applied, setApplied] = useState<Set<number>>(new Set())
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  // Auto-remediate flow state
  const [autoRemediating, setAutoRemediating] = useState(false)
  const [autoPhase, setAutoPhase] = useState<Phase | null>(null)
  const [autoResult, setAutoResult] = useSessionState<AutoRemediateResult | null>('healing_auto', null)
  const [autoApplying, setAutoApplying] = useState<number | null>(null)
  const [autoApplied, setAutoApplied] = useState<Set<number>>(new Set())

  const phaseTimersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const llmReady = llmConfig?.available && llmConfig?.api_key_set
  const busy = analyzing || autoRemediating

  const toggleExpand = (i: number) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  useEffect(() => {
    api.getLLMStatus().then(setLlmConfig).catch(() => setLlmConfig({ available: false, api_key_set: false, provider: '', model: '', base_url: '' }))
  }, [])

  // --- Manual flow handlers ---
  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    // Don't clear suggestion — let old results stay visible until replaced
    setAutoResult(null)
    setApplied(new Set())
    setExpanded(new Set())
    try {
      const res = await api.suggestRemediation()
      setSuggestion(res)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
      setError({ message: msg, type: errType })
    } finally {
      setAnalyzing(false)
    }
  }

  const handleApply = async (action: RemediationAction, index: number) => {
    setApplying(index)
    try {
      const res = await api.applyAction(action)
      if (res.success) {
        setApplied(prev => new Set([...prev, index]))
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
      setError({ message: msg, type: errType })
    } finally {
      setApplying(null)
    }
  }

  // --- Auto-remediate handlers ---
  const handleAutoRemediate = async () => {
    setAutoRemediating(true)
    setAutoPhase('analyzing')
    setError(null)
    setSuggestion(null)
    // Don't clear autoResult — let old results stay visible until replaced
    setAutoApplied(new Set())
    setApplied(new Set())

    // Cosmetic phase transitions while server processes
    const timers: ReturnType<typeof setTimeout>[] = []
    timers.push(setTimeout(() => setAutoPhase('applying'), 3000))
    timers.push(setTimeout(() => setAutoPhase('verifying'), 6000))
    phaseTimersRef.current = timers

    try {
      const res = await api.autoRemediate()
      // Clear cosmetic timers
      timers.forEach(clearTimeout)
      phaseTimersRef.current = []
      setAutoPhase(null)
      setAutoResult(res)
    } catch (e: unknown) {
      timers.forEach(clearTimeout)
      phaseTimersRef.current = []
      setAutoPhase(null)
      const msg = e instanceof Error ? e.message : String(e)
      const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
      setError({ message: msg, type: errType })
    } finally {
      setAutoRemediating(false)
    }
  }

  const handleAutoManualApply = async (action: RemediationAction, index: number) => {
    setAutoApplying(index)
    try {
      const res = await api.applyAction(action)
      if (res.success) {
        setAutoApplied(prev => new Set([...prev, index]))
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
      setError({ message: msg, type: errType })
    } finally {
      setAutoApplying(null)
    }
  }

  // --- Shared action card renderer ---
  const renderActionBadges = (action: RemediationAction) => (
    <div className="flex items-center gap-2 flex-wrap">
      <span className={`px-2 py-0.5 text-[10px] font-medium rounded border ${
        actionTypeColors[action.type] || 'bg-gray-500/15 text-gray-400 border-gray-500/30'
      }`}>
        {action.type.replace(/_/g, ' ')}
      </span>
      <span className="text-xs font-mono text-gray-400">{action.target}</span>
      {action.reversible && (
        <span className="px-1.5 py-0.5 text-[10px] bg-emerald-500/10 text-emerald-400 rounded">reversible</span>
      )}
      {!action.reversible && (
        <span className="px-1.5 py-0.5 text-[10px] bg-red-500/10 text-red-400 rounded">irreversible</span>
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader title="Self-Healing" subtitle="AI-powered threat analysis and automated remediation">
        <div className="flex items-center gap-2">
          <button
            onClick={handleAnalyze}
            disabled={busy || !llmReady || !canUseLLM}
            className="px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icon name="sparkles" size={14} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing...' : 'Analyze Threats'}
          </button>
          <button
            onClick={handleAutoRemediate}
            disabled={busy || !llmReady || !canUseLLM}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icon name="shield" size={14} className={autoRemediating ? 'animate-spin' : ''} />
            {autoRemediating ? 'Remediating...' : 'Auto-Remediate'}
          </button>
        </div>
      </PageHeader>

      {/* LLM status warnings */}
      {llmConfig && !llmConfig.available && (
        <LLMErrorCard message="LLM features require navil[llm]. Install with: pip install navil[llm]" errorType="auth" />
      )}
      {llmConfig?.available && !llmConfig?.api_key_set && (
        <LLMErrorCard message="No API key configured. Add your key in Settings to enable AI features." errorType="auth" />
      )}
      {error && (
        <LLMErrorCard message={error.message} errorType={error.type as any} onRetry={handleAnalyze} />
      )}
      {llmReady && !canUseLLM && !busy && !suggestion && !autoResult && (
        <UpgradePrompt feature="Self-Healing AI" onUpgrade={() => setPlan('lite')} />
      )}

      {/* Empty state */}
      {!suggestion && !autoResult && !busy && !error && llmReady && canUseLLM && (
        <div className="text-center py-16 animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-violet-500/10 mb-4">
            <Icon name="sparkles" size={32} className="text-violet-400" />
          </div>
          <p className="text-gray-400">Click &ldquo;Analyze Threats&rdquo; for manual review, or &ldquo;Auto-Remediate&rdquo; to automatically fix safe threats.</p>
        </div>
      )}

      {/* Manual analyze spinner — hide once results arrive */}
      {analyzing && !suggestion && (
        <div className="text-center py-16 animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-violet-500/10 mb-4">
            <Icon name="sparkles" size={32} className="text-violet-400 animate-spin" />
          </div>
          <p className="text-gray-400">Analyzing threats with AI...</p>
          <p className="text-xs text-gray-600 mt-1">This may take a few seconds</p>
        </div>
      )}

      {/* Auto-remediate phased progress — hide once results arrive */}
      {autoRemediating && !autoResult && (
        <div className="text-center py-16 animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-6">
            <Icon name="shield" size={32} className="text-emerald-400 animate-spin" />
          </div>

          {/* Phase stepper */}
          <div className="flex items-center justify-center gap-2 mb-4">
            {PHASES.map((phase, i) => {
              const currentIdx = autoPhase ? PHASES.indexOf(autoPhase) : -1
              const isDone = currentIdx > i
              const isCurrent = autoPhase === phase
              return (
                <div key={phase} className="flex items-center gap-2">
                  {i > 0 && (
                    <div className={`w-8 h-px ${isDone ? 'bg-emerald-500' : 'bg-gray-700'}`} />
                  )}
                  <div className="flex items-center gap-1.5">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-medium ${
                      isDone ? 'bg-emerald-500/20 text-emerald-400'
                        : isCurrent ? 'bg-emerald-500/20 text-emerald-400 animate-pulse'
                        : 'bg-gray-800 text-gray-600'
                    }`}>
                      {isDone ? <Icon name="check" size={11} /> : i + 1}
                    </div>
                    <span className={`text-xs capitalize ${
                      isCurrent ? 'text-emerald-400 font-medium' : isDone ? 'text-emerald-400' : 'text-gray-600'
                    }`}>
                      {phase === 'analyzing' ? 'Analyzing' : phase === 'applying' ? 'Applying' : 'Verifying'}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          <p className="text-xs text-gray-600">Autonomous remediation in progress...</p>
        </div>
      )}

      {/* ===== MANUAL FLOW RESULTS ===== */}
      {suggestion && (
        <div className="space-y-6 animate-fadeIn">
          <div className="glass-card p-5 flex items-start gap-4">
            <div className="shrink-0"><SeverityBadge severity={suggestion.risk_assessment} /></div>
            <div>
              <p className="text-sm text-gray-300">{suggestion.summary}</p>
              <p className="text-xs text-gray-500 mt-1">
                {suggestion.actions.length} remediation action{suggestion.actions.length !== 1 ? 's' : ''} suggested
              </p>
            </div>
          </div>

          {suggestion.actions.length === 0 ? (
            <div className="glass-card p-8 text-center">
              <Icon name="check" size={24} className="text-emerald-400 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">No remediation actions needed. System looks healthy.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {suggestion.actions.map((action, i) => {
                const isExpanded = expanded.has(i)
                return (
                <div key={`${action.type}-${action.target}-${i}`} className={`glass-card p-4 animate-slideUp opacity-0 transition-all ${applied.has(i) ? 'border-emerald-500/30' : ''}`}
                  style={{ animationDelay: `${i * 0.06}s` }}>
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <div className="mb-2">{renderActionBadges(action)}</div>
                      <p className="text-sm text-gray-300">{action.reason}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-[10px] text-gray-500">Confidence</span>
                        <MiniBar value={action.confidence * 100} max={100}
                          color={action.confidence >= 0.8 ? 'bg-emerald-500' : action.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-orange-500'}
                          height="h-1" className="w-24" />
                        <span className="text-[10px] text-gray-400">{(action.confidence * 100).toFixed(0)}%</span>
                        <button onClick={() => toggleExpand(i)} className="ml-auto text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors">
                          <Icon name="info" size={11} />
                          {isExpanded ? 'Less' : 'Details'}
                        </button>
                      </div>
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-gray-800/60 space-y-2.5 animate-fadeIn">
                          <div>
                            <span className="text-[10px] uppercase tracking-wider text-gray-500">What this does</span>
                            <p className="text-xs text-gray-400 mt-0.5">{actionTypeDescriptions[action.type] || 'Applies the recommended security change.'}</p>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase tracking-wider text-gray-500">Change</span>
                            <p className="text-xs font-mono text-gray-300 mt-0.5 bg-gray-800/40 rounded px-2 py-1.5">
                              {typeof action.value === 'string' ? action.value : JSON.stringify(action.value, null, 2)}
                            </p>
                          </div>
                          {action.reversible !== undefined && (
                            <div>
                              <span className="text-[10px] uppercase tracking-wider text-gray-500">Reversibility</span>
                              <p className="text-xs text-gray-400 mt-0.5">
                                {action.reversible ? 'This action can be undone. The previous state will be restored if reverted.'
                                  : 'This action cannot be easily undone. Review carefully before applying.'}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="shrink-0">
                      {applied.has(i) ? (
                        <span className="px-3 py-1.5 text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg flex items-center gap-1.5">
                          <Icon name="check" size={13} /> Applied
                        </span>
                      ) : (
                        <button onClick={() => handleApply(action, i)} disabled={applying === i}
                          className="px-3 py-1.5 text-xs bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-lg hover:bg-indigo-500/25 flex items-center gap-1.5 disabled:opacity-50">
                          <Icon name="shield" size={13} className={applying === i ? 'animate-spin' : ''} />
                          {applying === i ? 'Applying...' : 'Apply'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                )
              })}

              {applied.size > 0 && applied.size >= suggestion.actions.length && (
                <div className="glass-card p-5 text-center animate-fadeIn border-emerald-500/20">
                  <Icon name="check" size={22} className="text-emerald-400 mx-auto mb-2" />
                  <p className="text-sm text-emerald-400 font-medium">All {applied.size} remediation actions applied</p>
                  <p className="text-xs text-gray-500 mt-1">Click &ldquo;Analyze Threats&rdquo; again to verify the system is now healthy.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ===== AUTO-REMEDIATE RESULTS ===== */}
      {autoResult && (
        <div className="space-y-5 animate-fadeIn">
          {/* Initial analysis summary */}
          <div className="glass-card p-5 flex items-start gap-4">
            <div className="shrink-0"><SeverityBadge severity={autoResult.initial_analysis.risk_assessment} /></div>
            <div>
              <p className="text-sm text-gray-300">{autoResult.initial_analysis.summary}</p>
              <p className="text-xs text-gray-500 mt-1">
                {autoResult.auto_applied.length} auto-applied
                {autoResult.manual_review.length > 0 && `, ${autoResult.manual_review.length} need review`}
                {autoResult.failed_to_apply.length > 0 && `, ${autoResult.failed_to_apply.length} failed`}
              </p>
            </div>
          </div>

          {/* Post-status banner */}
          <div className={`glass-card p-4 flex items-center gap-3 ${
            autoResult.post_status.healthy ? 'border-emerald-500/20' : 'border-amber-500/20'
          }`}>
            <Icon name={autoResult.post_status.healthy ? 'check' : 'alert'} size={18}
              className={autoResult.post_status.healthy ? 'text-emerald-400' : 'text-amber-400'} />
            <div>
              <p className={`text-sm font-medium ${autoResult.post_status.healthy ? 'text-emerald-400' : 'text-amber-400'}`}>
                {autoResult.post_status.healthy
                  ? 'System Healthy — All Threats Resolved'
                  : `${autoResult.post_status.remaining_alert_count} alert${autoResult.post_status.remaining_alert_count !== 1 ? 's' : ''} remaining`}
              </p>
              <p className="text-xs text-gray-500">
                {autoResult.post_status.healthy
                  ? 'All threats have been automatically resolved.'
                  : 'Some actions require manual review below.'}
              </p>
            </div>
          </div>

          {/* Auto-applied actions (green section) */}
          {autoResult.auto_applied.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Icon name="check" size={13} />
                Auto-Applied ({autoResult.auto_applied.length})
              </h3>
              <div className="space-y-2">
                {autoResult.auto_applied.map((action, i) => (
                  <div key={`auto-${action.type}-${action.target}-${i}`} className="glass-card p-3 border-emerald-500/20 animate-slideUp opacity-0"
                    style={{ animationDelay: `${i * 0.06}s` }}>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        {renderActionBadges(action)}
                        <p className="text-xs text-gray-400 mt-1.5">{action.reason}</p>
                      </div>
                      <Icon name="check" size={14} className="text-emerald-400 shrink-0" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failed actions (red section) */}
          {autoResult.failed_to_apply.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Icon name="alert" size={13} />
                Failed ({autoResult.failed_to_apply.length})
              </h3>
              <div className="space-y-2">
                {autoResult.failed_to_apply.map((action, i) => (
                  <div key={`fail-${action.type}-${action.target}-${i}`} className="glass-card p-3 border-red-500/20">
                    {renderActionBadges(action)}
                    <p className="text-xs text-gray-400 mt-1.5">{action.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Manual review actions (yellow section with Apply buttons) */}
          {autoResult.manual_review.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-yellow-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Icon name="eye" size={13} />
                Needs Manual Review ({autoResult.manual_review.length})
              </h3>
              <div className="space-y-3">
                {autoResult.manual_review.map((action, i) => (
                  <div key={`manual-${action.type}-${action.target}-${i}`} className="glass-card p-4 border-yellow-500/20 animate-slideUp opacity-0"
                    style={{ animationDelay: `${(autoResult.auto_applied.length + i) * 0.06}s` }}>
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="mb-2">{renderActionBadges(action)}</div>
                        <p className="text-sm text-gray-300">{action.reason}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] text-gray-500">Confidence</span>
                          <MiniBar value={action.confidence * 100} max={100}
                            color={action.confidence >= 0.8 ? 'bg-emerald-500' : action.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-orange-500'}
                            height="h-1" className="w-24" />
                          <span className="text-[10px] text-gray-400">{(action.confidence * 100).toFixed(0)}%</span>
                          {!action.reversible && (
                            <span className="text-[10px] text-yellow-500 ml-2">Irreversible — review carefully</span>
                          )}
                        </div>
                      </div>
                      <div className="shrink-0">
                        {autoApplied.has(i) ? (
                          <span className="px-3 py-1.5 text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg flex items-center gap-1.5">
                            <Icon name="check" size={13} /> Applied
                          </span>
                        ) : (
                          <button onClick={() => handleAutoManualApply(action, i)} disabled={autoApplying === i}
                            className="px-3 py-1.5 text-xs bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-lg hover:bg-indigo-500/25 flex items-center gap-1.5 disabled:opacity-50">
                            <Icon name="shield" size={13} className={autoApplying === i ? 'animate-spin' : ''} />
                            {autoApplying === i ? 'Applying...' : 'Apply'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No actions at all */}
          {autoResult.auto_applied.length === 0 && autoResult.manual_review.length === 0 && autoResult.failed_to_apply.length === 0 && (
            <div className="glass-card p-8 text-center">
              <Icon name="check" size={24} className="text-emerald-400 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">No remediation actions needed. System looks healthy.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
