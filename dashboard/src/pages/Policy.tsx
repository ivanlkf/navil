import { useEffect, useState } from 'react'
import { api, PolicyCheckResult, PolicyDecision, GeneratedPolicy } from '../api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import SeverityBadge from '../components/SeverityBadge'
import RelativeTime from '../components/RelativeTime'
import Icon from '../components/Icon'
import { SkeletonTable } from '../components/Skeleton'
import LLMErrorCard from '../components/LLMErrorCard'
import UpgradePrompt from '../components/UpgradePrompt'
import useBilling from '../hooks/useBilling'

export default function Policy() {
  const { canUseLLM, setPlan } = useBilling()
  const [decisions, setDecisions] = useState<PolicyDecision[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')

  // Check form
  const [agentName, setAgentName] = useState('')
  const [toolName, setToolName] = useState('')
  const [action, setAction] = useState('')
  const [checking, setChecking] = useState(false)
  const [result, setResult] = useState<PolicyCheckResult | null>(null)

  // AI Policy Generator
  const [genDescription, setGenDescription] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generatedYaml, setGeneratedYaml] = useState('')
  const [generatedPolicy, setGeneratedPolicy] = useState<Record<string, unknown> | null>(null)
  const [refineInput, setRefineInput] = useState('')
  const [refining, setRefining] = useState(false)
  const [copied, setCopied] = useState(false)
  const [genError, setGenError] = useState<{ message: string; type: string } | null>(null)

  const loadDecisions = () => {
    api.getPolicyDecisions()
      .then(d => { setDecisions(d); setLoaded(true) })
      .catch(e => setError(e.message))
  }

  useEffect(loadDecisions, [])

  const handleCheck = async () => {
    if (!agentName || !toolName || !action) return
    setChecking(true)
    setResult(null)
    setError('')
    try {
      const res = await api.checkPolicy(agentName, toolName, action)
      setResult(res)
      loadDecisions() // refresh decisions
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Policy Engine" subtitle="Check permissions and review decisions" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policy Checker */}
        <div className="space-y-4">
          <div className="glass-card p-5">
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Icon name="shield" size={16} className="text-indigo-400" />
              Check Permission
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Agent Name</label>
                <input
                  value={agentName}
                  onChange={e => setAgentName(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
                  placeholder="e.g., code-assistant"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Tool Name</label>
                <input
                  value={toolName}
                  onChange={e => setToolName(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
                  placeholder="e.g., admin_panel"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Action</label>
                <input
                  value={action}
                  onChange={e => setAction(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
                  placeholder="e.g., read, write, delete"
                />
              </div>
              <button
                onClick={handleCheck}
                disabled={!agentName || !toolName || !action || checking}
                className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Icon name="shield" size={14} />
                {checking ? 'Checking...' : 'Check Permission'}
              </button>
            </div>
          </div>

          {/* Result card */}
          {result && (
            <div className={`glass-card p-5 animate-slideUp ${
              result.allowed
                ? 'border-emerald-500/30'
                : 'border-red-500/30'
            }`}>
              <div className="flex items-center gap-3 mb-2">
                {result.allowed ? (
                  <>
                    <div className="w-10 h-10 rounded-full bg-emerald-500/15 flex items-center justify-center">
                      <Icon name="check" size={20} className="text-emerald-400" />
                    </div>
                    <div>
                      <p className="font-medium text-emerald-400">Allowed</p>
                      <p className="text-xs text-gray-500">This action is permitted</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-10 h-10 rounded-full bg-red-500/15 flex items-center justify-center">
                      <Icon name="x" size={20} className="text-red-400" />
                    </div>
                    <div>
                      <p className="font-medium text-red-400">Denied</p>
                      <p className="text-xs text-gray-500">This action is blocked</p>
                    </div>
                  </>
                )}
              </div>
              <p className="text-sm text-gray-400 mt-2">{result.reason}</p>
            </div>
          )}
        </div>

        {/* Decision Log */}
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
            <Icon name="clock" size={16} className="text-gray-500" />
            Decision Log
          </h3>
          {!loaded ? <SkeletonTable rows={8} cols={4} /> : (
            decisions.length === 0 ? (
              <div className="glass-card p-8 text-center">
                <p className="text-gray-500 text-sm">No policy decisions recorded yet.</p>
              </div>
            ) : (
              <div className="glass-card overflow-hidden max-h-[600px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-900/90 backdrop-blur">
                    <tr className="border-b border-gray-800/60 text-gray-400 text-left">
                      <th className="px-3 py-2.5 font-medium">Decision</th>
                      <th className="px-3 py-2.5 font-medium">Agent</th>
                      <th className="px-3 py-2.5 font-medium">Tool / Action</th>
                      <th className="px-3 py-2.5 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.map((d, i) => (
                      <tr
                        key={`${d.timestamp}-${d.agent}-${d.tool}-${d.action}`}
                        className="border-b border-gray-800/30 hover:bg-indigo-500/[0.04] animate-fadeIn opacity-0"
                        style={{ animationDelay: `${i * 0.03}s` }}
                      >
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-2">
                            <StatusBadge status={d.decision} />
                          </div>
                        </td>
                        <td className="px-3 py-2.5 text-gray-300 text-xs">{d.agent}</td>
                        <td className="px-3 py-2.5">
                          <span className="text-gray-300 text-xs font-mono">{d.tool}</span>
                          <span className="text-gray-600 text-xs mx-1">→</span>
                          <span className="text-gray-400 text-xs">{d.action}</span>
                        </td>
                        <td className="px-3 py-2.5">
                          <RelativeTime timestamp={d.timestamp} className="text-gray-500 text-xs" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
        </div>
      </div>

      {/* AI Policy Generator */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
          <Icon name="sparkles" size={16} className="text-violet-400" />
          Generate Policy with AI
        </h3>
        {!canUseLLM ? (
          <UpgradePrompt feature="AI Policy Generator" onUpgrade={() => setPlan('pro')} compact />
        ) : (
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Describe your security policy</label>
            <textarea
              value={genDescription}
              onChange={e => setGenDescription(e.target.value)}
              className="w-full h-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none resize-none"
              placeholder="e.g., Only allow data-reader to read logs and metrics. Block admin tools for all agents except admin-bot. Rate limit to 100 requests/hour."
            />
          </div>
          <button
            onClick={async () => {
              if (!genDescription.trim()) return
              setGenerating(true)
              setGenError(null)
              try {
                const res = await api.generatePolicy(genDescription)
                setGeneratedYaml(res.yaml)
                setGeneratedPolicy(res.policy)
              } catch (e: unknown) {
                const msg = e instanceof Error ? e.message : String(e)
                const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                setGenError({ message: msg, type: errType })
              } finally {
                setGenerating(false)
              }
            }}
            disabled={!genDescription.trim() || generating}
            className="px-4 py-2.5 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icon name="sparkles" size={14} className={generating ? 'animate-spin' : ''} />
            {generating ? 'Generating...' : 'Generate Policy'}
          </button>
        </div>
        )}

        {genError && (
          <div className="mt-3">
            <LLMErrorCard
              message={genError.message}
              errorType={genError.type as any}
              onRetry={async () => {
                if (!genDescription.trim()) return
                setGenerating(true)
                setGenError(null)
                try {
                  const res = await api.generatePolicy(genDescription)
                  setGeneratedYaml(res.yaml)
                  setGeneratedPolicy(res.policy)
                } catch (e: unknown) {
                  const msg = e instanceof Error ? e.message : String(e)
                  const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                  setGenError({ message: msg, type: errType })
                } finally {
                  setGenerating(false)
                }
              }}
            />
          </div>
        )}

        {generatedYaml && (
          <div className="mt-4 space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-500">Generated YAML</p>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(generatedYaml)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}
                className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200 border border-gray-700 rounded hover:border-gray-600 flex items-center gap-1"
              >
                <Icon name={copied ? 'check' : 'terminal'} size={12} />
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <pre className="bg-gray-900/80 border border-gray-800/60 rounded-lg p-4 text-sm text-gray-300 font-mono overflow-x-auto max-h-80 overflow-y-auto whitespace-pre-wrap">
              {generatedYaml}
            </pre>
            <div className="flex gap-2">
              <input
                value={refineInput}
                onChange={e => setRefineInput(e.target.value)}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
                placeholder="Refine: e.g., Add a rate limit of 50/hr for deploy-agent"
              />
              <button
                onClick={async () => {
                  if (!refineInput.trim() || !generatedPolicy) return
                  setRefining(true)
                  setGenError(null)
                  try {
                    const res = await api.refinePolicy(generatedPolicy, refineInput)
                    setGeneratedYaml(res.yaml)
                    setGeneratedPolicy(res.policy)
                    setRefineInput('')
                  } catch (e: unknown) {
                    const msg = e instanceof Error ? e.message : String(e)
                    const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                    setGenError({ message: msg, type: errType })
                  } finally {
                    setRefining(false)
                  }
                }}
                disabled={!refineInput.trim() || refining}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
              >
                <Icon name="sparkles" size={13} className={refining ? 'animate-spin' : ''} />
                Refine
              </button>
            </div>
          </div>
        )}
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
    </div>
  )
}
