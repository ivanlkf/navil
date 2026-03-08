import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiKeyCreated } from '../api'
import Icon from '../components/Icon'

type Step = 1 | 2 | 3 | 4

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(1)
  const [newKey, setNewKey] = useState<ApiKeyCreated | null>(null)
  const [copied, setCopied] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)
  const [polling, setPolling] = useState(false)

  const handleCreateKey = async () => {
    setCreating(true)
    setError('')
    try {
      const result = await api.createApiKey('Default Proxy')
      setNewKey(result)
      setStep(3)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setCreating(false)
    }
  }

  const copyKey = () => {
    if (!newKey) return
    navigator.clipboard.writeText(newKey.raw_key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const copyCommand = () => {
    if (!newKey) return
    const cmd = `pip install navil && navil proxy start --target <YOUR_MCP_SERVER> --cloud-key ${newKey.raw_key}`
    navigator.clipboard.writeText(cmd)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Poll for proxy connection
  const pollConnection = useCallback(async () => {
    try {
      const status = await api.getProxyConnection()
      if (status.status === 'connected') {
        setConnected(true)
        setPolling(false)
      }
    } catch {
      // ignore polling errors
    }
  }, [])

  useEffect(() => {
    if (step === 4 && !connected) {
      setPolling(true)
      const interval = setInterval(pollConnection, 3000)
      return () => clearInterval(interval)
    }
  }, [step, connected, pollConnection])

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        {/* Progress bar */}
        <div className="flex items-center gap-2 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className="flex-1 flex items-center gap-2">
              <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                s <= step ? 'bg-indigo-500' : 'bg-gray-800'
              }`} />
            </div>
          ))}
        </div>

        {/* Step 1: Welcome */}
        {step === 1 && (
          <div className="glass-card p-8 text-center animate-fadeIn">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-indigo-500/20 flex items-center justify-center">
              <Icon name="shield" size={32} className="text-indigo-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-3">
              Secure your MCP servers
            </h1>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              Set up Navil in 3 simple steps. Monitor your AI agents, detect anomalies,
              and enforce security policies — all from your cloud dashboard.
            </p>
            <button
              onClick={() => setStep(2)}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-500 transition-colors"
            >
              Get Started
            </button>
          </div>
        )}

        {/* Step 2: Generate API Key */}
        {step === 2 && (
          <div className="glass-card p-8 animate-fadeIn">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-sm font-bold text-indigo-400">
                1
              </div>
              <h2 className="text-xl font-bold text-white">Generate your API key</h2>
            </div>
            <p className="text-gray-400 mb-6">
              This key authenticates your proxy with Navil Cloud. It will be used to securely
              transmit telemetry data from your MCP servers.
            </p>
            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
            <button
              onClick={handleCreateKey}
              disabled={creating}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Icon name="key" size={16} />
              {creating ? 'Generating...' : 'Generate API Key'}
            </button>
          </div>
        )}

        {/* Step 3: Install & Connect */}
        {step === 3 && newKey && (
          <div className="glass-card p-8 animate-fadeIn space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-sm font-bold text-indigo-400">
                2
              </div>
              <h2 className="text-xl font-bold text-white">Install & connect your proxy</h2>
            </div>

            {/* API Key display */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 font-medium">Your API Key</span>
                <button
                  onClick={copyKey}
                  className="px-2 py-1 text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded hover:bg-emerald-500/25 flex items-center gap-1"
                >
                  <Icon name="check" size={10} />
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <code className="block text-xs text-indigo-300 font-mono break-all">
                {newKey.raw_key}
              </code>
              <p className="text-xs text-amber-400/70 mt-2 flex items-center gap-1">
                <Icon name="alert" size={12} />
                Save this key — it won't be shown again.
              </p>
            </div>

            {/* Install command */}
            <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-800">
              <p className="text-xs text-gray-500 font-medium mb-2">Run on your server:</p>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-gray-600 text-xs mt-0.5">$</span>
                  <code className="text-xs text-gray-300 font-mono">
                    pip install navil
                  </code>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-gray-600 text-xs mt-0.5">$</span>
                  <code className="text-xs text-gray-300 font-mono break-all">
                    navil proxy start --target &lt;YOUR_MCP_SERVER&gt; --cloud-key {newKey.raw_key.slice(0, 20)}...
                  </code>
                </div>
              </div>
              <button
                onClick={copyCommand}
                className="mt-3 px-3 py-1.5 text-xs bg-gray-800 text-gray-400 border border-gray-700 rounded hover:bg-gray-700 hover:text-gray-300 flex items-center gap-1"
              >
                <Icon name="check" size={10} />
                Copy full command
              </button>
            </div>

            <button
              onClick={() => setStep(4)}
              className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-500 transition-colors"
            >
              I've started the proxy
            </button>
          </div>
        )}

        {/* Step 4: Waiting for connection */}
        {step === 4 && (
          <div className="glass-card p-8 text-center animate-fadeIn">
            <div className="flex items-center gap-3 mb-6 justify-center">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-sm font-bold text-indigo-400">
                3
              </div>
              <h2 className="text-xl font-bold text-white">
                {connected ? 'Connected!' : 'Waiting for connection...'}
              </h2>
            </div>

            {connected ? (
              <div className="space-y-6">
                <div className="w-20 h-20 mx-auto rounded-full bg-emerald-500/20 flex items-center justify-center animate-slideUp">
                  <Icon name="check" size={40} className="text-emerald-400" />
                </div>
                <p className="text-gray-400">
                  Your proxy is connected and sending telemetry. Head to the dashboard to
                  monitor your MCP servers.
                </p>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-6 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-500 transition-colors"
                >
                  Go to Dashboard
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {polling && (
                  <div className="w-12 h-12 mx-auto rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
                )}
                <p className="text-gray-500 text-sm">
                  Listening for your proxy's heartbeat...
                </p>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="text-sm text-gray-600 hover:text-gray-400 underline"
                >
                  Skip — I'll connect later
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
