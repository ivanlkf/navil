import CodeBlock from '../../components/CodeBlock'

export default function PolicyEngine() {
  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">Policy Engine</h1>

      <p>
        The policy engine provides YAML-based access control for MCP agents. Define fine-grained
        rules that control which agents can invoke which tools, with support for rate limiting,
        data sensitivity constraints, and time-window restrictions.
      </p>

      {/* Policy Format */}
      <h2>Policy Format</h2>
      <p>
        Policies are defined in YAML. Each policy targets an agent by name and contains a list of
        rules. Rules match on tool names (with wildcard support) and specify an action:
      </p>
      <CodeBlock
        code={`policies:
  - agent: "data-agent"
    rules:
      - tool: "database_query"
        action: "allow"
        conditions:
          max_rate: 100
          data_sensitivity: "low"
      - tool: "*"
        action: "deny"

  - agent: "file-agent"
    rules:
      - tool: "read_file"
        action: "allow"
        conditions:
          max_rate: 50
      - tool: "write_file"
        action: "rate_limit"
        conditions:
          max_rate: 10
          time_window: 60
      - tool: "delete_file"
        action: "deny"`}
        language="yaml"
        filename="policy.yaml"
      />

      {/* Rule Types */}
      <h2>Rule Types</h2>
      <p>Each rule specifies an <code>action</code> that determines what happens when the rule matches:</p>
      <ul>
        <li>
          <strong>allow</strong> — Permits the tool call. Optional conditions can still constrain
          the call (e.g., rate limits).
        </li>
        <li>
          <strong>deny</strong> — Blocks the tool call entirely. The agent receives an access
          denied error.
        </li>
        <li>
          <strong>rate_limit</strong> — Allows the tool call but enforces a maximum invocation rate.
          Calls exceeding the rate are rejected until the window resets.
        </li>
      </ul>
      <p>
        Rules are evaluated top-to-bottom. The first matching rule wins. Use <code>"*"</code> as a
        wildcard tool name for catch-all rules at the end of a policy.
      </p>

      {/* Conditions */}
      <h2>Conditions</h2>
      <p>Conditions add constraints to allow and rate_limit rules:</p>
      <ul>
        <li>
          <strong>max_rate</strong> — Maximum number of calls permitted within the time window.
          Defaults to unlimited if not set.
        </li>
        <li>
          <strong>data_sensitivity</strong> — Required sensitivity level for the data being
          accessed. Values: <code>"low"</code>, <code>"medium"</code>, <code>"high"</code>,{' '}
          <code>"critical"</code>.
        </li>
        <li>
          <strong>time_window</strong> — Duration in seconds for the rate limit window. Defaults to
          60 seconds.
        </li>
      </ul>

      {/* Checking Policies */}
      <h2>Checking Policies</h2>
      <p>
        Use the policy check API endpoint to programmatically verify whether a tool call is
        permitted under the current policy:
      </p>
      <CodeBlock
        code={`curl -X POST http://localhost:8484/api/policy/check \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent": "data-agent",
    "tool": "database_query",
    "context": {
      "data_sensitivity": "low"
    }
  }'`}
        language="bash"
      />
      <p>The response includes the decision, matched rule, and any applicable conditions:</p>
      <CodeBlock
        code={`{
  "allowed": true,
  "rule": {
    "tool": "database_query",
    "action": "allow",
    "conditions": {
      "max_rate": 100,
      "data_sensitivity": "low"
    }
  },
  "remaining_rate": 97
}`}
        language="json"
      />
    </div>
  )
}
