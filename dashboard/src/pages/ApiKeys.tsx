import { useEffect, useState } from 'react'
import { api, ApiKeyInfo, ApiKeyCreated } from '../api'
import PageHeader from '../components/PageHeader'
import RelativeTime from '../components/RelativeTime'
import Icon from '../components/Icon'
import { SkeletonTable } from '../components/Skeleton'
import ConnectionError from '../components/ConnectionError'

export default function ApiKeys() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')

  // Create form
  const [keyName, setKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState<ApiKeyCreated | null>(null)
  const [copied, setCopied] = useState(false)

  const load = () => {
    api.listApiKeys()
      .then(data => { setKeys(data); setLoaded(true) })
      .catch(e => setError(e.message))
  }

  useEffect(load, [])

  const handleCreate = async () => {
    const name = keyName.trim() || 'Default'
    setCreating(true)
    setError('')
    try {
      const result = await api.createApiKey(name)
      setNewKey(result)
      setKeyName('')
      load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setCreating(false)
    }
  }

  const handleRevoke = async (keyId: number) => {
    try {
      await api.revokeApiKey(keyId)
      load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const copyKey = () => {
    if (!newKey) return
    navigator.clipboard.writeText(newKey.raw_key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const activeKeys = keys.filter(k => !k.revoked)
  const revokedKeys = keys.filter(k => k.revoked)

  if (error && !loaded) return (
    <div className="space-y-6">
      <PageHeader title="API Keys" subtitle="Manage keys for proxy-to-cloud telemetry" />
      <ConnectionError onRetry={load} />
    </div>
  )

  return (
    <div className="space-y-6">
      <PageHeader title="API Keys" subtitle="Manage keys for proxy-to-cloud telemetry" />

      {/* Create new key */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
          <Icon name="key" size={16} className="text-indigo-400" />
          Create New API Key
        </h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-500 mb-1">Key Name</label>
            <input
              value={keyName}
              onChange={e => setKeyName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
              placeholder="e.g. Production Proxy"
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
          </div>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Icon name="key" size={14} />
            {creating ? 'Creating...' : 'Create Key'}
          </button>
        </div>
      </div>

      {/* New key display */}
      {newKey && (
        <div className="glass-card border-emerald-500/30 p-5 animate-slideUp">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-2">
                <Icon name="check" size={16} /> API key created successfully
              </p>
              <p className="text-xs text-gray-500 mb-2">
                Copy this key now — it won't be shown again. Use it as a Bearer token
                when starting the Navil proxy.
              </p>
              <code className="block bg-gray-800 rounded-lg p-3 text-xs text-gray-300 font-mono break-all max-w-2xl">
                {newKey.raw_key}
              </code>
              <div className="mt-3 p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                <p className="text-xs text-gray-400 font-medium mb-1">Quick start:</p>
                <code className="text-xs text-indigo-300 font-mono">
                  navil proxy start --target &lt;MCP_SERVER&gt; --cloud-key {newKey.raw_key.slice(0, 16)}...
                </code>
              </div>
            </div>
            <div className="flex gap-2 ml-4">
              <button
                onClick={copyKey}
                className="px-3 py-1.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs hover:bg-emerald-500/25 flex items-center gap-1"
              >
                <Icon name="check" size={12} />
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={() => setNewKey(null)}
                className="px-2 py-1.5 text-gray-500 hover:text-gray-300"
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Active keys table */}
      {!loaded ? <SkeletonTable rows={3} cols={5} /> : (
        <>
          <div className="glass-card overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-800/60 bg-gray-900/40">
              <h3 className="text-sm font-medium text-gray-300">
                Active Keys ({activeKeys.length})
              </h3>
            </div>
            {activeKeys.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-500">
                No active API keys. Create one above to connect your proxy.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800/60 text-gray-400 text-left bg-gray-900/20">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Key Prefix</th>
                    <th className="px-4 py-3 font-medium">Scopes</th>
                    <th className="px-4 py-3 font-medium">Created</th>
                    <th className="px-4 py-3 font-medium">Last Used</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {activeKeys.map((k, i) => (
                    <tr
                      key={k.id}
                      className="border-b border-gray-800/30 animate-fadeIn opacity-0"
                      style={{ animationDelay: `${i * 0.04}s` }}
                    >
                      <td className="px-4 py-3 text-gray-300">{k.name}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">{k.key_prefix}...</td>
                      <td className="px-4 py-3">
                        {k.scopes.map(s => (
                          <span key={s} className="mr-1 px-2 py-0.5 bg-indigo-500/10 text-indigo-300/80 border border-indigo-500/20 rounded-full text-xs">
                            {s}
                          </span>
                        ))}
                      </td>
                      <td className="px-4 py-3">
                        <RelativeTime timestamp={k.created_at} className="text-gray-400 text-xs" />
                      </td>
                      <td className="px-4 py-3">
                        {k.last_used_at ? (
                          <RelativeTime timestamp={k.last_used_at} className="text-gray-400 text-xs" />
                        ) : (
                          <span className="text-gray-600 text-xs">Never</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleRevoke(k.id)}
                          className="px-2 py-1 bg-red-500/15 text-red-400 border border-red-500/30 rounded text-xs hover:bg-red-500/25 flex items-center gap-1"
                        >
                          <Icon name="x" size={12} /> Revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Revoked keys (collapsed) */}
          {revokedKeys.length > 0 && (
            <details className="glass-card overflow-hidden">
              <summary className="px-4 py-3 cursor-pointer text-sm text-gray-500 hover:text-gray-300 transition-colors select-none">
                Revoked Keys ({revokedKeys.length})
              </summary>
              <table className="w-full text-sm opacity-60">
                <thead>
                  <tr className="border-b border-gray-800/60 text-gray-500 text-left bg-gray-900/20">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Key Prefix</th>
                    <th className="px-4 py-3 font-medium">Created</th>
                    <th className="px-4 py-3 font-medium">Last Used</th>
                  </tr>
                </thead>
                <tbody>
                  {revokedKeys.map(k => (
                    <tr key={k.id} className="border-b border-gray-800/30">
                      <td className="px-4 py-3 text-gray-500 line-through">{k.name}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-600">{k.key_prefix}...</td>
                      <td className="px-4 py-3">
                        <RelativeTime timestamp={k.created_at} className="text-gray-600 text-xs" />
                      </td>
                      <td className="px-4 py-3">
                        {k.last_used_at ? (
                          <RelativeTime timestamp={k.last_used_at} className="text-gray-600 text-xs" />
                        ) : (
                          <span className="text-gray-700 text-xs">Never</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          )}
        </>
      )}
    </div>
  )
}
