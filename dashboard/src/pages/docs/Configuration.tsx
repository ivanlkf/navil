import { Link } from 'react-router-dom'
import CodeBlock from '../../components/CodeBlock'

interface EnvVar {
  name: string
  description: string
  required: boolean
  category: string
}

const envVars: EnvVar[] = [
  // Auth
  { name: 'CLERK_SECRET_KEY', description: 'Clerk backend secret key for authentication', required: false, category: 'Auth' },
  { name: 'CLERK_ISSUER_URL', description: 'Clerk JWT issuer URL for token verification', required: false, category: 'Auth' },
  { name: 'VITE_CLERK_PUBLISHABLE_KEY', description: 'Clerk frontend publishable key', required: false, category: 'Auth' },
  // LLM
  { name: 'ANTHROPIC_API_KEY', description: 'API key for Anthropic Claude models', required: false, category: 'LLM' },
  { name: 'OPENAI_API_KEY', description: 'API key for OpenAI models', required: false, category: 'LLM' },
  { name: 'GEMINI_API_KEY', description: 'API key for Google Gemini models', required: false, category: 'LLM' },
  // Billing
  { name: 'STRIPE_SECRET_KEY', description: 'Stripe secret key for billing integration', required: false, category: 'Billing' },
  { name: 'STRIPE_WEBHOOK_SECRET', description: 'Stripe webhook signing secret', required: false, category: 'Billing' },
  { name: 'STRIPE_PRO_PRICE_ID', description: 'Stripe price ID for Pro plan', required: false, category: 'Billing' },
  // Server
  { name: 'ALLOWED_ORIGINS', description: 'Comma-separated CORS allowed origins', required: false, category: 'Server' },
  { name: 'PORT', description: 'Server port (default: 8484)', required: false, category: 'Server' },
]

export default function Configuration() {
  let lastCategory = ''

  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">Configuration</h1>

      <p>
        Navil is configured through environment variables, a JSON config file for MCP server
        definitions, and optional YAML policy files. This page covers all configuration options.
      </p>

      {/* Environment Variables */}
      <h2>Environment Variables</h2>
      <p>
        Set these environment variables to configure authentication, LLM providers, billing, and
        server behavior. All are optional — Navil runs with sensible defaults.
      </p>

      <div className="overflow-x-auto mb-6">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left py-3 pr-4 text-gray-400 font-medium">Variable</th>
              <th className="text-left py-3 pr-4 text-gray-400 font-medium">Description</th>
              <th className="text-left py-3 text-gray-400 font-medium">Required</th>
            </tr>
          </thead>
          <tbody>
            {envVars.map((v) => {
              const showCategory = v.category !== lastCategory
              lastCategory = v.category
              return (
                <tr key={v.name} className="border-b border-gray-800/50">
                  <td className="py-2.5 pr-4 align-top">
                    {showCategory && (
                      <span className="block text-[10px] uppercase tracking-wider text-gray-600 mb-1">
                        {v.category}
                      </span>
                    )}
                    <code className="text-xs">{v.name}</code>
                  </td>
                  <td className="py-2.5 pr-4 text-gray-400">{v.description}</td>
                  <td className="py-2.5 text-gray-500">{v.required ? 'Yes' : 'No'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Config File Format */}
      <h2>Config File Format</h2>
      <p>
        MCP server configurations are defined in a JSON file following the standard MCP config
        schema. Each server entry specifies a command, arguments, and optional environment variables:
      </p>
      <CodeBlock
        code={`{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {
        "API_KEY": "your-api-key"
      }
    },
    "database": {
      "command": "python",
      "args": ["-m", "mcp_server_db"],
      "env": {
        "DB_URL": "postgresql://user:pass@localhost/mydb"
      }
    }
  }
}`}
        language="json"
        filename="config.json"
      />
      <p>
        Pass this file to the scanner with <code>navil scan config.json</code>. The scanner detects
        hardcoded credentials, insecure protocols, overly permissive paths, and known malicious
        server patterns.
      </p>

      {/* Policy YAML */}
      <h2>Policy YAML Format</h2>
      <p>
        Policies are defined in YAML files and control which agents can invoke which tools, with
        optional rate limits and data sensitivity constraints. See the{' '}
        <Link to="/docs/policy-engine">Policy Engine</Link> documentation for the full format
        reference, rule types, and condition options.
      </p>
      <CodeBlock
        code={`policies:
  - agent: "data-agent"
    rules:
      - tool: "database_query"
        action: "allow"
        conditions:
          max_rate: 100
      - tool: "*"
        action: "deny"`}
        language="yaml"
        filename="policy.yaml"
      />
    </div>
  )
}
