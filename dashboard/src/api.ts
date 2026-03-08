const BASE = '/api'

// ── Auth token injection ──────────────────────────────────
let _getAuthToken: (() => Promise<string | null>) | null = null

/** Called once by AuthTokenBridge to wire Clerk's getToken into fetch calls. */
export function setAuthTokenFetcher(fn: () => Promise<string | null>) {
  _getAuthToken = fn
}

async function authHeaders(): Promise<Record<string, string>> {
  if (!_getAuthToken) return {}
  try {
    const token = await _getAuthToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
  } catch {
    return {}
  }
}

// ── Error parsing ─────────────────────────────────────────
async function parseError(res: Response, method: string, path: string): Promise<never> {
  let body: Record<string, unknown> | null = null
  try {
    body = await res.json()
  } catch {
    // Response is not JSON (e.g. HTML 404 from proxy) — fall through to generic error
  }
  if (body?.detail) {
    const detail = body.detail as Record<string, unknown>
    if (typeof detail === 'object' && detail?.message) {
      const err = new Error(detail.message as string) as Error & { errorType?: string }
      err.errorType = (detail.error_type as string) || 'unknown'
      throw err
    }
    if (typeof body.detail === 'string') throw new Error(body.detail)
  }
  // Friendly message when backend is unreachable (500 from dev proxy or no backend)
  if (res.status === 500 || res.status === 502 || res.status === 503) {
    throw new Error('Backend not reachable. Run: navil cloud serve')
  }
  throw new Error(`${method} ${path} failed: ${res.status}`)
}

const FETCH_TIMEOUT_MS = 30_000
const LLM_TIMEOUT_MS = 120_000  // LLM calls can be slow (Ollama, large models)

function withTimeout(ms: number): { signal: AbortSignal; clear: () => void } {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), ms)
  return { signal: controller.signal, clear: () => clearTimeout(id) }
}

async function get<T>(path: string): Promise<T> {
  const headers = await authHeaders()
  const timeout = path.startsWith('/llm/') ? LLM_TIMEOUT_MS : FETCH_TIMEOUT_MS
  const { signal, clear } = withTimeout(timeout)
  try {
    const res = await fetch(`${BASE}${path}`, { headers, signal })
    if (!res.ok) return parseError(res, 'GET', path)
    try { return await res.json() } catch { throw new Error(`GET ${path}: invalid JSON response`) }
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error(`GET ${path} timed out after ${timeout / 1000}s`)
    }
    throw e
  } finally {
    clear()
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const auth = await authHeaders()
  const timeout = path.startsWith('/llm/') ? LLM_TIMEOUT_MS : FETCH_TIMEOUT_MS
  const { signal, clear } = withTimeout(timeout)
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...auth },
      body: JSON.stringify(body),
      signal,
    })
    if (!res.ok) return parseError(res, 'POST', path)
    try { return await res.json() } catch { throw new Error(`POST ${path}: invalid JSON response`) }
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error(`POST ${path} timed out after ${timeout / 1000}s`)
    }
    throw e
  } finally {
    clear()
  }
}

async function del<T>(path: string): Promise<T> {
  const headers = await authHeaders()
  const { signal, clear } = withTimeout(FETCH_TIMEOUT_MS)
  try {
    const res = await fetch(`${BASE}${path}`, { method: 'DELETE', headers, signal })
    if (!res.ok) return parseError(res, 'DELETE', path)
    try { return await res.json() } catch { throw new Error(`DELETE ${path}: invalid JSON response`) }
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new Error(`DELETE ${path} timed out after ${FETCH_TIMEOUT_MS / 1000}s`)
    }
    throw e
  } finally {
    clear()
  }
}

// Types
export interface Overview {
  total_agents: number
  total_alerts: number
  critical_alerts: number
  active_credentials: number
  total_credentials: number
  total_invocations: number
  recent_alerts: Alert[]
  agent_health: AgentHealth[]
}

export interface AgentHealth {
  name: string
  status: string
  observations: number
  alert_count: number
}

export interface Alert {
  anomaly_type: string
  severity: string
  agent: string
  description: string
  timestamp: string
  evidence: string[]
  recommended_action: string
  confidence: number
}

export interface Agent {
  name: string
  observations: number
  alert_count: number
  known_tools: string[]
  duration_mean: number
  data_volume_mean: number
}

