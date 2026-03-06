import { useCallback, useEffect, useState } from 'react'
import { api, type BillingInfo } from '../api'

interface UseBillingResult {
  plan: BillingInfo['plan']
  canUseLLM: boolean
  hasByokKey: boolean
  llmCallCount: number
  loading: boolean
  /** Refresh billing data from server. */
  refresh: () => void
  /** Temporarily toggle plan (no Stripe yet). */
  setPlan: (plan: 'free' | 'pro') => Promise<void>
}

/**
 * Hook that fetches the current user's billing state from `/api/billing/plan`.
 */
export default function useBilling(): UseBillingResult {
  const [info, setInfo] = useState<BillingInfo | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(() => {
    setLoading(true)
    api.getBilling()
      .then(setInfo)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const setPlan = useCallback(async (plan: 'free' | 'pro') => {
    try {
      await api.setPlan(plan)
      refresh()
    } catch { /* ignore */ }
  }, [refresh])

  return {
    plan: info?.plan ?? 'free',
    canUseLLM: info?.can_use_llm ?? false,
    hasByokKey: info?.has_byok_key ?? false,
    llmCallCount: info?.llm_call_count ?? 0,
    loading,
    refresh,
    setPlan,
  }
}
