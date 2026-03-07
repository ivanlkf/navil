import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { AnalyticsOverview } from '../api'
import useBilling from '../hooks/useBilling'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import ScoreGauge from '../components/ScoreGauge'
import MiniBar from '../components/MiniBar'
import SparklineChart from '../components/SparklineChart'
import Icon from '../components/Icon'
import { SkeletonCard } from '../components/Skeleton'

// ── Demo data (used when backend is unavailable) ────────────

const DEMO_DATA: AnalyticsOverview = {
  avg_trust_score: 72.4,
  agents_monitored: 5,
  anomaly_rate: 0.034,
  total_events_24h: 12847,
  trust_scores: [
    {
      agent_name: 'data-pipeline-bot',
      score: 91.2,
      verdict: 'trusted',
      components: {
        policy_compliance: 96.0,
        anomaly_frequency: 88.5,
        data_pattern: 90.0,
        behavioral_stability: 92.3,
      },
    },
    {
      agent_name: 'code-review-agent',
      score: 78.5,
      verdict: 'trusted',
      components: {
        policy_compliance: 85.0,
        anomaly_frequency: 72.0,
        data_pattern: 80.2,
        behavioral_stability: 76.8,
      },
    },
    {
      agent_name: 'deploy-bot',
      score: 65.3,
      verdict: 'moderate',
      components: {
        policy_compliance: 70.0,
        anomaly_frequency: 55.0,
        data_pattern: 68.4,
        behavioral_stability: 67.8,
      },
    },
    {
      agent_name: 'monitoring-agent',
      score: 82.1,
      verdict: 'trusted',
      components: {
        policy_compliance: 90.0,
        anomaly_frequency: 78.0,
        data_pattern: 75.5,
        behavioral_stability: 85.0,
      },
    },
    {
      agent_name: 'test-runner',
      score: 45.0,
      verdict: 'untrusted',
      components: {
        policy_compliance: 50.0,
        anomaly_frequency: 35.0,
        data_pattern: 48.0,
        behavioral_stability: 47.0,
      },
    },
  ],
  behavioral_profiles: [
    {
      agent_name: 'data-pipeline-bot',
      total_events: 4521,
      top_tool: 'readFile',
      top_tool_pct: 42.5,
      avg_duration_ms: 125,
      total_data_bytes: 2_200_000,
    },
    {
      agent_name: 'code-review-agent',
      total_events: 3102,
      top_tool: 'analyzeCode',
      top_tool_pct: 58.2,
      avg_duration_ms: 340,
      total_data_bytes: 890_000,
    },
    {
      agent_name: 'deploy-bot',
      total_events: 2890,
      top_tool: 'executeCommand',
      top_tool_pct: 35.1,
      avg_duration_ms: 520,
      total_data_bytes: 450_000,
    },
    {
      agent_name: 'monitoring-agent',
      total_events: 1876,
      top_tool: 'checkStatus',
      top_tool_pct: 67.3,
      avg_duration_ms: 45,
      total_data_bytes: 120_000,
    },
    {
      agent_name: 'test-runner',
      total_events: 458,
      top_tool: 'runTests',
      top_tool_pct: 80.1,
      avg_duration_ms: 890,
      total_data_bytes: 3_400_000,
    },
  ],
  trends: Array.from({ length: 24 }, (_, i) => ({
    label: `${23 - i}h`,
    events: Math.floor(400 + Math.random() * 200 + (i > 12 ? 100 : 0)),
    anomalies: Math.floor(5 + Math.random() * 15 + (i > 18 ? 10 : 0)),
  })),
}

// ── Helpers ──────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function verdictColor(verdict: string): string {
  if (verdict === 'trusted') return 'text-emerald-400'
  if (verdict === 'moderate') return 'text-amber-400'
  return 'text-red-400'
}

function verdictBg(verdict: string): string {
  if (verdict === 'trusted') return 'bg-emerald-500/10 border-emerald-500/20'
  if (verdict === 'moderate') return 'bg-amber-500/10 border-amber-500/20'
  return 'bg-red-500/10 border-red-500/20'
}