export interface AgentDetail {
  baseline: Record<string, unknown>
  alerts: Alert[]
  anomaly_scores: AnomalyScore[]
}

export interface AnomalyScore {
  anomaly_type: string
  confidence: number
  level: string
  z_score: number
  should_alert: boolean
  evidence: string[]
}

export interface ScanResult {
  status: string
  security_score: number
  total_vulnerabilities: number
  vulnerabilities_by_level: Record<string, number>
  vulnerabilities: Vulnerability[]
  recommendation: string
}

export interface Vulnerability {
  id: string
  title: string
  description: string
  risk_level: string
  affected_field: string
  remediation: string
}

export interface Credential {
  token_id: string
  agent_name: string
  scope: string
  status: string
  issued_at: string
  expires_at: string
  rotation_count?: number
  last_used?: string | null
  used_count?: number
}

export interface IssuedCredential extends Credential {
  token: string
}

export interface PolicyCheckResult {
  allowed: boolean
  reason: string
}

export interface PolicyDecision {
  decision: string
  rule: string
  reason: string
  severity: string
  agent: string
  tool: string
  action: string
  timestamp: string
}

export interface FeedbackStats {
  total_entries: number
  by_anomaly_type: Record<string, { confirmed: number; dismissed: number; escalated: number }>
}

// LLM Feature Types
export interface LLMConfig {
  available: boolean
  api_key_set: boolean
  provider: string
  model: string
  base_url: string
}

export type LLMStatus = LLMConfig

export interface AnomalyExplanation {
  explanation: string
  likely_threat: boolean
  recommended_actions: string[]
  analysis?: string
}

export interface ConfigAnalysis {
  explanation: string
  risks: string[]
  remediations: string[]
  severity: string
  confidence?: number
}

export interface GeneratedPolicy {
  policy: Record<string, unknown>
  yaml: string
}

export interface RemediationAction {
  type: string
  target: string
  value: unknown
  reason: string
  confidence: number
  reversible: boolean
}

export interface RemediationSuggestion {
  actions: RemediationAction[]
  summary: string
  risk_assessment: string
}

export interface AutoRemediateResult {
  initial_analysis: {
    summary: string
    risk_assessment: string
  }
  auto_applied: RemediationAction[]
  failed_to_apply: RemediationAction[]
  manual_review: RemediationAction[]
  post_status: {
    healthy: boolean
    remaining_alert_count: number
  }
  llm_calls_used: number
}

// Proxy Types
export interface ProxyStatus {
  running: boolean
  target_url: string
  stats: {
    total_requests: number
    blocked: number
    alerts_generated: number
    forwarded: number
  }
  uptime_seconds: number
  traffic_log_size: number
}

export interface TrafficEntry {
  timestamp: string
  agent: string
  method: string
  tool: string
  decision: string
  duration_ms: number
  data_bytes: number
}

// Pentest Types
export interface PentestScenarioResult {
  scenario: string
  description: string
  attack_steps: string[]
  detected: boolean
  alerts_fired: Alert[]
  severity: string
  verdict: string
}

export interface PentestReport {
  status: string
  timestamp?: string
  total_scenarios: number
  passed: number
  failed: number
  partial: number
  detection_rate: number
  results: PentestScenarioResult[]
}

// Analytics Types (Elite)
export interface AgentTrustScore {
  agent_name: string
  score: number
  verdict: string
  components: {
    policy_compliance: number
    anomaly_frequency: number
    data_pattern: number
    behavioral_stability: number
  }
}

export interface BehavioralProfileSummary {
  agent_name: string
  total_events: number
  top_tool: string
  top_tool_pct: number
  avg_duration_ms: number
  total_data_bytes: number
}

export interface TrendPoint {
  label: string
  events: number
  anomalies: number
}

export interface AnalyticsOverview {
  avg_trust_score: number
  agents_monitored: number
  anomaly_rate: number
  total_events_24h: number
  trust_scores: AgentTrustScore[]
  behavioral_profiles: BehavioralProfileSummary[]
  trends: TrendPoint[]
}

// API Key Types (Cloud)
export interface ApiKeyInfo {
  id: number
  key_prefix: string
  name: string
  scopes: string[]
  created_at: string
  last_used_at: string | null
  expires_at: string | null
  revoked: boolean
}

