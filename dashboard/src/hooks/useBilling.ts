import { useCallback, useEffect, useState } from 'react'
import { api, type BillingInfo } from '../api'

export type PlanType = BillingInfo['plan']

interface UseBillingResult {
  plan: PlanType
  canUseLLM: boolean
  hasByokKey: boolean
  llmCallCount: number
  stripeEnabled: boolean
  loading: boolean
  /** Refresh billing data from server. */
  refresh: () => void
  /** Temporarily toggle plan (in-memory only — ignored when Stripe is active). */
  setPlan: (plan: PlanType) => Promise<void>
  /** Redirect to Stripe Checkout for a specific plan. */
  checkout: (plan?: 'lite' | 'elite') => Promise<void>
  /** Redirect to Stripe Customer Portal. */
  portal: () => Promise<void>
}

/**
 * Hook that fetches the current user's billing state from `/api/billing/plan`.
 */
export default function useBilling(): UseBillingResult {
  const [info, setInfo] = useState<BillingInfo | null>(null)
  const [loading, setLoading] = useState(true)

  // Client-side override persisted in sessionStorage when backend is unreachable
  const [localPlan, setLocalPlan] = useState<PlanType | null>(() => {
    const stored = sessionStorage.getItem('navil_demo_plan')
    return stored ? (stored as PlanType) : null
  })

  const refresh = useCallback(() => {
    setLoading(true)
    api.getBilling()
      .then((data) => {
        setInfo(data)
        setLocalPlan(null)
        sessionStorage.removeItem('navil_demo_plan')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const setPlan = useCallback(async (plan: PlanType) => {
    try {
      await api.setPlan(plan)
      refresh()
    } catch {
      // Backend unreachable — persist client-side override for demo
      setLocalPlan(plan)
      sessionStorage.setItem('navil_demo_plan', plan)
    }
  }, [refresh])

  const checkout = useCallback(async (_plan: 'lite' | 'elite' = 'lite') => {
    try {
      const res = await api.createCheckout({
        success_url: `${window.location.origin}/dashboard/settings?checkout=success`,
        cancel_url: `${window.location.origin}/dashboard/settings`,
      })
      window.location.href = res.checkout_url
    } catch {
      // Stripe not configured — fall back to settings
      window.location.href = '/dashboard/settings'
    }
  }, [])

  const portal = useCallback(async () => {
    try {
      const res = await api.createPortal()
      window.location.href = res.portal_url
    } catch { /* ignore */ }
  }, [])

  return {
    plan: localPlan ?? info?.plan ?? 'free',
    canUseLLM: localPlan ? localPlan !== 'free' : (info?.can_use_llm ?? false),
    hasByokKey: info?.has_byok_key ?? false,
    llmCallCount: info?.llm_call_count ?? 0,
    stripeEnabled: info?.stripe_enabled ?? false,
    loading,
    refresh,
    setPlan,
    checkout,
    portal,
  }
}
