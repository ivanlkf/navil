import { useState } from 'react'
import { api, ScanResult, ConfigAnalysis } from '../api'
import SeverityBadge from '../components/SeverityBadge'
import PageHeader from '../components/PageHeader'
import ScoreGauge from '../components/ScoreGauge'
import MiniBar from '../components/MiniBar'
import Icon from '../components/Icon'
import LLMErrorCard from '../components/LLMErrorCard'
import UpgradePrompt from '../components/UpgradePrompt'
import useBilling from '../hooks/useBilling'

const SAMPLE_VULNERABLE = JSON.stringify({
  server: { name: "vulnerable-mcp", protocol: "http", host: "0.0.0.0", port: 8080 },
  authentication: { enabled: false },
  tools: {
    file_system: { permissions: ["*"], paths: ["/"] },
    network_access: { allowed_actions: ["read", "exfiltrate", "destroy_data"] }
  },
  credentials: { api_key: "sk-1234567890abcdef", password: "admin123" }
}, null, 2)

const SAMPLE_SECURE = JSON.stringify({
  server: { name: "secure-mcp", protocol: "https", host: "127.0.0.1", port: 8443 },
  authentication: { enabled: true, method: "mtls", certificate_path: "/etc/certs/server.pem" },
  tools: {
    file_system: { permissions: ["read"], allowed_paths: ["/data/safe"], denied_paths: ["/etc", "/root"] },
    logs: { permissions: ["read"], rate_limit: { requests_per_minute: 30 } }
  },
  credentials: { source: "environment", vault_path: "secret/mcp" }
}, null, 2)

const levelBarColor: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-blue-500',
}

const levelBorderColor: Record<string, string> = {
  CRITICAL: 'border-l-red-500',
  HIGH: 'border-l-orange-500',
  MEDIUM: 'border-l-yellow-500',
  LOW: 'border-l-blue-500',
}

