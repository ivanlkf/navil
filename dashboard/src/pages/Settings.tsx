import { useEffect, useState } from 'react'
import { api, LLMConfig } from '../api'
import PageHeader from '../components/PageHeader'
import Icon from '../components/Icon'
import useBilling from '../hooks/useBilling'
import useSessionState from '../hooks/useSessionState'
import { isAnyAuthRequired } from '../auth/ClerkProviderWrapper'

const providers = [
  { value: 'anthropic', label: 'Anthropic (Claude)', hint: 'ANTHROPIC_API_KEY' },
  { value: 'openai', label: 'OpenAI', hint: 'OPENAI_API_KEY' },
  { value: 'gemini', label: 'Google Gemini', hint: 'GEMINI_API_KEY' },
  { value: 'ollama', label: 'Ollama (Local)', hint: 'No API key needed — runs locally at localhost:11434' },
  { value: 'openai_compatible', label: 'OpenAI Compatible', hint: 'Any OpenAI-compatible API' },
]

const compatibleExamples = [
  { name: 'OpenRouter', url: 'https://openrouter.ai/api/v1' },
  { name: 'Together AI', url: 'https://api.together.xyz/v1' },
  { name: 'Groq', url: 'https://api.groq.com/openai/v1' },
  { name: 'DeepSeek', url: 'https://api.deepseek.com/v1' },
  { name: 'Fireworks', url: 'https://api.fireworks.ai/inference/v1' },
  { name: 'Ollama', url: 'http://localhost:11434/v1' },
]

