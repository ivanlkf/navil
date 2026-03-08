# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""REST API endpoints for the Navil Cloud dashboard."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from navil.cloud.state import AppState

router = APIRouter(prefix="/api")

_logger = logging.getLogger(__name__)


def _require_llm(s: AppState) -> None:
    """Raise HTTPException if LLM features are not available."""
    if not s.llm_available:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "llm_not_available",
                "message": "LLM features require navil[llm]. Install with: pip install navil[llm]",
                "error_type": "auth",
            },
        )


def _call_llm(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Call an LLM function, converting auth/runtime errors to HTTPException."""
    try:
        return fn(*args, **kwargs)
    except TypeError as e:
        err = str(e)
        if "api_key" in err or "authentication" in err.lower() or "auth_token" in err:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "llm_auth_error",
                    "message": "API key not configured or invalid. Configure in Settings.",
                    "error_type": "auth",
                },
            ) from e
        raise HTTPException(
            status_code=500,
            detail={"error": "llm_error", "message": err, "error_type": "unknown"},
        ) from e
    except Exception as e:
        err_str = str(e)
        err_lower = err_str.lower()
        error_type = "unknown"
        status = 500
        message = err_str

        if "429" in err_str or ("rate" in err_lower and "limit" in err_lower):
            error_type = "rate_limit"
            status = 429
            message = "Rate limit exceeded. Please wait a moment and try again."
        elif (
            "quota" in err_lower
            or "billing" in err_lower
            or "exceeded" in err_lower
            and "limit" in err_lower
        ):
            error_type = "quota"
            status = 503
            message = "API quota exceeded. Check your provider account or wait for quota reset."
        elif "auth" in err_lower or "api_key" in err_lower or "401" in err_str or "403" in err_str:
            error_type = "auth"
            status = 503
            message = "API key is invalid or expired. Check your key in Settings."

        _logger.error(f"LLM call failed ({error_type}): {e}")
        raise HTTPException(
            status_code=status,
            detail={"error": "llm_error", "message": message, "error_type": error_type},
        ) from e


# ── Request / Response Models ───────────────────────────────


class ScanRequest(BaseModel):
    config: dict[str, Any]


class InvocationRequest(BaseModel):
    agent_name: str
    tool_name: str
    action: str
    duration_ms: int
    data_accessed_bytes: int = 0
    success: bool = True


class CredentialIssueRequest(BaseModel):
    agent_name: str
    scope: str
    ttl_seconds: int = 3600


class PolicyCheckRequest(BaseModel):
    agent_name: str
    tool_name: str
    action: str


class FeedbackRequest(BaseModel):
    alert_timestamp: str
    anomaly_type: str
    agent_name: str
    verdict: str
    operator_notes: str = ""


class ExplainAnomalyRequest(BaseModel):
    anomaly_data: dict[str, Any]


class AnalyzeConfigRequest(BaseModel):
    config: dict[str, Any]


class GeneratePolicyRequest(BaseModel):
    description: str


class RefinePolicyRequest(BaseModel):
    existing_policy: dict[str, Any]
    instruction: str


class ApplyActionRequest(BaseModel):
    action: dict[str, Any]


class AutoRemediateRequest(BaseModel):
    confidence_threshold: float = 0.9


class LLMConfigRequest(BaseModel):
    provider: str
    api_key: str
    base_url: str = ""
    model: str = ""


class SetPlanRequest(BaseModel):
    plan: str


def _get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by Clerk middleware) or default."""
    return getattr(request.state, "user_id", "anonymous")


def _require_pro_or_byok(request: Request) -> None:
    """Raise 403 if user is free-tier without a BYOK key configured."""
    s = AppState.get()
    user_id = _get_user_id(request)
    has_byok = s.llm_api_key_configured
    if not s.billing.can_use_llm(user_id, has_byok):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "message": "AI features require a Pro plan or your own API key (BYOK).",
                "error_type": "billing",
            },
        )


# ── Overview ────────────────────────────────────────────────


@router.get("/overview")
def get_overview() -> dict[str, Any]:
    s = AppState.get()
    alerts = s.anomaly_detector.get_alerts()
    agents = list(s.anomaly_detector.adaptive_baselines.keys())
    creds = s.credential_manager.list_credentials()
    active_creds = [c for c in creds if c.get("status") == "ACTIVE"]

    # Per-agent health summary
    agent_health = []
    for agent in agents:
        agent_alerts = [a for a in alerts if a.get("agent") == agent]
        max_sev = "OK"
        for a in agent_alerts:
            sev = a.get("severity", "LOW")
            if sev == "CRITICAL":
                max_sev = "CRITICAL"
                break
            elif sev == "HIGH" and max_sev not in ("CRITICAL",):
                max_sev = "HIGH"
            elif sev == "MEDIUM" and max_sev not in ("CRITICAL", "HIGH"):
                max_sev = "MEDIUM"
            elif sev == "LOW" and max_sev == "OK":
                max_sev = "LOW"
        bl = s.anomaly_detector.adaptive_baselines.get(agent)
        agent_health.append(
            {
                "name": agent,
                "status": max_sev,
                "observations": bl.duration_ema.count if bl else 0,
                "alert_count": len(agent_alerts),
            }
        )

    return {
        "total_agents": len(agents),
        "total_alerts": len(alerts),
        "critical_alerts": len([a for a in alerts if a.get("severity") == "CRITICAL"]),
        "active_credentials": len(active_creds),
        "total_credentials": len(creds),
        "total_invocations": len(s.anomaly_detector.invocations),
        "recent_alerts": alerts[-10:][::-1],
        "agent_health": agent_health,
    }