export interface ApiKeyCreated {
  key_id: number
  key_prefix: string
  raw_key: string
  name: string
  scopes: string[]
}

export interface ProxyConnection {
  status: 'connected' | 'stale' | 'disconnected'
  last_heartbeat: string | null
  proxy_version: string | null
  hostname: string | null
}

// Billing Types
export interface BillingInfo {
  plan: 'free' | 'lite' | 'elite'
  llm_call_count: number
  has_byok_key: boolean
  can_use_llm: boolean
  stripe_enabled: boolean
}

// Admin Types
export interface AdminOverview {
  tenant_detectors_active: number
  llm_available: boolean
  llm_provider: string
  llm_model: string
  stripe_enabled: boolean
  proxy_running: boolean
  total_events: number
  total_alerts: number
  total_api_keys: number
  total_tenants: number
  connected_proxies: number
  events_last_hour: number
  alerts_last_hour: number
  critical_alerts_24h: number
  redis_configured: boolean
  scheduler_running: boolean
}

export interface AdminTenant {
  user_id: string
  event_count: number
  alert_count: number
  api_key_count: number
  proxy_status: 'connected' | 'stale' | 'disconnected'
  last_seen: string | null
  plan: string
}

export interface AdminTenantList {
  tenants: AdminTenant[]
  total: number
}

export interface AdminAlert {
  id: number
  user_id: string
  agent_name: string
  anomaly_type: string
  severity: string
  details: string
  created_at: string | null
}

export interface AdminAlertList {
  alerts: AdminAlert[]
  total: number
}

export interface AdminApiKey {
  id: number
  user_id: string
  key_prefix: string
  name: string
  revoked: boolean
  last_used_at: string | null
  created_at: string | null
}

export interface AdminSystem {
  llm: {
    available: boolean
    api_key_set: boolean
    provider: string
    model: string
    base_url: string
  }
  tenant_detectors: { active: number; max_size: number }
  stripe_enabled: boolean
  proxy_running: boolean
  database: { url?: string; status: string; error?: string }
  redis: { status: string; url?: string; used_memory_mb?: number; error?: string }
  scheduler: { status: string }
  environment: {
    clerk_configured: boolean
    stripe_configured: boolean
    resend_configured: boolean
    admin_ids_set: boolean
  }
}

export interface ThroughputPoint {
  hour: string
  count: number
}

export interface AdminThroughput {
  events: ThroughputPoint[]
  alerts: ThroughputPoint[]
}

export interface AdminBilling {
  total_users: number
  plan_distribution: Record<string, number>
  stripe_enabled: boolean
}

