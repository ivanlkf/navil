import CodeBlock from '../../components/CodeBlock'

export default function Proxy() {
  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">Security Proxy</h1>

      <p>
        The Navil security proxy provides real-time MCP traffic interception with JSON-RPC
        inspection. It sits between your MCP client and server, applying policies, enforcing
        authentication, and logging every call for the dashboard.
      </p>

      {/* Starting the Proxy */}
      <h2>Starting the Proxy</h2>
      <p>Start the proxy from the command line by specifying the target MCP server:</p>
      <CodeBlock
        code={`# Point the proxy at your MCP server
navil proxy --target http://localhost:3000

# Customize the proxy listen port (default: 9090)
navil proxy --target http://localhost:3000 --port 9091

# Enable verbose logging
navil proxy --target http://localhost:3000 --verbose`}
        language="bash"
      />

      <p>You can also start the proxy through the REST API:</p>
      <CodeBlock
        code={`curl -X POST http://localhost:8484/api/proxy/start \\
  -H "Content-Type: application/json" \\
  -d '{
    "target": "http://localhost:3000",
    "port": 9090
  }'`}
        language="bash"
      />

      {/* How It Works */}
      <h2>How It Works</h2>
      <p>The security proxy operates as a transparent intermediary in the MCP communication chain:</p>
      <ol>
        <li>
          <strong>Intercept</strong> — The proxy receives all JSON-RPC requests from the MCP client
          before they reach the server.
        </li>
        <li>
          <strong>Inspect</strong> — Each request is parsed and analyzed. Tool calls, parameters,
          and metadata are extracted for policy evaluation.
        </li>
        <li>
          <strong>Enforce</strong> — Requests are checked against the active policy. Denied calls
          are blocked and logged. Rate-limited calls are throttled.
        </li>
        <li>
          <strong>Forward</strong> — Permitted requests are forwarded to the target MCP server. The
          response is relayed back to the client.
        </li>
        <li>
          <strong>Log</strong> — All traffic (requests, responses, and policy decisions) is recorded
          and made available through the dashboard and traffic API.
        </li>
      </ol>

      {/* Traffic Monitoring */}
      <h2>Traffic Monitoring</h2>
      <p>
        View live proxy traffic in the dashboard Gateway page, which displays all intercepted
        requests with method, parameters, policy decision, and timing.
      </p>
      <p>
        Programmatically retrieve traffic data through the API:
      </p>
      <CodeBlock
        code={`# Get proxy traffic log
curl http://localhost:8484/api/proxy/traffic

# Check proxy status
curl http://localhost:8484/api/proxy/status`}
        language="bash"
      />
      <p>The traffic endpoint returns a list of intercepted calls with timestamps, methods, policy
        verdicts, and response times.</p>

      {/* Authentication */}
      <h2>Authentication</h2>
      <p>
        The proxy can enforce authentication on incoming MCP requests. When enabled, clients must
        include a bearer token sourced from the Navil credential manager:
      </p>
      <CodeBlock
        code={`# Start proxy with auth enforcement
navil proxy --target http://localhost:3000 --require-auth`}
        language="bash"
      />
      <p>
        Clients must then include an <code>Authorization</code> header with a valid bearer token.
        Tokens are managed through the credentials API (<code>GET /api/credentials</code>) or the
        dashboard Credentials page.
      </p>
      <p>
        Unauthenticated requests receive a <code>401 Unauthorized</code> response and are logged
        as blocked traffic in the dashboard.
      </p>
    </div>
  )
}
