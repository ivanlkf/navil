import { useEffect, useState } from 'react'
import { api, Credential, Agent } from '../api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import RelativeTime from '../components/RelativeTime'
import Icon from '../components/Icon'
import { SkeletonTable } from '../components/Skeleton'
import ConnectionError from '../components/ConnectionError'

const TTL_OPTIONS = [
  { label: '1 hour', value: 3600 },
  { label: '8 hours', value: 28800 },
  { label: '24 hours', value: 86400 },
  { label: '7 days', value: 604800 },
]

export default function Credentials() {
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')

  // Issue form
  const [agentName, setAgentName] = useState('')
  const [scope, setScope] = useState('read:tools')
  const [ttl, setTtl] = useState(3600)
  const [issuing, setIssuing] = useState(false)
  const [newToken, setNewToken] = useState('')
  const [copied, setCopied] = useState(false)

  const load = () => {
    Promise.all([api.getCredentials(), api.getAgents()])
      .then(([creds, agts]) => { setCredentials(creds); setAgents(agts); setLoaded(true) })
      .catch(e => setError(e.message))
  }

  useEffect(load, [])

  const handleIssue = async () => {
    if (!agentName) return
    setIssuing(true)
    setError('')
    try {
      const result = await api.issueCredential(agentName, scope, ttl)
      setNewToken(result.token)
      load() // refresh list
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setIssuing(false)
    }
  }

  const handleRevoke = async (tokenId: string) => {
    try {
      await api.revokeCredential(tokenId)
      load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const copyToken = () => {
    navigator.clipboard.writeText(newToken)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (error && !loaded) return (
    <div className="space-y-6">
      <PageHeader title="Credentials" subtitle="Manage agent API tokens" />
      <ConnectionError onRetry={load} />
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader title="Credentials" subtitle="Manage agent API tokens" />

      {/* Issue new credential */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
          <Icon name="key" size={16} className="text-indigo-400" />
          Issue New Credential
        </h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Agent</label>
            <select
              value={agentName}
              onChange={e => setAgentName(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">Select agent...</option>
              {agents.map(a => <option key={a.name} value={a.name}>{a.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Scope</label>
            <input
              value={scope}
              onChange={e => setScope(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none w-48"
              placeholder="read:tools write:logs"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">TTL</label>
            <select
              value={ttl}
              onChange={e => setTtl(Number(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
            >
              {TTL_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <button
            onClick={handleIssue}
            disabled={!agentName || issuing}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icon name="key" size={14} />
            {issuing ? 'Issuing...' : 'Issue Token'}
          </button>
        </div>
      </div>

      {/* New token display */}
      {newToken && (
        <div className="glass-card border-emerald-500/30 p-5 animate-slideUp">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-2">
                <Icon name="check" size={16} /> Token issued successfully
              </p>
              <p className="text-xs text-gray-500 mb-2">Copy this token now — it won't be shown again.</p>
              <code className="block bg-gray-800 rounded-lg p-3 text-xs text-gray-300 font-mono break-all max-w-2xl">
                {newToken}
              </code>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyToken}
                className="px-3 py-1.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs hover:bg-emerald-500/25 flex items-center gap-1"
              >
                <Icon name="check" size={12} />
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={() => setNewToken('')}
                className="px-2 py-1.5 text-gray-500 hover:text-gray-300"
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Credentials table */}
      {!loaded ? <SkeletonTable rows={5} cols={6} /> : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800/60 text-gray-400 text-left bg-gray-900/40">
                <th className="px-4 py-3 font-medium">Token ID</th>
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Scope</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Issued</th>
                <th className="px-4 py-3 font-medium">Expires</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {credentials.map((c, i) => (
                <tr
                  key={c.token_id}
                  className={`border-b border-gray-800/30 animate-fadeIn opacity-0 ${
                    c.status === 'REVOKED' ? 'opacity-50' : ''
                  }`}
                  style={{ animationDelay: `${i * 0.04}s` }}
                >
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{c.token_id.slice(0, 16)}...</td>
                  <td className="px-4 py-3 text-gray-300">{c.agent_name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-300/80 border border-indigo-500/20 rounded-full text-xs">
                      {c.scope}
                    </span>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-3"><RelativeTime timestamp={c.issued_at} className="text-gray-400 text-xs" /></td>
                  <td className="px-4 py-3"><RelativeTime timestamp={c.expires_at} className="text-gray-400 text-xs" /></td>
                  <td className="px-4 py-3">
                    {c.status === 'ACTIVE' && (
                      <button
                        onClick={() => handleRevoke(c.token_id)}
                        className="px-2 py-1 bg-red-500/15 text-red-400 border border-red-500/30 rounded text-xs hover:bg-red-500/25 flex items-center gap-1"
                      >
                        <Icon name="x" size={12} /> Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
