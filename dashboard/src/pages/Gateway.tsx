import { useEffect, useState, useCallback } from 'react'
import { api, ProxyStatus, TrafficEntry } from '../api'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Icon from '../components/Icon'
import RelativeTime from '../components/RelativeTime'

const POLL_INTERVAL = 2000

const decisionColors: Record<string, string> = {
  ALLOWED: 'text-emerald-400',
  FORWARDED: 'text-emerald-400',
  DENIED: 'text-red-400',
  AUTH_REQUIRED: 'text-red-400',
  ALERT: 'text-amber-400',
}

const decisionBg: Record<string, string> = {
  ALLOWED: 'bg-emerald-500/10',
  FORWARDED: 'bg-emerald-500/10',
  DENIED: 'bg-red-500/10',
  AUTH_REQUIRED: 'bg-red-500/10',
  ALERT: 'bg-amber-500/10',
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export default function Gateway() {
  const [status, setStatus] = useState<ProxyStatus | null>(null)
  const [traffic, setTraffic] = useState<TrafficEntry[]>([])
  const [agentFilter, setAgentFilter] = useState('')
  const [blockedOnly, setBlockedOnly] = useState(false)

  const [fetchError, setFetchError] = useState('')

  // Start proxy form state
  const [targetUrl, setTargetUrl] = useState('http://localhost:3000')
  const [proxyPort, setProxyPort] = useState('9090')
  const [requireAuth, setRequireAuth] = useState(true)
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState('')

  const handleStartProxy = async () => {
    if (!targetUrl.trim()) return
    setStarting(true)
    setStartError('')
    try {
      await api.proxyStart(targetUrl.trim(), Number(proxyPort) || 9090, requireAuth)
      fetchData()
    } catch (e: unknown) {
      setStartError(e instanceof Error ? e.message : String(e))
    } finally {
      setStarting(false)
    }
  }

  const fetchData = useCallback(() => {
    api.proxyStatus().then(s => { setStatus(s); setFetchError('') }).catch(e => setFetchError(e.message))
    api.proxyTraffic(agentFilter || undefined, blockedOnly)
      .then(setTraffic)
      .catch(() => {})
  }, [agentFilter, blockedOnly])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData])

  // Unique agents from traffic for filter dropdown
  const agents = [...new Set(traffic.map(t => t.agent))].sort()

  const running = status?.running ?? false

  return (
    <div>
      <PageHeader
        title="Gateway"
        subtitle="MCP Security Proxy — real-time traffic monitoring"
      >
        <div className="flex items-center gap-3">
          {running ? (
            <span className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Running
            </span>
          ) : (
            <span className="flex items-center gap-2 px-3 py-1.5 bg-gray-500/10 border border-gray-500/20 rounded-lg text-gray-400 text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              Stopped
            </span>
          )}
          {running && status?.target_url && (
            <span className="text-xs text-gray-500 font-mono">
              {status.target_url}
            </span>
          )}
        </div>
      </PageHeader>

      {!running ? (
        /* Start proxy form */
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
            <Icon name="gateway" size={32} className="text-indigo-400" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Start MCP Security Proxy</h3>
          <p className="text-gray-400 max-w-md mb-6">
            Intercept and monitor agent-to-tool traffic in real time.
            The proxy enforces policies, detects anomalies, and blocks threats.
          </p>

          <div className="bg-gray-900/50 border border-gray-800/60 rounded-xl p-6 max-w-lg w-full text-left space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Target MCP Server URL</label>
              <input
                type="text"
                value={targetUrl}
                onChange={e => setTargetUrl(e.target.value)}
                placeholder="http://localhost:3000"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1.5">Proxy Port</label>
                <input
                  type="number"
                  value={proxyPort}
                  onChange={e => setProxyPort(e.target.value)}
                  placeholder="9090"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 font-mono focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div className="flex-1 flex items-end pb-1">
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireAuth}
                    onChange={e => setRequireAuth(e.target.checked)}
                    className="rounded border-gray-700 bg-gray-800 text-indigo-500 focus:ring-indigo-500/30"
                  />
                  Require auth tokens
                </label>
              </div>
            </div>

            {startError && (
              <p className="text-xs text-red-400 flex items-center gap-1">
                <Icon name="warning" size={11} />
                {startError}
              </p>
            )}

            <button
              onClick={handleStartProxy}
              disabled={!targetUrl.trim() || starting}
              className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Icon name="gateway" size={14} className={starting ? 'animate-spin' : ''} />
              {starting ? 'Starting...' : 'Start Proxy'}
            </button>

            <p className="text-xs text-gray-600 text-center">
              Agents connect to <span className="text-gray-400 font-mono">http://localhost:{proxyPort || '9090'}/mcp</span> instead of the MCP server directly.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Stats bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="Total Requests"
              value={status?.stats.total_requests ?? 0}
              icon="activity"
              accent="indigo"
              index={0}
            />
            <StatCard
              label="Blocked"
              value={status?.stats.blocked ?? 0}
              icon="shield"
              accent="red"
              index={1}
            />
            <StatCard
              label="Alerts Generated"
              value={status?.stats.alerts_generated ?? 0}
              icon="alert"
              accent="amber"
              index={2}
            />
            <StatCard
              label="Uptime"
              value={formatUptime(status?.uptime_seconds ?? 0)}
              icon="clock"
              accent="emerald"
              index={3}
            />
          </div>

          {/* Filter controls */}
          <div className="flex items-center gap-4 mb-4">
            <select
              value={agentFilter}
              onChange={e => setAgentFilter(e.target.value)}
              className="bg-gray-900/50 border border-gray-800/60 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500/50"
            >
              <option value="">All agents</option>
              {agents.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>

            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={blockedOnly}
                onChange={e => setBlockedOnly(e.target.checked)}
                className="rounded border-gray-700 bg-gray-800 text-indigo-500 focus:ring-indigo-500/30"
              />
              Blocked only
            </label>

            <span className="text-xs text-gray-600 ml-auto">
              Auto-refreshing every 2s
            </span>
          </div>

          {/* Traffic table */}
          <div className="bg-gray-900/30 border border-gray-800/60 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800/60">
                    <th className="text-left px-4 py-3 text-gray-500 font-medium">Time</th>
                    <th className="text-left px-4 py-3 text-gray-500 font-medium">Agent</th>
                    <th className="text-left px-4 py-3 text-gray-500 font-medium">Method</th>
                    <th className="text-left px-4 py-3 text-gray-500 font-medium">Tool</th>
                    <th className="text-left px-4 py-3 text-gray-500 font-medium">Decision</th>
                    <th className="text-right px-4 py-3 text-gray-500 font-medium">Duration</th>
                    <th className="text-right px-4 py-3 text-gray-500 font-medium">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {traffic.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-12 text-center text-gray-600">
                        {blockedOnly
                          ? 'No blocked requests'
                          : 'No traffic yet — send a JSON-RPC request to the proxy'}
                      </td>
                    </tr>
                  ) : (
                    traffic.map((entry) => (
                      <tr
                        key={entry.timestamp + entry.agent + entry.tool}
                        className={`border-b border-gray-800/30 ${decisionBg[entry.decision] || ''} hover:bg-gray-800/20 transition-colors`}
                      >
                        <td className="px-4 py-2.5 text-gray-500 font-mono text-xs whitespace-nowrap">
                          <RelativeTime timestamp={entry.timestamp} />
                        </td>
                        <td className="px-4 py-2.5 text-gray-300 font-medium">
                          {entry.agent}
                        </td>
                        <td className="px-4 py-2.5 text-gray-400 font-mono text-xs">
                          {entry.method}
                        </td>
                        <td className="px-4 py-2.5 text-gray-300">
                          {entry.tool || '-'}
                        </td>
                        <td className={`px-4 py-2.5 font-medium ${decisionColors[entry.decision] || 'text-gray-400'}`}>
                          {entry.decision}
                        </td>
                        <td className="px-4 py-2.5 text-gray-500 text-right font-mono text-xs">
                          {entry.duration_ms}ms
                        </td>
                        <td className="px-4 py-2.5 text-gray-500 text-right font-mono text-xs">
                          {entry.data_bytes > 1024
                            ? `${(entry.data_bytes / 1024).toFixed(1)}KB`
                            : `${entry.data_bytes}B`}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
