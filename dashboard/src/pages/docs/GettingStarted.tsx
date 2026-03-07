import { Link } from 'react-router-dom'
import CodeBlock from '../../components/CodeBlock'

export default function GettingStarted() {
  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">Getting Started</h1>

      <p>
        Navil is an open-source security toolkit for the Model Context Protocol (MCP). It provides
        config scanning, policy enforcement, traffic proxying, penetration testing, and AI-powered
        analysis — all from a single install. Get up and running in 2 minutes.
      </p>

      {/* Installation */}
      <h2>Installation</h2>
      <p>Install the core package from PyPI:</p>
      <CodeBlock code="pip install navil" language="bash" />

      <p>For cloud dashboard features:</p>
      <CodeBlock code="pip install navil[cloud]" language="bash" />

      <p>For LLM-powered analysis:</p>
      <CodeBlock code="pip install navil[llm]" language="bash" />

      <p>For everything (proxy, cloud, LLM, pentest):</p>
      <CodeBlock code="pip install navil[all]" language="bash" />

      {/* First Scan */}
      <h2>Your First Scan</h2>
      <p>
        Create a JSON config file that describes your MCP server setup. Here is an example:
      </p>
      <CodeBlock
        code={`{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {
        "API_KEY": "sk-example-key-12345"
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

      <p>Run the scanner against your config:</p>
      <CodeBlock code="navil scan config.json" language="bash" />

      <p>
        The scanner will analyze your configuration for hardcoded credentials, overly permissive
        permissions, insecure protocols, and known malicious patterns. Results are displayed in the
        terminal with severity ratings.
      </p>

      {/* Dashboard */}
      <h2>Start the Dashboard</h2>
      <p>Launch the Navil dashboard for a visual overview of your security posture:</p>
      <CodeBlock code="navil cloud serve" language="bash" />

      <p>
        The dashboard opens at <code>http://localhost:8484</code> and provides real-time monitoring
        of agents, alerts, scan results, and policy decisions.
      </p>

      {/* Proxy */}
      <h2>Start the Security Proxy</h2>
      <p>
        Intercept and inspect MCP traffic in real time by running the security proxy:
      </p>
      <CodeBlock code="navil proxy --target http://localhost:3000" language="bash" />

      <p>
        The proxy listens on port <code>9090</code> by default. It sits between your MCP client and
        server, inspecting every JSON-RPC call, enforcing policies, and logging traffic for the
        dashboard.
      </p>

      {/* Next Steps */}
      <h2>Next Steps</h2>
      <ul>
        <li>
          <Link to="/docs/configuration">Configuration</Link> — Environment variables, config file
          format, and policy YAML.
        </li>
        <li>
          <Link to="/docs/policy-engine">Policy Engine</Link> — Fine-grained access control for
          agent tool calls.
        </li>
        <li>
          <Link to="/docs/proxy">Security Proxy</Link> — Real-time traffic interception and
          monitoring.
        </li>
      </ul>
    </div>
  )
}