// API calls
export const api = {
  getOverview: () => get<Overview>('/overview'),
  getAgents: () => get<Agent[]>('/agents'),
  getAgent: (name: string) => get<AgentDetail>(`/agents/${name}`),
  getAlerts: (severity?: string, agent?: string) => {
    const params = new URLSearchParams()
    if (severity) params.set('severity', severity)
    if (agent) params.set('agent', agent)
    const qs = params.toString()
    return get<Alert[]>(`/alerts${qs ? '?' + qs : ''}`)
  },
  scan: (config: object) => post<ScanResult>('/scan', { config }),
  getCredentials: () => get<Credential[]>('/credentials'),
  issueCredential: (agent_name: string, scope: string, ttl_seconds = 3600) =>
    post<IssuedCredential>('/credentials', { agent_name, scope, ttl_seconds }),
  revokeCredential: (id: string) => del<{ status: string }>(`/credentials/${id}`),
  checkPolicy: (agent_name: string, tool_name: string, action: string) =>
    post<PolicyCheckResult>('/policy/check', { agent_name, tool_name, action }),
  getPolicyDecisions: () => get<PolicyDecision[]>('/policy/decisions'),
  submitFeedback: (data: {
    alert_timestamp: string; anomaly_type: string; agent_name: string;
    verdict: string; operator_notes?: string
  }) => post<{ status: string }>('/feedback', data),
  getFeedbackStats: () => get<FeedbackStats>('/feedback/stats'),

  // LLM endpoints
  getLLMStatus: () => get<LLMStatus>('/llm/status'),
  explainAnomaly: (alert: Alert) =>
    post<AnomalyExplanation>('/llm/explain-anomaly', { anomaly_data: alert }),
  analyzeConfig: (config: object) =>
    post<ConfigAnalysis>('/llm/analyze-config', { config }),
  generatePolicy: (description: string) =>
    post<GeneratedPolicy>('/llm/generate-policy', { description }),
  refinePolicy: (policy: Record<string, unknown>, instruction: string) =>
    post<GeneratedPolicy>('/llm/refine-policy', { existing_policy: policy, instruction }),
  suggestRemediation: () =>
    post<RemediationSuggestion>('/llm/suggest-remediation', {}),
  applyAction: (action: RemediationAction) =>
    post<{ success: boolean; action: RemediationAction }>('/llm/apply-action', { action }),
  autoRemediate: (confidenceThreshold = 0.9) =>
    post<AutoRemediateResult>('/llm/auto-remediate', { confidence_threshold: confidenceThreshold }),

  // Settings endpoints
  getLLMSettings: () => get<LLMConfig>('/settings/llm'),
  updateLLMSettings: (provider: string, api_key: string, base_url = '', model = '') =>
    post<LLMConfig>('/settings/llm', { provider, api_key, base_url, model }),
  testLLMConnection: (provider = '', api_key = '', base_url = '', model = '') =>
    post<{ success: boolean; response_preview?: string; error?: string }>('/settings/llm/test', { provider, api_key, base_url, model }),

  // Pentest endpoints
  pentest: (scenario?: string) =>
    post<PentestReport>('/pentest', { scenario: scenario || null }),

  // Proxy endpoints
  proxyStatus: () => get<ProxyStatus>('/proxy/status'),
  proxyTraffic: (agent?: string, blockedOnly = false) => {
    const params = new URLSearchParams()
    if (agent) params.set('agent', agent)
    if (blockedOnly) params.set('blocked_only', 'true')
    const qs = params.toString()
    return get<TrafficEntry[]>(`/proxy/traffic${qs ? '?' + qs : ''}`)
  },
  proxyStart: (target_url: string, port = 9090, require_auth = true) =>
    post<{ status: string; target_url: string; port: number }>('/proxy/start', { target_url, port, require_auth }),

  // Analytics endpoints (Elite)
  getAnalyticsOverview: () => get<AnalyticsOverview>('/analytics/overview'),

  // API Key endpoints (Cloud)
  listApiKeys: () => get<ApiKeyInfo[]>('/api-keys'),
  createApiKey: (name: string, scopes: string[] = ['ingest']) =>
    post<ApiKeyCreated>('/api-keys', { name, scopes }),
  revokeApiKey: (keyId: number) => del<{ status: string }>(`/api-keys/${keyId}`),
  getProxyConnection: () => get<ProxyConnection>('/proxy/connection'),

  // Billing endpoints
  getBilling: () => get<BillingInfo>('/billing/plan'),
  setPlan: (plan: string) =>
    post<{ plan: string; status: string }>('/billing/plan', { plan }),
  createCheckout: (data: { success_url: string; cancel_url: string }) =>
    post<{ checkout_url: string }>('/billing/checkout', data),
  createPortal: () =>
    post<{ portal_url: string }>('/billing/portal', {}),

  // Admin endpoints
  adminOverview: () => get<AdminOverview>('/admin/overview'),
  adminTenants: (limit = 50, offset = 0, search = '') => {
    const params = new URLSearchParams()
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    if (search) params.set('search', search)
    return get<AdminTenantList>(`/admin/tenants?${params}`)
  },
  adminTenantDetail: (userId: string) =>
    get<Record<string, unknown>>(`/admin/tenants/${encodeURIComponent(userId)}`),
  adminAlerts: (severity?: string, limit = 100, offset = 0) => {
    const params = new URLSearchParams()
    if (severity) params.set('severity', severity)
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return get<AdminAlertList>(`/admin/alerts?${params}`)
  },
  adminApiKeys: (limit = 100, offset = 0) => {
    const params = new URLSearchParams()
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return get<{ keys: AdminApiKey[]; total: number }>(`/admin/api-keys?${params}`)
  },
  adminRevokeApiKey: (keyId: number) =>
    del<{ status: string }>(`/admin/api-keys/${keyId}`),
  adminSystem: () => get<AdminSystem>('/admin/system'),
  adminThroughput: (hours = 24) =>
    get<AdminThroughput>(`/admin/throughput?hours=${hours}`),
  adminBilling: () => get<AdminBilling>('/admin/billing'),
}