export default function Settings() {
  const { plan, canUseLLM, hasByokKey, llmCallCount, stripeEnabled, setPlan, checkout, portal } = useBilling()
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const checkoutSuccess = new URLSearchParams(window.location.search).get('checkout') === 'success'
  const [config, setConfig] = useState<LLMConfig | null>(null)
  const [provider, setProvider] = useState('anthropic')
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [saveResult, setSaveResult] = useSessionState<{ ok: boolean; msg: string } | null>('settings_save', null)
  const [testResult, setTestResult] = useSessionState<{ ok: boolean; msg: string } | null>('settings_test', null)

  const isOllama = provider === 'ollama'
  const isCompatible = provider === 'openai_compatible'

  useEffect(() => {
    api.getLLMSettings().then(c => {
      setConfig(c)
      if (c.provider) {
        // Map internal provider names back to UI values
        if (c.provider === 'openai' && c.base_url?.includes('11434')) setProvider('ollama')
        else if (c.provider === 'openai' && c.base_url) setProvider('openai_compatible')
        else setProvider(c.provider)
      }
      if (c.base_url) setBaseUrl(c.base_url)
    }).catch(() => {})
  }, [])

  const handleSave = async () => {
    if (!apiKey.trim() && !isCompatible && !isOllama) return
    if (isCompatible && !baseUrl.trim()) return
    setSaving(true)
    setSaveResult(null)
    setTestResult(null)
    try {
      const res = await api.updateLLMSettings(provider, apiKey.trim(), baseUrl.trim(), model.trim())
      setConfig(res)
      setApiKey('')
      setSaveResult({ ok: true, msg: 'LLM configuration saved successfully.' })
    } catch (e: unknown) {
      setSaveResult({ ok: false, msg: e instanceof Error ? e.message : String(e) })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      // Send current form values so the test uses what's on screen, not the saved config
      const res = await api.testLLMConnection(provider, apiKey.trim(), baseUrl.trim(), model.trim())
      setTestResult(res.success
        ? { ok: true, msg: 'Connection successful!' }
        : { ok: false, msg: res.error || 'Connection failed.' }
      )
    } catch (e: unknown) {
      setTestResult({ ok: false, msg: e instanceof Error ? e.message : String(e) })
    } finally {
      setTesting(false)
    }
  }

  const selectedHint = providers.find(p => p.value === provider)?.hint
  const canSave = isOllama
    ? (model.trim() || true)  // Ollama always saveable — no key needed
    : isCompatible
      ? baseUrl.trim() && (apiKey.trim() || config?.api_key_set)
      : apiKey.trim()

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Configure Navil preferences" />

      {/* Checkout success banner */}
      {checkoutSuccess && (
        <div className="p-4 rounded-lg border bg-emerald-500/5 border-emerald-500/20 flex items-center gap-3 animate-fadeIn">
          <Icon name="check" size={18} className="text-emerald-400 shrink-0" />
          <div>
            <p className="text-sm text-emerald-400 font-medium">Welcome to {plan === 'elite' ? 'Elite' : 'Lite'}!</p>
            <p className="text-xs text-gray-400">Your subscription is active. {plan === 'elite' ? 'All features and analytics are now unlocked.' : 'All AI features are now unlocked.'}</p>
          </div>
        </div>
      )}

      {/* Subscription */}
      <div className="glass-card p-6 animate-slideUp opacity-0 stagger-1">
        <h3 className="text-sm font-medium text-gray-300 mb-5 flex items-center gap-2">
          <Icon name="shield" size={16} className="text-violet-400" />
          Subscription
        </h3>

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
              plan === 'elite'
                ? 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30'
                : plan === 'lite'
                  ? 'bg-violet-500/15 text-violet-400 border-violet-500/30'
                  : 'bg-gray-800 text-gray-400 border-gray-700'
            }`}>
              {plan === 'elite' ? 'Elite' : plan === 'lite' ? 'Lite' : 'Free'}
            </span>
            <div>
              <p className="text-sm text-gray-300">
                {plan === 'elite' ? 'Full analytics & trust scoring' : plan === 'lite' ? 'All AI features unlocked' : 'Core monitoring features'}
              </p>
              <p className="text-xs text-gray-600 mt-0.5">
                {hasByokKey
                  ? 'BYOK key configured — AI features available regardless of plan'
                  : plan === 'free'
                    ? 'Upgrade to Lite or add your own API key to unlock AI features'
                    : `${llmCallCount} AI calls this session`
                }
              </p>
            </div>
          </div>

          {stripeEnabled ? (
            plan !== 'free' ? (
              <button
                onClick={() => portal()}
                className="px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 bg-gray-800 text-gray-400 border border-gray-700 hover:bg-gray-700"
              >
                <Icon name="settings" size={14} />
                Manage Subscription
              </button>
            ) : (
              <button
                onClick={async () => { setCheckoutLoading(true); await checkout(); setCheckoutLoading(false) }}
                disabled={checkoutLoading}
                className="px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50"
              >
                <Icon name="sparkles" size={14} />
                {checkoutLoading ? 'Redirecting...' : 'Upgrade'}
              </button>
            )
          ) : (
            <div className="flex items-center gap-2">
              {(['free', 'lite', 'elite'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPlan(p)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg ${
                    plan === p
                      ? 'bg-violet-600 text-white'
                      : 'bg-gray-800 text-gray-400 border border-gray-700 hover:bg-gray-700'
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* AI access status */}
        <div className={`p-3 rounded-lg border flex items-center gap-3 ${
          canUseLLM
            ? 'bg-emerald-500/5 border-emerald-500/20'
            : 'bg-amber-500/5 border-amber-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full ${canUseLLM ? 'bg-emerald-400' : 'bg-amber-400'}`} />
          <p className={`text-sm ${canUseLLM ? 'text-emerald-400' : 'text-amber-400'}`}>
            {canUseLLM ? 'AI features enabled' : 'AI features locked'}
          </p>
        </div>

        {!stripeEnabled && (
          <p className="text-xs text-gray-600 mt-3 flex items-center gap-1">
            <Icon name="info" size={10} className="text-gray-600" />
            Subscription is session-only for demo. Configure Stripe for real billing.
          </p>
        )}
      </div>

      {/* LLM Configuration */}
      <div className="glass-card p-6 animate-slideUp opacity-0 stagger-2">
        <h3 className="text-sm font-medium text-gray-300 mb-5 flex items-center gap-2">
          <Icon name="sparkles" size={16} className="text-violet-400" />
          LLM Configuration
        </h3>

        {/* Connection status */}
        {config && (
          <div className={`mb-5 p-3 rounded-lg border flex items-center gap-3 ${
            config.api_key_set
              ? 'bg-emerald-500/5 border-emerald-500/20'
              : 'bg-amber-500/5 border-amber-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${config.api_key_set ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <div>
              <p className={`text-sm ${config.api_key_set ? 'text-emerald-400' : 'text-amber-400'}`}>
                {config.api_key_set ? 'Connected' : 'Not configured'}
              </p>
              {config.api_key_set && (
                <p className="text-xs text-gray-500">
                  Provider: {config.provider} · Model: {config.model}
                  {config.base_url ? ` · ${config.base_url}` : ''}
                </p>
              )}
            </div>
          </div>
        )}

        {config && !config.available && (
          <div className="mb-5 p-3 rounded-lg border bg-red-500/5 border-red-500/20 flex items-center gap-3">
            <Icon name="warning" size={14} className="text-red-400 shrink-0" />
            <div>
              <p className="text-sm text-red-400">LLM SDKs not installed</p>
              <p className="text-xs text-gray-500">
                Install with: <code className="font-mono text-red-400/80">pip install navil[llm]</code>
              </p>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {/* Provider */}
          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Provider</label>
            <select
              value={provider}
              onChange={e => { setProvider(e.target.value); setSaveResult(null); setTestResult(null) }}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none"
            >
              {providers.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <p className="text-xs text-gray-600 mt-1">
              {isOllama
                ? 'Runs locally — no API key needed. Make sure Ollama is running on your machine.'
                : isCompatible
                  ? 'Works with OpenRouter, Together AI, Groq, DeepSeek, Fireworks, and any OpenAI-compatible API'
                  : <>Or set via environment variable: <code className="font-mono text-gray-500">{selectedHint}</code></>
              }
            </p>
          </div>

          {/* Base URL — only for OpenAI Compatible */}
          {isCompatible && (
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Base URL</label>
              <input
                value={baseUrl}
                onChange={e => { setBaseUrl(e.target.value); setSaveResult(null) }}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none font-mono"
                placeholder="https://api.example.com/v1"
                
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {compatibleExamples.map(ex => (
                  <button
                    key={ex.name}
                    onClick={() => { setBaseUrl(ex.url); setSaveResult(null) }}
                    className="px-2 py-0.5 text-[10px] bg-gray-800 text-gray-400 border border-gray-700 rounded hover:border-gray-600 hover:text-gray-300"
                  >
                    {ex.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Model override — for compatible/ollama or when user wants to customize */}
          {(isCompatible || isOllama) && (
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Model {!isOllama && <span className="text-gray-600">(optional)</span>}</label>
              <input
                value={model}
                onChange={e => { setModel(e.target.value); setSaveResult(null) }}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none font-mono"
                placeholder={isOllama ? 'e.g., llama3.2, deepseek-r1:70b, qwen3' : 'e.g., anthropic/claude-sonnet-4, deepseek-chat, llama-3.1-70b'}
                
              />
            </div>
          )}

          {/* API Key — hidden for Ollama */}
          {!isOllama && <div>
            <label className="block text-xs text-gray-500 mb-1.5">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={e => { setApiKey(e.target.value); setSaveResult(null) }}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:border-indigo-500 focus:outline-none font-mono"
              placeholder={config?.api_key_set ? '••••••••  (key is set — enter new to replace)' : 'Paste your API key here'}
              
            />
            <p className="text-xs text-gray-600 mt-1 flex items-center gap-1">
              <Icon name="lock" size={10} className="text-gray-600" />
              Stored in memory only. Not persisted to disk.
            </p>
          </div>}

          {/* Buttons */}
          <div className="flex gap-3 pt-1">
            <button
              onClick={handleSave}
              disabled={!canSave || saving}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Icon name="check" size={14} />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleTest}
              disabled={testing || (!config?.api_key_set && !isOllama && !apiKey.trim())}
              className="px-4 py-2 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Icon name="activity" size={14} className={testing ? 'animate-spin' : ''} />
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
          </div>

          {/* Result messages */}
          {saveResult && (
            <div className={`p-3 rounded-lg border animate-fadeIn ${
              saveResult.ok ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
            }`}>
              <p className={`text-sm flex items-center gap-2 ${saveResult.ok ? 'text-emerald-400' : 'text-red-400'}`}>
                <Icon name={saveResult.ok ? 'check' : 'warning'} size={14} />
                {saveResult.msg}
              </p>
            </div>
          )}
          {testResult && (
            <div className={`p-3 rounded-lg border animate-fadeIn ${
              testResult.ok ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'
            }`}>
              <p className={`text-sm flex items-center gap-2 ${testResult.ok ? 'text-emerald-400' : 'text-red-400'}`}>
                <Icon name={testResult.ok ? 'check' : 'warning'} size={14} className="shrink-0" />
                <span className="line-clamp-2 break-words">{testResult.msg}</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Authentication */}
      {!isAnyAuthRequired() && (
        <div className="glass-card p-6 animate-slideUp opacity-0 stagger-3">
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <Icon name="lock" size={16} className="text-amber-400" />
            Authentication
          </h3>
          <div className="p-3 rounded-lg border bg-amber-500/5 border-amber-500/20 mb-4 flex items-start gap-3">
            <Icon name="warning" size={14} className="text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-amber-400">No authentication configured</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Your dashboard is publicly accessible. Enable auth to require sign-in.
              </p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <p className="text-gray-400">To enable authentication, set the environment variable before starting the dashboard:</p>
            <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs text-gray-300 border border-gray-800">
              <p className="text-gray-500"># Local auth (email-based, stored in browser)</p>
              <p>VITE_NAVIL_AUTH=true npm run dev</p>
            </div>
            <p className="text-xs text-gray-500">
              Users will be prompted to sign in with their email. Sessions are stored in localStorage.
            </p>
          </div>
        </div>
      )}

      {/* About */}
      <div className="glass-card p-6 animate-slideUp opacity-0 stagger-3">
        <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
          <Icon name="info" size={16} className="text-gray-400" />
          About
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Version</span>
            <span className="text-gray-300 font-mono">{import.meta.env.VITE_APP_VERSION || '0.1.0'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">LLM SDK</span>
            <span className={`font-mono ${config?.available ? 'text-emerald-400' : 'text-red-400'}`}>
              {config?.available ? 'Installed' : 'Not installed'}
            </span>
          </div>
          {config?.api_key_set && (
            <>
              <div className="flex justify-between">
                <span className="text-gray-500">Active Provider</span>
                <span className="text-gray-300 font-mono">{config.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Active Model</span>
                <span className="text-gray-300 font-mono">{config.model}</span>
              </div>
              {config.base_url && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Base URL</span>
                  <span className="text-gray-300 font-mono text-xs truncate max-w-[250px]">{config.base_url}</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