# ── Scanner ─────────────────────────────────────────────────


@router.post("/scan")
def scan_config(req: ScanRequest) -> dict[str, Any]:
    s = AppState.get()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(req.config, f)
        tmp_path = f.name
    try:
        result = s.scanner.scan(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return result


# ── Agents ──────────────────────────────────────────────────


@router.get("/agents")
def list_agents() -> list[dict[str, Any]]:
    s = AppState.get()
    alerts = s.anomaly_detector.get_alerts()
    result = []
    for name, bl in s.anomaly_detector.adaptive_baselines.items():
        agent_alerts = [a for a in alerts if a.get("agent") == name]
        result.append(
            {
                "name": name,
                "observations": bl.duration_ema.count,
                "alert_count": len(agent_alerts),
                "known_tools": list(bl.known_tools),
                "duration_mean": round(bl.duration_ema.mean, 1),
                "data_volume_mean": round(bl.data_volume_ema.mean, 1),
            }
        )
    return result


@router.get("/agents/{name}")
def get_agent_detail(name: str) -> dict[str, Any]:
    s = AppState.get()
    baseline = s.anomaly_detector.get_adaptive_baseline(name)
    alerts = s.anomaly_detector.get_alerts(agent_name=name)
    scores = s.anomaly_detector.score_anomaly(name)
    return {
        "baseline": baseline,
        "alerts": alerts,
        "anomaly_scores": scores,
    }


# ── Alerts ──────────────────────────────────────────────────


@router.get("/alerts")
def list_alerts(severity: str | None = None, agent: str | None = None) -> list[dict[str, Any]]:
    s = AppState.get()
    alerts = s.anomaly_detector.get_alerts(agent_name=agent, severity=severity)
    return alerts[::-1]


# ── Invocations ─────────────────────────────────────────────


@router.post("/invocations")
def record_invocation(req: InvocationRequest) -> dict[str, str]:
    s = AppState.get()
    s.anomaly_detector.record_invocation(
        agent_name=req.agent_name,
        tool_name=req.tool_name,
        action=req.action,
        duration_ms=req.duration_ms,
        data_accessed_bytes=req.data_accessed_bytes,
        success=req.success,
    )
    return {"status": "recorded"}


# ── Credentials ─────────────────────────────────────────────


@router.get("/credentials")
def list_credentials(agent: str | None = None) -> list[dict[str, Any]]:
    s = AppState.get()
    return s.credential_manager.list_credentials(agent_name=agent)


@router.post("/credentials")
def issue_credential(req: CredentialIssueRequest) -> dict[str, Any]:
    s = AppState.get()
    return s.credential_manager.issue_credential(
        agent_name=req.agent_name,
        scope=req.scope,
        ttl_seconds=req.ttl_seconds,
    )


@router.delete("/credentials/{token_id}")
def revoke_credential(token_id: str) -> dict[str, str]:
    s = AppState.get()
    try:
        s.credential_manager.revoke_credential(token_id, reason="Dashboard revocation")
        return {"status": "revoked"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ── Policy ──────────────────────────────────────────────────


@router.post("/policy/check")
def check_policy(req: PolicyCheckRequest) -> dict[str, Any]:
    s = AppState.get()
    allowed, reason = s.policy_engine.check_tool_call(
        agent_name=req.agent_name,
        tool_name=req.tool_name,
        action=req.action,
    )
    return {"allowed": allowed, "reason": reason}


@router.get("/policy/decisions")
def get_decisions() -> list[dict[str, Any]]:
    s = AppState.get()
    return s.policy_engine.get_decisions_log()[-50:][::-1]


# ── Feedback ────────────────────────────────────────────────


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest) -> dict[str, str]:
    s = AppState.get()
    s.feedback_loop.submit_feedback(
        alert_timestamp=req.alert_timestamp,
        anomaly_type=req.anomaly_type,
        agent_name=req.agent_name,
        verdict=req.verdict,  # type: ignore[arg-type]
        operator_notes=req.operator_notes,
    )
    return {"status": "recorded"}


@router.get("/feedback/stats")
def get_feedback_stats() -> dict[str, Any]:
    s = AppState.get()
    return s.feedback_loop.get_stats()


# ── Settings ───────────────────────────────────────────────


@router.get("/settings/llm")
def get_llm_settings() -> dict[str, Any]:
    return AppState.get().get_llm_config()


@router.post("/settings/llm")
def update_llm_settings(req: LLMConfigRequest) -> dict[str, Any]:
    s = AppState.get()
    valid_providers = ("anthropic", "openai", "gemini", "openai_compatible", "ollama")
    if req.provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_provider",
                "message": f"Provider must be one of: {', '.join(valid_providers)}",
            },
        )
    if req.provider == "openai_compatible" and not req.base_url:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_base_url",
                "message": "Base URL is required for OpenAI-compatible providers.",
            },
        )
    # Ollama doesn't require an API key — use a placeholder
    api_key = req.api_key if req.provider != "ollama" else (req.api_key or "ollama")
    try:
        s.configure_llm(
            req.provider,
            api_key,
            base_url=req.base_url or None,
            model=req.model or None,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=501,
            detail={"error": "llm_not_available", "message": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "llm_config_error", "message": f"Failed to configure: {e}"},
        ) from e
    return s.get_llm_config()


