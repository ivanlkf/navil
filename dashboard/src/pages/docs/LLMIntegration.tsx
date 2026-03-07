import CodeBlock from '../../components/CodeBlock'

export default function LLMIntegration() {
  return (
    <div className="docs-prose animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-2">LLM Integration</h1>

      <p>
        Navil uses large language models to provide AI-powered security analysis, including anomaly
        explanation, configuration review, automatic policy generation, and threat remediation. All
        LLM features support Bring Your Own Key (BYOK) so you stay in control of costs and data.
      </p>

      {/* Supported Providers */}
      <h2>Supported Providers</h2>
      <p>Navil works with a wide range of LLM providers out of the box:</p>
      <ul>
        <li>
          <strong>Anthropic</strong> — Claude models (claude-sonnet-4-20250514, etc.)
        </li>
        <li>
          <strong>OpenAI</strong> — GPT-4o, GPT-4o-mini, and other OpenAI models
        </li>
        <li>
          <strong>Google Gemini</strong> — Gemini Pro and Gemini Flash models
        </li>
        <li>
          <strong>Ollama</strong> — Run local models with no API key required
        </li>
        <li>
          <strong>OpenAI-compatible</strong> — Any provider that implements the OpenAI API format,
          including OpenRouter, Together AI, Groq, and others
        </li>
      </ul>

      {/* Configuration */}
      <h2>Configuration</h2>
      <p>
        Configure your LLM provider through the dashboard Settings page or via environment
        variables:
      </p>

      <h3>Environment Variables</h3>
      <CodeBlock
        code={`# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
OPENAI_API_KEY=sk-...

# Google Gemini
GEMINI_API_KEY=AIza...`}
        language="bash"
        filename=".env"
      />

      <h3>API Configuration</h3>
      <p>You can also configure the LLM provider at runtime through the settings API:</p>
      <CodeBlock
        code={`curl -X POST http://localhost:8484/api/settings/llm \\
  -H "Content-Type: application/json" \\
  -d '{
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "apiKey": "sk-ant-..."
  }'`}
        language="bash"
      />

      <p>
        Test your configuration with the test endpoint to verify connectivity before relying on
        LLM features:
      </p>
      <CodeBlock
        code={`curl -X POST http://localhost:8484/api/settings/llm/test`}
        language="bash"
      />

      {/* AI Features */}
      <h2>AI Features</h2>
      <p>Once configured, the following AI-powered features become available:</p>

      <h3>Anomaly Explanation</h3>
      <p>
        When the anomaly detection system flags suspicious behavior, the LLM analyzes the event
        context and produces a human-readable explanation of what happened, why it was flagged, and
        how severe it is.
      </p>

      <h3>Config Analysis</h3>
      <p>
        Submit an MCP configuration for AI-powered review. The LLM identifies security risks,
        misconfigurations, and best-practice violations that static analysis might miss.
      </p>

      <h3>Policy Generation</h3>
      <p>
        Describe your security requirements in natural language and the LLM generates a
        complete YAML policy file. This accelerates policy creation and ensures best practices
        are followed.
      </p>

      <h3>Auto-Remediation</h3>
      <p>
        For detected threats and vulnerabilities, the LLM can suggest specific remediation steps
        or automatically apply fixes when enabled. Auto-remediation actions are logged and can be
        reviewed in the dashboard.
      </p>

      {/* BYOK */}
      <h2>BYOK (Bring Your Own Key)</h2>
      <p>
        All LLM features operate on a BYOK model. Users configure their own API key through the
        dashboard Settings page or environment variables. This means:
      </p>
      <ul>
        <li>You control costs — usage is billed directly to your LLM provider account.</li>
        <li>You control data — prompts and responses stay between Navil and your chosen provider.</li>
        <li>You choose the model — pick the provider and model that best fits your needs.</li>
        <li>No vendor lock-in — switch providers at any time through settings.</li>
      </ul>
      <p>
        API keys are encrypted at rest and never logged. You can manage your key in the{' '}
        <strong>Settings</strong> page of the dashboard.
      </p>
    </div>
  )
}