// ── Component ───────────────────────────────────────────────

export default function Analytics() {
  const { plan } = useBilling()
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(() => {
    setLoading(true)
    api
      .getAnalyticsOverview()
      .then(setData)
      .catch(() => setData(DEMO_DATA))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // ── Plan gate ─────────────────────────────────────────────
  if (plan !== 'elite') {
    return (
      <>
        <PageHeader title="Analytics" subtitle="Agent trust scores and behavioral profiling" />
        <div className="glass-card p-10 text-center animate-fadeIn">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-500/10 mb-4">
            <Icon name="chart" size={32} className="text-indigo-400" />
          </div>
          <div className="inline-block px-2.5 py-0.5 text-[10px] font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-full mb-3">
            NAVIL CLOUD
          </div>
          <h3 className="text-lg font-medium text-gray-200 mb-2">
            Unlock Agent Risk Analytics
          </h3>
          <p className="text-sm text-gray-500 mb-2 max-w-lg mx-auto">
            Go beyond alerting. Navil Cloud continuously scores every agent on trust,
            tracks behavioral drift over time, and surfaces risk trends before they become incidents.
          </p>
          <ul className="text-sm text-gray-400 mb-6 max-w-md mx-auto space-y-1.5 text-left inline-block">
            <li className="flex items-center gap-2"><Icon name="check" size={12} className="text-emerald-400 shrink-0" /> Per-agent trust scores with component breakdown</li>
            <li className="flex items-center gap-2"><Icon name="check" size={12} className="text-emerald-400 shrink-0" /> Behavioral profiling and anomaly trend analysis</li>
            <li className="flex items-center gap-2"><Icon name="check" size={12} className="text-emerald-400 shrink-0" /> Know which agents are safe for production</li>
          </ul>
          <div>
            <a
              href="https://www.navil.ai/pricing"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500"
            >
              <Icon name="sparkles" size={14} />
              Get Navil Cloud
            </a>
          </div>
        </div>
      </>
    )
  }

  // ── Loading ───────────────────────────────────────────────
  if (loading || !data) {
    return (
      <>
        <PageHeader title="Analytics" subtitle="Agent trust scores and behavioral profiling" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </>
    )
  }

  // ── Main content ──────────────────────────────────────────
  return (
    <>
      <PageHeader title="Analytics" subtitle="Agent trust scores and behavioral profiling">
        <span className="px-2.5 py-1 text-[10px] font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-full">
          ELITE
        </span>
      </PageHeader>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Avg Trust Score" value={Math.round(data.avg_trust_score)} icon="shield" accent="emerald" index={0} />
        <StatCard label="Agents Monitored" value={data.agents_monitored} icon="bot" accent="indigo" index={1} />
        <StatCard label="Anomaly Rate" value={`${(data.anomaly_rate * 100).toFixed(1)}%`} icon="alert" accent="amber" index={2} />
        <StatCard label="Events (24h)" value={data.total_events_24h} icon="activity" accent="indigo" index={3} />
      </div>

      {/* Trust Scores + Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* Trust Scores */}
        <div className="glass-card p-5 animate-slideUp opacity-0" style={{ animationDelay: '0.1s' }}>
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Icon name="shield" size={16} className="text-indigo-400" />
            Agent Trust Scores
          </h3>
          <div className="space-y-4">
            {data.trust_scores
              .sort((a, b) => b.score - a.score)
              .map((agent) => (
                <div key={agent.agent_name} className="flex items-center gap-4">
                  <ScoreGauge score={Math.round(agent.score)} size={64} strokeWidth={5} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-200 truncate">
                        {agent.agent_name}
                      </span>
                      <span
                        className={`px-1.5 py-0.5 text-[10px] font-semibold rounded border ${verdictBg(agent.verdict)} ${verdictColor(agent.verdict)}`}
                      >
                        {agent.verdict}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                      <ScoreBar label="Policy" value={agent.components.policy_compliance} />
                      <ScoreBar label="Anomaly" value={agent.components.anomaly_frequency} />
                      <ScoreBar label="Data" value={agent.components.data_pattern} />
                      <ScoreBar label="Stability" value={agent.components.behavioral_stability} />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Anomaly Trends */}
        <div className="glass-card p-5 animate-slideUp opacity-0" style={{ animationDelay: '0.15s' }}>
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Icon name="activity" size={16} className="text-indigo-400" />
            Anomaly Trends (24h)
          </h3>
          <div className="mb-4">
            <SparklineChart
              data={data.trends.map((t) => ({ label: t.label, value: t.anomalies }))}
              height={140}
              color="rgb(248, 113, 113)"
              fillColor="rgba(248, 113, 113, 0.08)"
            />
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-red-400 rounded-full inline-block" />
              Anomalies
            </span>
          </div>
          <div className="mt-4">
            <SparklineChart
              data={data.trends.map((t) => ({ label: t.label, value: t.events }))}
              height={80}
              color="rgb(129, 140, 248)"
              fillColor="rgba(129, 140, 248, 0.06)"
            />
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-indigo-400 rounded-full inline-block" />
              Total Events
            </span>
          </div>
        </div>
      </div>

      {/* Behavioral Profiles Table */}
      <div className="glass-card overflow-x-auto animate-slideUp opacity-0" style={{ animationDelay: '0.2s' }}>
        <div className="p-5 border-b border-gray-800/50">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Icon name="bot" size={16} className="text-indigo-400" />
            Behavioral Profiles
          </h3>
        </div>
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="border-b border-gray-800/50">
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-left">
                Agent
              </th>
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-left">
                Top Tool
              </th>
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-right">
                Invocations
              </th>
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-right">
                Avg Duration
              </th>
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-right">
                Data Volume
              </th>
              <th className="text-xs font-medium text-gray-500 uppercase tracking-wider px-5 py-3 text-center">
                Trust
              </th>
            </tr>
          </thead>
          <tbody>
            {data.behavioral_profiles.map((profile) => {
              const trustEntry = data.trust_scores.find(
                (t) => t.agent_name === profile.agent_name,
              )
              const score = trustEntry?.score ?? 50
              const verdict = trustEntry?.verdict ?? 'moderate'
              return (
                <tr
                  key={profile.agent_name}
                  className="border-b border-gray-800/30 hover:bg-gray-800/20 transition-colors"
                >
                  <td className="px-5 py-3.5">
                    <span className="text-sm font-medium text-gray-200">
                      {profile.agent_name}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-gray-800 px-1.5 py-0.5 rounded text-indigo-300">
                        {profile.top_tool}
                      </code>
                      <span className="text-xs text-gray-500">{profile.top_tool_pct}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-sm text-gray-300">
                      {profile.total_events.toLocaleString()}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-sm text-gray-300">{profile.avg_duration_ms}ms</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-sm text-gray-300">
                      {formatBytes(profile.total_data_bytes)}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex flex-col items-center gap-1">
                      <span className={`text-sm font-semibold ${verdictColor(verdict)}`}>
                        {Math.round(score)}
                      </span>
                      <MiniBar
                        value={score}
                        max={100}
                        color={
                          score >= 80
                            ? 'bg-emerald-500'
                            : score >= 60
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                        }
                        height="h-1"
                        className="w-12"
                      />
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ── Sub-components ──────────────────────────────────────────

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] text-gray-500 w-12 truncate">{label}</span>
      <MiniBar
        value={value}
        max={100}
        color={value >= 80 ? 'bg-emerald-500' : value >= 60 ? 'bg-amber-500' : 'bg-red-500'}
        height="h-1"
        className="flex-1"
      />
      <span className="text-[10px] text-gray-500 w-6 text-right">{Math.round(value)}</span>
    </div>
  )
}
