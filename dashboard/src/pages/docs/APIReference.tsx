export default function APIReference() {
  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">API Reference</h1>

      <p>
        Navil exposes a REST API at <code>/api/</code> for all platform features. All endpoints
        accept and return JSON. When authentication is enabled, include a valid bearer token in the{' '}
        <code>Authorization</code> header.
      </p>

      {/* Overview */}
      <h2>Overview</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/overview', description: 'Dashboard summary with agent count, alert count, and system health.' },
        ]}
      />

      {/* Agents */}
      <h2>Agents</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/agents', description: 'List all registered MCP agents with status and metadata.' },
          { method: 'GET', path: '/api/agents/:name', description: 'Get details for a specific agent by name.' },
        ]}
      />

      {/* Alerts */}
      <h2>Alerts</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/alerts', description: 'List all security alerts with severity, type, and timestamps.' },
        ]}
      />

      {/* Scanner */}
      <h2>Scanner</h2>
      <EndpointTable
        endpoints={[
          { method: 'POST', path: '/api/scan', description: 'Submit an MCP config for security analysis. Returns findings with severity ratings.' },
        ]}
      />

      {/* Credentials */}
      <h2>Credentials</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/credentials', description: 'List all stored credentials (metadata only, keys are masked).' },
          { method: 'POST', path: '/api/credentials', description: 'Store a new credential. Encrypted at rest.' },
          { method: 'DELETE', path: '/api/credentials/:id', description: 'Delete a stored credential by ID.' },
        ]}
      />

      {/* Policy */}
      <h2>Policy</h2>
      <EndpointTable
        endpoints={[
          { method: 'POST', path: '/api/policy/check', description: 'Check whether a tool call is permitted under the current policy.' },
          { method: 'GET', path: '/api/policy/decisions', description: 'List recent policy decisions with verdicts and matched rules.' },
        ]}
      />

      {/* Proxy */}
      <h2>Proxy</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/proxy/status', description: 'Get proxy running status, target URL, and uptime.' },
          { method: 'GET', path: '/api/proxy/traffic', description: 'Retrieve intercepted traffic log with methods, timing, and verdicts.' },
          { method: 'POST', path: '/api/proxy/start', description: 'Start the security proxy with a specified target and port.' },
        ]}
      />

      {/* Pentest */}
      <h2>Pentest</h2>
      <EndpointTable
        endpoints={[
          { method: 'POST', path: '/api/pentest', description: 'Run penetration test scenarios. Returns verdicts and detection rate.' },
        ]}
      />

      {/* LLM */}
      <h2>LLM</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/llm/status', description: 'Check LLM provider connectivity and current configuration.' },
          { method: 'POST', path: '/api/llm/explain-anomaly', description: 'Get an AI-generated explanation for a detected anomaly.' },
          { method: 'POST', path: '/api/llm/analyze-config', description: 'Submit an MCP config for AI-powered security review.' },
          { method: 'POST', path: '/api/llm/generate-policy', description: 'Generate a YAML policy from a natural language description.' },
          { method: 'POST', path: '/api/llm/suggest-remediation', description: 'Get AI-suggested remediation steps for a vulnerability.' },
          { method: 'POST', path: '/api/llm/auto-remediate', description: 'Automatically apply AI-generated remediation for a threat.' },
        ]}
      />

      {/* Billing */}
      <h2>Billing</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/billing/plan', description: 'Get the current billing plan and usage limits.' },
          { method: 'POST', path: '/api/billing/plan', description: 'Update the billing plan.' },
          { method: 'POST', path: '/api/billing/checkout', description: 'Create a Stripe checkout session for plan upgrade.' },
          { method: 'POST', path: '/api/billing/portal', description: 'Create a Stripe customer portal session for billing management.' },
        ]}
      />

      {/* Settings */}
      <h2>Settings</h2>
      <EndpointTable
        endpoints={[
          { method: 'GET', path: '/api/settings/llm', description: 'Get current LLM provider settings (API keys are masked).' },
          { method: 'POST', path: '/api/settings/llm', description: 'Update LLM provider, model, and API key configuration.' },
          { method: 'POST', path: '/api/settings/llm/test', description: 'Test LLM provider connectivity with the current configuration.' },
        ]}
      />
    </div>
  )
}

/* ------------------------------------------------------------------ */

interface Endpoint {
  method: string
  path: string
  description: string
}

function EndpointTable({ endpoints }: { endpoints: Endpoint[] }) {
  return (
    <div className="overflow-x-auto mb-6">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left py-3 pr-4 text-gray-400 font-medium w-24">Method</th>
            <th className="text-left py-3 pr-4 text-gray-400 font-medium">Path</th>
            <th className="text-left py-3 text-gray-400 font-medium">Description</th>
          </tr>
        </thead>
        <tbody>
          {endpoints.map((ep) => (
            <tr key={`${ep.method}-${ep.path}`} className="border-b border-gray-800/50">
              <td className="py-2.5 pr-4">
                <span
                  className={`inline-block text-xs font-semibold px-2 py-0.5 rounded ${
                    ep.method === 'GET'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : ep.method === 'POST'
                        ? 'bg-blue-500/10 text-blue-400'
                        : 'bg-red-500/10 text-red-400'
                  }`}
                >
                  {ep.method}
                </span>
              </td>
              <td className="py-2.5 pr-4">
                <code className="text-xs">{ep.path}</code>
              </td>
              <td className="py-2.5 text-gray-400">{ep.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