class LLMTestRequest(BaseModel):
    provider: str = ""
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@router.post("/settings/llm/test")
def test_llm_connection(req: LLMTestRequest) -> dict[str, Any]:
    """Test LLM connection using the provided form values (unsaved).

    When form values are supplied, a temporary client is created to test them
    without changing the saved configuration.  If no provider is given, the
    already-saved configuration is tested instead.
    """
    from navil.llm.client import LLMClient

    s = AppState.get()
    _require_llm(s)

    if req.provider:
        # ── Test with the *unsaved* form values ──
        api_key = req.api_key if req.provider != "ollama" else (req.api_key or "ollama")
        try:
            client = LLMClient(
                provider=req.provider,
                api_key=api_key or None,
                base_url=req.base_url or None,
                model=req.model or None,
            )
        except Exception as e:
            return {"success": False, "error": f"Configuration error: {e}"}
    else:
        # ── Fallback: test the saved config ──
        if not s.llm_api_key_configured:
            return {"success": False, "error": "No API key configured."}
        client = s.llm_analyzer.client

    try:
        result = client.complete(
            "You are a connection test. Respond with exactly: OK",
            "Test.",
        )
        return {"success": True, "response_preview": result[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Billing ────────────────────────────────────────────────


@router.get("/billing/plan")
def get_user_plan(request: Request) -> dict[str, Any]:
    user_id = _get_user_id(request)
    s = AppState.get()
    has_byok = s.llm_api_key_configured
    result: dict[str, Any] = {
        "plan": "free",
        "llm_call_count": 0,
        "has_byok_key": has_byok,
        "can_use_llm": False,
        "stripe_enabled": s.stripe_enabled,
    }
    if s.stripe_enabled:
        status = s.billing.get_subscription_status(user_id)  # type: ignore[attr-defined]
        result["plan"] = status.plan
        result["can_use_llm"] = s.billing.can_use_llm(user_id, has_byok)
    else:
        billing = s.billing.get_billing(user_id)  # type: ignore[attr-defined]
        result["plan"] = billing.plan
        result["llm_call_count"] = billing.llm_call_count
        result["can_use_llm"] = s.billing.can_use_llm(user_id, has_byok)
    return result


@router.post("/billing/plan")
def set_user_plan(req: SetPlanRequest, request: Request) -> dict[str, Any]:
    user_id = _get_user_id(request)
    s = AppState.get()
    if req.plan not in ("free", "lite", "elite"):
        raise HTTPException(status_code=400, detail="Plan must be 'free', 'lite', or 'elite'")
    if s.stripe_enabled:
        raise HTTPException(
            status_code=400,
            detail="Use Stripe checkout to change plan",
        )
    s.billing.set_plan(user_id, req.plan)  # type: ignore[arg-type]
    return {"plan": req.plan, "status": "updated"}


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


@router.post("/billing/checkout")
def create_checkout(req: CheckoutRequest, request: Request) -> dict[str, Any]:
    """Create a Stripe Checkout Session for the Pro plan."""
    s = AppState.get()
    if not s.stripe_enabled:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    user_id = _get_user_id(request)
    email = getattr(request.state, "user_email", "")
    url = s.billing.create_checkout_session(  # type: ignore[attr-defined]
        user_id,
        req.success_url,
        req.cancel_url,
        email,
    )
    return {"checkout_url": url}


@router.post("/billing/portal")
def create_portal(request: Request) -> dict[str, Any]:
    """Create a Stripe Customer Portal session."""
    s = AppState.get()
    if not s.stripe_enabled:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    user_id = _get_user_id(request)
    return_url = request.headers.get("referer", "/")
    url = s.billing.create_portal_session(  # type: ignore[attr-defined]
        user_id,
        return_url,
    )
    return {"portal_url": url}


@router.post("/billing/webhook")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    """Handle Stripe webhook events."""
    s = AppState.get()
    if not s.stripe_enabled:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        return s.billing.handle_webhook(payload, sig)  # type: ignore[attr-defined]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── LLM-Powered Features ──────────────────────────────────


@router.get("/llm/status")
def llm_status() -> dict[str, Any]:
    return AppState.get().get_llm_config()


@router.post("/llm/explain-anomaly")
def explain_anomaly(req: ExplainAnomalyRequest, request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    result = _call_llm(s.llm_analyzer.explain_anomaly, req.anomaly_data)
    s.billing.increment_llm_calls(_get_user_id(request))
    return result


@router.post("/llm/analyze-config")
def analyze_config_llm(req: AnalyzeConfigRequest, request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    result = _call_llm(s.llm_analyzer.analyze_config, req.config)
    s.billing.increment_llm_calls(_get_user_id(request))
    return result


@router.post("/llm/generate-policy")
def generate_policy(req: GeneratePolicyRequest, request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    policy = _call_llm(s.policy_generator.generate, req.description)
    s.billing.increment_llm_calls(_get_user_id(request))
    return {
        "policy": policy,
        "yaml": yaml.dump(policy, default_flow_style=False),
    }


@router.post("/llm/refine-policy")
def refine_policy(req: RefinePolicyRequest, request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    policy = _call_llm(s.policy_generator.refine, req.existing_policy, req.instruction)
    s.billing.increment_llm_calls(_get_user_id(request))
    return {
        "policy": policy,
        "yaml": yaml.dump(policy, default_flow_style=False),
    }


@router.post("/llm/suggest-remediation")
def suggest_remediation(request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    alerts = s.anomaly_detector.get_alerts()
    if not alerts:
        return {
            "summary": "No active threats detected. The system is healthy.",
            "risk_assessment": "LOW",
            "actions": [],
        }
    critical = [a for a in alerts if a.get("severity") in ("CRITICAL", "HIGH")]
    selected = critical[-10:] if critical else alerts[-10:]
    current_policy = getattr(s.policy_engine, "policy", {})
    baselines: dict[str, Any] = {}
    for name, bl in s.anomaly_detector.adaptive_baselines.items():
        baselines[name] = {
            "duration_mean": bl.duration_ema.mean,
            "data_volume_mean": bl.data_volume_ema.mean,
            "known_tools": list(bl.known_tools),
        }
    result = _call_llm(s.self_healing.suggest_remediation, selected, current_policy, baselines)
    s.billing.increment_llm_calls(_get_user_id(request))
    return result


@router.post("/llm/apply-action")
def apply_action(req: ApplyActionRequest, request: Request) -> dict[str, Any]:
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)
    success = _call_llm(
        s.self_healing.apply_action, req.action, s.policy_engine, s.anomaly_detector
    )
    s.billing.increment_llm_calls(_get_user_id(request))
    return {"success": success, "action": req.action}


@router.post("/llm/auto-remediate")
def auto_remediate(req: AutoRemediateRequest, request: Request) -> dict[str, Any]:
    """Full auto-remediation cycle: analyze, auto-apply safe actions, verify."""
    s = AppState.get()
    _require_llm(s)
    _require_pro_or_byok(request)

    user_id = _get_user_id(request)

    alerts = s.anomaly_detector.get_alerts()
    if not alerts:
        return {
            "initial_analysis": {
                "summary": "No active threats detected. The system is healthy.",
                "risk_assessment": "LOW",
            },
            "auto_applied": [],
            "failed_to_apply": [],
            "manual_review": [],
            "post_status": {"healthy": True, "remaining_alert_count": 0},
            "llm_calls_used": 0,
        }

    critical = [a for a in alerts if a.get("severity") in ("CRITICAL", "HIGH")]
    selected = critical[-10:] if critical else alerts[-10:]
    current_policy = getattr(s.policy_engine, "policy", {})
    baselines: dict[str, Any] = {}
    for name, bl in s.anomaly_detector.adaptive_baselines.items():
        baselines[name] = {
            "duration_mean": bl.duration_ema.mean,
            "data_volume_mean": bl.data_volume_ema.mean,
            "known_tools": list(bl.known_tools),
        }

    result = _call_llm(
        s.self_healing.full_auto_remediate,
        selected,
        current_policy,
        baselines,
        s.policy_engine,
        s.anomaly_detector,
        req.confidence_threshold,
    )

    llm_calls = result.get("llm_calls_used", 1)
    for _ in range(llm_calls):
        s.billing.increment_llm_calls(user_id)

    return result


# ── Analytics (Elite) ──────────────────────────────────────


def _require_elite(request: Request) -> None:
    """Raise 403 if user is not on the Elite plan."""
    s = AppState.get()
    user_id = _get_user_id(request)
    if s.stripe_enabled:
        status = s.billing.get_subscription_status(user_id)  # type: ignore[attr-defined]
        plan = status.plan
    else:
        plan = s.billing.get_billing(user_id).plan  # type: ignore[attr-defined]
    if plan != "elite":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "elite_required",
                "message": "Analytics features require an Elite plan.",
                "error_type": "billing",
            },
        )


def _hours_ago(timestamp_str: str, now: Any) -> int:
    """Return how many hours ago a timestamp was (0-23, clamped)."""
    import datetime as dt

    try:
        ts = dt.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).replace(tzinfo=None)
        delta = (now - ts).total_seconds() / 3600
        return max(0, min(23, int(delta)))
    except (ValueError, AttributeError):
        return 12


@router.get("/analytics/overview")
def analytics_overview(request: Request) -> dict[str, Any]:
    """Return aggregated analytics data for the Elite dashboard."""
    _require_elite(request)
    s = AppState.get()
    alerts = s.anomaly_detector.get_alerts()
    agents = list(s.anomaly_detector.adaptive_baselines.keys())
    invocations = s.anomaly_detector.invocations

    # Compute trust scores from in-memory data
    trust_scores = []
    for name in agents:
        bl = s.anomaly_detector.adaptive_baselines.get(name)
        if not bl:
            continue
        agent_alerts = [a for a in alerts if a.get("agent") == name]
        obs = bl.duration_ema.count
        alert_rate = len(agent_alerts) / max(obs, 1)

        policy_compliance = min(100.0, max(0.0, (1.0 - alert_rate * 2) * 100))
        anomaly_frequency = max(0.0, 100.0 - alert_rate * 500)
        dur_cv = (bl.duration_ema.variance**0.5) / max(bl.duration_ema.mean, 1)
        behavioral_stability = max(0.0, 100.0 - dur_cv * 50)
        data_pattern = 75.0

        score = (
            policy_compliance * 0.30
            + anomaly_frequency * 0.25
            + data_pattern * 0.20
            + behavioral_stability * 0.25
        )
        score = max(0.0, min(100.0, score))

        verdict = "trusted" if score >= 70 else ("moderate" if score >= 40 else "untrusted")

        trust_scores.append(
            {
                "agent_name": name,
                "score": round(score, 1),
                "verdict": verdict,
                "components": {
                    "policy_compliance": round(policy_compliance, 1),
                    "anomaly_frequency": round(anomaly_frequency, 1),
                    "data_pattern": round(data_pattern, 1),
                    "behavioral_stability": round(behavioral_stability, 1),
                },
            }
        )

    # Behavioral profiles
    profiles = []
    for name in agents:
        bl = s.anomaly_detector.adaptive_baselines.get(name)
        if not bl:
            continue
        tools = list(bl.known_tools)
        agent_invocations = [inv for inv in invocations if inv.agent_name == name]
        total = len(agent_invocations)
        tool_counts: dict[str, int] = {}
        total_bytes = 0
        for inv in agent_invocations:
            t = inv.tool_name or "unknown"
            tool_counts[t] = tool_counts.get(t, 0) + 1
            total_bytes += inv.data_accessed_bytes

        top_tool = (
            max(tool_counts, key=tool_counts.get)  # type: ignore[arg-type]
            if tool_counts
            else (tools[0] if tools else "unknown")
        )
        top_pct = round((tool_counts.get(top_tool, 0) / max(total, 1)) * 100, 1)

        profiles.append(
            {
                "agent_name": name,
                "total_events": total or bl.duration_ema.count,
                "top_tool": top_tool,
                "top_tool_pct": top_pct if total else 50.0,
                "avg_duration_ms": round(bl.duration_ema.mean, 0),
                "total_data_bytes": total_bytes
                or int(bl.data_volume_ema.mean * bl.duration_ema.count),
            }
        )

    # Hourly trend buckets
    import datetime as dt

    now = dt.datetime.utcnow()
    trends = []
    for h in range(24):
        label = f"{23 - h}h"
        bucket_alerts = len(
            [
                a
                for a in alerts
                if a.get("timestamp") and _hours_ago(a["timestamp"], now) == (23 - h)
            ]
        )
        trends.append(
            {
                "label": label,
                "events": max(len(invocations) // 24, 10) + (h % 5) * 3,
                "anomalies": bucket_alerts,
            }
        )

    avg_score = sum(t["score"] for t in trust_scores) / max(len(trust_scores), 1)
    total_alerts = len(alerts)
    _profile_events = [p["total_events"] for p in profiles]
    total_events = len(invocations) or int(sum(_profile_events))  # type: ignore[arg-type]
    anomaly_rate = total_alerts / max(total_events, 1)

    return {
        "avg_trust_score": round(avg_score, 1),
        "agents_monitored": len(agents),
        "anomaly_rate": round(anomaly_rate, 4),
        "total_events_24h": total_events,
        "trust_scores": trust_scores,
        "behavioral_profiles": profiles,
        "trends": trends,
    }


# ── Pentest ────────────────────────────────────────────────


class PentestRequest(BaseModel):
    scenario: str | None = None  # None = run all scenarios


@router.post("/pentest")
def run_pentest(req: PentestRequest) -> dict[str, Any]:
    """Run SAFE-MCP attack simulations against the anomaly detectors."""
    from navil.pentest import PentestEngine

    s = AppState.get()
    engine = PentestEngine(s.anomaly_detector, s.policy_engine)

    if req.scenario:
        result = engine.run_scenario(req.scenario)
        return {
            "status": "completed",
            "total_scenarios": 1,
            "passed": 1 if result.verdict == "PASS" else 0,
            "failed": 1 if result.verdict == "FAIL" else 0,
            "partial": 1 if result.verdict == "PARTIAL" else 0,
            "detection_rate": (
                100.0 if result.verdict == "PASS" else 50.0 if result.verdict == "PARTIAL" else 0.0
            ),
            "results": [result.to_dict()],
        }
    return engine.run_all()


# ── Proxy endpoints ──────────────────────────────────────────


@router.get("/proxy/status")
def proxy_status() -> dict[str, Any]:
    """Get MCP proxy status."""
    s = AppState.get()
    if s.proxy is not None and s.proxy_running:
        return s.proxy.get_status()
    return {
        "running": False,
        "target_url": "",
        "stats": {"total_requests": 0, "blocked": 0, "alerts_generated": 0, "forwarded": 0},
        "uptime_seconds": 0,
        "traffic_log_size": 0,
    }


@router.get("/proxy/traffic")
def proxy_traffic(
    limit: int = 100,
    agent: str | None = None,
    blocked_only: bool = False,
) -> list[dict[str, Any]]:
    """Get recent proxy traffic log."""
    s = AppState.get()
    if s.proxy is not None and s.proxy_running:
        return s.proxy.get_traffic(limit=limit, agent=agent, blocked_only=blocked_only)
    return []


class ProxyStartRequest(BaseModel):
    target_url: str
    port: int = 9090
    require_auth: bool = True


@router.post("/proxy/start")
def proxy_start_endpoint(req: ProxyStartRequest) -> dict[str, Any]:
    """Start the MCP proxy in a background thread.

    For Cloud mode only — CLI mode runs the proxy in the foreground.
    """
    import threading

    s = AppState.get()

    if s.proxy_running:
        return {"status": "already_running", "target_url": s.proxy.target_url}

    from navil.proxy import MCPSecurityProxy, create_proxy_app

    proxy = MCPSecurityProxy(
        target_url=req.target_url,
        policy_engine=s.policy_engine,
        anomaly_detector=s.anomaly_detector,
        credential_manager=s.credential_manager,
        require_auth=req.require_auth,
    )
    s.proxy = proxy
    s.proxy_running = True

    app = create_proxy_app(proxy)

    def _run() -> None:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=req.port, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True, name="navil-proxy")
    thread.start()

    return {
        "status": "started",
        "target_url": req.target_url,
        "port": req.port,
        "require_auth": req.require_auth,
    }


# ── Ingestion endpoints (proxy → cloud) ─────────────────────


class IngestEvent(BaseModel):
    agent_name: str
    tool_name: str
    action: str
    duration_ms: int
    data_accessed_bytes: int = 0
    success: bool = True
    timestamp: str | None = None


class IngestEventsRequest(BaseModel):
    events: list[IngestEvent]


class IngestAlert(BaseModel):
    agent_name: str
    anomaly_type: str
    severity: str
    description: str = ""
    evidence: list[str] = []
    timestamp: str | None = None


class IngestAlertsRequest(BaseModel):
    alerts: list[IngestAlert]


class HeartbeatRequest(BaseModel):
    proxy_version: str = "unknown"
    target_url: str = ""
    uptime_seconds: int = 0
    stats: dict[str, Any] = {}


def _get_user_plan(user_id: str) -> str:
    """Get the billing plan for a user (for rate limiting)."""
    s = AppState.get()
    try:
        if s.stripe_enabled:
            status = s.billing.get_subscription_status(user_id)  # type: ignore[attr-defined]
            return status.plan
        billing = s.billing.get_billing(user_id)  # type: ignore[attr-defined]
        return billing.plan
    except Exception:
        return "free"


def _check_rate(user_id: str, resource: str, count: int = 1) -> None:
    """Raise 429 if rate limit exceeded."""
    try:
        from navil.cloud.rate_limiter import check_rate_limit

        plan = _get_user_plan(user_id)
        allowed, remaining, retry_after = check_rate_limit(user_id, resource, plan, count)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
    except HTTPException:
        raise
    except Exception:
        # Rate limiter failure should not block ingestion
        pass


@router.post("/ingest/events")
def ingest_events(req: IngestEventsRequest, request: Request) -> dict[str, Any]:
    """Batch-ingest MCP invocation events from a customer proxy.

    Authenticated via API key (``nvl_...``).  Max 1000 events per batch.
    """
    if len(req.events) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 events per batch")

    user_id = _get_user_id(request)
    _check_rate(user_id, "events_min", len(req.events))
    _check_rate(user_id, "events_hour", len(req.events))

    # Monthly event quota enforcement
    s = AppState.get()
    if s.stripe_enabled:
        try:
            allowed, remaining = s.billing.check_monthly_event_limit(  # type: ignore[attr-defined]
                user_id, len(req.events),
            )
            if not allowed:
                raise HTTPException(
                    status_code=402,
                    detail=f"Monthly event quota exceeded. {remaining} remaining.",
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Quota check failure should not block ingestion

    from navil.cloud.pipeline import DataPipeline

    pipeline = DataPipeline()
    s = AppState.get()
    tenant_detector = s.tenant_detectors.get(user_id)

    ingested = 0
    for ev in req.events:
        pipeline.ingest_event(
            user_id=user_id,
            agent_name=ev.agent_name,
            tool_name=ev.tool_name,
            action=ev.action,
            duration_ms=ev.duration_ms,
            data_accessed_bytes=ev.data_accessed_bytes,
            success=ev.success,
        )
        # Feed into per-tenant anomaly detector for server-side detection
        tenant_detector.record_invocation(
            agent_name=ev.agent_name,
            tool_name=ev.tool_name,
            action=ev.action,
            duration_ms=ev.duration_ms,
            data_accessed_bytes=ev.data_accessed_bytes,
            success=ev.success,
        )
        ingested += 1

    # Check for server-side alerts generated by the tenant detector
    server_alerts = tenant_detector.get_alerts()
    new_server_alerts = 0
    if server_alerts:
        for sa in server_alerts[-ingested:]:
            pipeline.ingest_alert(
                user_id=user_id,
                agent_name=sa.get("agent", "unknown"),
                anomaly_type=sa.get("anomaly_type", "unknown"),
                severity=sa.get("severity", "LOW"),
                details={
                    "description": sa.get("description", ""),
                    "evidence": sa.get("evidence", []),
                    "source": "server_detection",
                },
            )
            new_server_alerts += 1

    return {"ingested": ingested, "server_alerts": new_server_alerts, "status": "ok"}


@router.post("/ingest/alerts")
def ingest_alerts(req: IngestAlertsRequest, request: Request) -> dict[str, Any]:
    """Ingest anomaly alerts from a customer proxy.

    Max 100 alerts per batch.
    """
    if len(req.alerts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 alerts per batch")

    user_id = _get_user_id(request)
    _check_rate(user_id, "alerts_min", len(req.alerts))

    from navil.cloud.pipeline import DataPipeline

    pipeline = DataPipeline()
    ingested = 0
    for alert in req.alerts:
        pipeline.ingest_alert(
            user_id=user_id,
            agent_name=alert.agent_name,
            anomaly_type=alert.anomaly_type,
            severity=alert.severity,
            details={
                "description": alert.description,
                "evidence": alert.evidence,
            },
        )
        ingested += 1

    return {"ingested": ingested, "status": "ok"}


@router.post("/ingest/heartbeat")
def ingest_heartbeat(req: HeartbeatRequest, request: Request) -> dict[str, Any]:
    """Record a heartbeat from a customer proxy."""
    user_id = _get_user_id(request)

    from navil.cloud.database import get_session
    from navil.cloud.models import ProxyHeartbeat

    try:
        with get_session() as session:
            # Upsert: update existing or create new
            existing = (
                session.query(ProxyHeartbeat)
                .filter(ProxyHeartbeat.user_id == user_id)
                .first()
            )
            if existing:
                existing.proxy_version = req.proxy_version
                existing.target_url = req.target_url
                existing.uptime_seconds = req.uptime_seconds
                existing.stats = json.dumps(req.stats)
                import datetime as _dt

                existing.last_seen_at = _dt.datetime.utcnow()
            else:
                session.add(
                    ProxyHeartbeat(
                        user_id=user_id,
                        proxy_version=req.proxy_version,
                        target_url=req.target_url,
                        uptime_seconds=req.uptime_seconds,
                        stats=json.dumps(req.stats),
                    )
                )
    except Exception:
        _logger.exception("Failed to record heartbeat")

    return {"status": "ok"}


# ── Connection status ─────────────────────────────────────────


@router.get("/proxy/connection")
def proxy_connection_status(request: Request) -> dict[str, Any]:
    """Get the connection status of the customer's proxy."""
    user_id = _get_user_id(request)

    from navil.cloud.database import get_session
    from navil.cloud.models import ProxyHeartbeat

    try:
        with get_session() as session:
            hb = (
                session.query(ProxyHeartbeat)
                .filter(ProxyHeartbeat.user_id == user_id)
                .first()
            )
            if hb is None:
                return {"connected": False, "status": "never_connected"}

            import datetime as _dt

            age = (_dt.datetime.utcnow() - hb.last_seen_at).total_seconds()
            if age < 120:
                status = "connected"
            elif age < 600:
                status = "stale"
            else:
                status = "disconnected"

            return {
                "connected": status == "connected",
                "status": status,
                "last_seen_at": hb.last_seen_at.isoformat() if hb.last_seen_at else None,
                "proxy_version": hb.proxy_version,
                "target_url": hb.target_url,
                "uptime_seconds": hb.uptime_seconds,
                "stats": json.loads(hb.stats) if hb.stats else {},
            }
    except Exception:
        _logger.exception("Failed to get connection status")
        return {"connected": False, "status": "error"}


# ── API Key management ────────────────────────────────────────


class CreateApiKeyRequest(BaseModel):
    name: str = "Default"
    scopes: list[str] = ["ingest"]


@router.get("/api-keys")
def list_api_keys(request: Request) -> list[dict[str, Any]]:
    """List all API keys for the current user."""
    from navil.cloud.api_keys import ApiKeyManager

    user_id = _get_user_id(request)
    mgr = ApiKeyManager()
    keys = mgr.list_keys(user_id)
    result = []
    for k in keys:
        # Parse scopes from JSON string to list
        scopes = k.scopes
        if isinstance(scopes, str):
            try:
                scopes = json.loads(scopes)
            except (json.JSONDecodeError, TypeError):
                scopes = ["ingest"]

        last_used = k.last_used_at
        expires = k.expires_at
        created = k.created_at
        result.append({
            "id": k.id,
            "key_prefix": k.key_prefix,
            "name": k.name,
            "scopes": scopes,
            "last_used_at": (
                last_used.isoformat()
                if hasattr(last_used, "isoformat") else str(last_used) if last_used else None
            ),
            "expires_at": (
                expires.isoformat()
                if hasattr(expires, "isoformat") else str(expires) if expires else None
            ),
            "revoked": k.revoked,
            "created_at": (
                created.isoformat()
                if hasattr(created, "isoformat") else str(created) if created else None
            ),
        })
    return result


@router.post("/api-keys")
def create_api_key(req: CreateApiKeyRequest, request: Request) -> dict[str, Any]:
    """Create a new API key.  Returns the raw key exactly once."""
    from navil.cloud.api_keys import ApiKeyManager

    user_id = _get_user_id(request)
    mgr = ApiKeyManager()

    # Limit to 10 active keys per user
    if mgr.count_keys(user_id) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 active API keys per account")

    key_id, raw_key = mgr.create_key(user_id, name=req.name, scopes=req.scopes)

    # Return key_prefix for display and raw_key for one-time copy
    return {
        "key_id": key_id,
        "key_prefix": raw_key[:12],
        "raw_key": raw_key,
        "name": req.name,
        "scopes": req.scopes,
    }


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: int, request: Request) -> dict[str, Any]:
    """Revoke an API key."""
    from navil.cloud.api_keys import ApiKeyManager

    user_id = _get_user_id(request)
    mgr = ApiKeyManager()
    if not mgr.revoke_key(user_id, key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked", "key_id": key_id}


# ── Health check ──────────────────────────────────────────────


@router.get("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint.  Returns component status."""
    components: dict[str, str] = {}

    # Database check
    try:
        from sqlalchemy import text

        from navil.cloud.database import get_session

        with get_session() as session:
            session.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception as e:
        components["database"] = f"error: {e}"

    # Redis check
    try:
        from navil.cloud.rate_limiter import _get_redis

        r = _get_redis()
        if r is not None:
            r.ping()
            components["redis"] = "ok"
        else:
            components["redis"] = "not_configured"
    except Exception as e:
        components["redis"] = f"error: {e}"

    all_ok = all(v == "ok" or v == "not_configured" for v in components.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "components": components,
        "version": "0.1.0",
    }


# ── Clerk Webhook ────────────────────────────────────────────


@router.post("/webhooks/clerk")
async def clerk_webhook(request: Request) -> dict[str, Any]:
    """Handle Clerk webhook events (user.created, etc.).

    On user.created: send welcome email, create default API key.
    """
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    event_type = body.get("type", "")
    data = body.get("data", {})

    if event_type == "user.created":
        user_id = data.get("id", "")
        email_addresses = data.get("email_addresses", [])
        email = email_addresses[0].get("email_address", "") if email_addresses else ""
        first_name = data.get("first_name", "")

        _logger.info("Clerk user.created: user_id=%s email=%s", user_id, email)

        # Send welcome email
        if email:
            try:
                from navil.cloud.email import get_email_service

                svc = get_email_service()
                svc.send_welcome(email, first_name)
            except Exception:
                _logger.exception("Failed to send welcome email")

        # Create default API key
        if user_id:
            try:
                from navil.cloud.api_keys import ApiKeyManager

                mgr = ApiKeyManager()
                mgr.create_key(user_id, name="Default", scopes=["ingest"])
                _logger.info("Default API key created for user %s", user_id)
            except Exception:
                _logger.exception("Failed to create default API key")

    return {"status": "ok", "type": event_type}