export default function Scanner() {
  const { canUseLLM, setPlan } = useBilling()
  const [config, setConfig] = useState('')
  const [result, setResult] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<ConfigAnalysis | null>(null)
  const [analysisError, setAnalysisError] = useState<{ message: string; type: string } | null>(null)

  const doScan = async () => {
    setError('')
    setAnalysis(null)
    setAnalysisError(null)
    setResult(null)
    setLoading(true)
    try {
      const parsed = JSON.parse(config)
      const res = await api.scan(parsed)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Config Scanner" subtitle="Analyze MCP server configurations for vulnerabilities" />

      <div className="flex gap-2">
        <button
          onClick={() => setConfig(SAMPLE_VULNERABLE)}
          className="px-3 py-1.5 text-xs bg-red-500/15 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/25 flex items-center gap-1.5"
        >
          <Icon name="unlock" size={13} />
          Load Vulnerable Sample
        </button>
        <button
          onClick={() => setConfig(SAMPLE_SECURE)}
          className="px-3 py-1.5 text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/25 flex items-center gap-1.5"
        >
          <Icon name="lock" size={13} />
          Load Secure Sample
        </button>
      </div>

      <textarea
        value={config}
        onChange={e => setConfig(e.target.value)}
        placeholder="Paste your MCP server configuration JSON here..."
        className="w-full h-64 bg-gray-900/60 backdrop-blur border border-gray-800/60 rounded-xl p-4 font-mono text-sm text-gray-300 focus:border-indigo-500 focus:outline-none resize-y leading-6"
      />

      <div className="relative inline-block">
        <button
          onClick={doScan}
          disabled={loading || !config.trim()}
          className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <Icon name="scan" size={16} className="animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <Icon name="scan" size={16} />
              Scan Configuration
            </>
          )}
        </button>
        {loading && (
          <div className="absolute inset-0 rounded-lg bg-indigo-500/20 animate-pulseGlow pointer-events-none" />
        )}
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Score + Breakdown */}
          <div className="glass-card p-8 flex flex-col sm:flex-row items-center gap-8">
            <ScoreGauge score={result.security_score} size={160} />
            <div className="flex-1 space-y-3">
              <p className="text-lg text-gray-300">
                <span className="font-semibold text-white">{result.total_vulnerabilities}</span> vulnerabilities found
              </p>
              <p className="text-sm text-gray-500">{result.recommendation}</p>
              {/* Severity breakdown bars */}
              <div className="space-y-2 mt-4">
                {Object.entries(result.vulnerabilities_by_level).map(([level, count]) => (
                  count > 0 && (
                    <div key={level} className="flex items-center gap-3">
                      <SeverityBadge severity={level} />
                      <MiniBar
                        value={count as number}
                        max={result.total_vulnerabilities}
                        color={levelBarColor[level] || 'bg-gray-500'}
                        className="flex-1"
                      />
                      <span className="text-xs text-gray-500 w-6 text-right">{count as number}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          </div>

          {/* Vulnerabilities list */}
          {result.vulnerabilities.length > 0 && (
            <div className="space-y-3">
              {result.vulnerabilities.map((vuln, i) => (
                <div
                  key={vuln.id || `vuln-${i}`}
                  className={`glass-card border-l-2 ${levelBorderColor[vuln.risk_level] || 'border-l-gray-500'} p-4 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 animate-slideUp opacity-0`}
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  <div className="flex items-start gap-3">
                    <Icon name="warning" size={16} className="text-gray-500 mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <SeverityBadge severity={vuln.risk_level} />
                        <p className="font-medium text-gray-200">{vuln.title}</p>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">{vuln.description}</p>
                      <p className="text-sm text-indigo-400 mt-2">
                        <span className="text-gray-500">Remediation:</span> {vuln.remediation}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* AI Deep Analysis */}
          <div className="glass-card p-6 animate-slideUp opacity-0" style={{ animationDelay: '0.3s' }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                <Icon name="sparkles" size={16} className="text-violet-400" />
                AI Deep Analysis
              </h3>
              {!analysis && canUseLLM && (
                <button
                  onClick={async () => {
                    setAnalyzing(true)
                    setAnalysisError(null)
                    try {
                      const parsed = JSON.parse(config)
                      const res = await api.analyzeConfig(parsed)
                      setAnalysis(res)
                    } catch (e: unknown) {
                      const msg = e instanceof Error ? e.message : String(e)
                      const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                      setAnalysisError({ message: msg, type: errType })
                    } finally {
                      setAnalyzing(false)
                    }
                  }}
                  disabled={analyzing}
                  className="px-3 py-1.5 text-xs bg-violet-500/15 text-violet-400 border border-violet-500/30 rounded-lg hover:bg-violet-500/25 flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Icon name="sparkles" size={13} className={analyzing ? 'animate-spin' : ''} />
                  {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
                </button>
              )}
            </div>

            {!canUseLLM && !analysis && !analysisError && !analyzing && (
              <UpgradePrompt feature="AI Deep Analysis" onUpgrade={() => setPlan('pro')} compact />
            )}

            {analysisError && (
              <LLMErrorCard
                message={analysisError.message}
                errorType={analysisError.type as any}
                onRetry={async () => {
                  setAnalyzing(true)
                  setAnalysisError(null)
                  try {
                    const parsed = JSON.parse(config)
                    const res = await api.analyzeConfig(parsed)
                    setAnalysis(res)
                  } catch (e: unknown) {
                    const msg = e instanceof Error ? e.message : String(e)
                    const errType = e instanceof Error && 'errorType' in e ? (e as Error & { errorType?: string }).errorType || 'unknown' : 'unknown'
                    setAnalysisError({ message: msg, type: errType })
                  } finally {
                    setAnalyzing(false)
                  }
                }}
              />
            )}

            {analysis && (
              <div className="space-y-4 animate-fadeIn">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={analysis.severity} />
                  {analysis.confidence !== undefined && (
                    <div className="flex items-center gap-2">
                      <MiniBar value={analysis.confidence * 100} max={100} color="bg-violet-500" height="h-1" className="w-20" />
                      <span className="text-xs text-gray-500">{(analysis.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-300">{analysis.explanation}</p>
                {analysis.risks.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-2">Identified Risks</p>
                    <ul className="space-y-1.5">
                      {analysis.risks.map((risk, j) => (
                        <li key={j} className="text-sm text-orange-400 flex items-start gap-2">
                          <Icon name="warning" size={12} className="text-orange-500 mt-0.5 shrink-0" />
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.remediations.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-2">Remediations</p>
                    <ul className="space-y-1.5">
                      {analysis.remediations.map((rem, j) => (
                        <li key={j} className="text-sm text-indigo-400 flex items-start gap-2">
                          <Icon name="check" size={12} className="text-indigo-500 mt-0.5 shrink-0" />
                          {rem}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
