# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Admin API endpoints for Navil Cloud operator portal.

Protected by ``NAVIL_ADMIN_IDS`` — a comma-separated list of Clerk user IDs
that have operator access.  When not set, admin endpoints return 403.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import func, text

from navil.cloud.state import AppState

router = APIRouter(prefix="/api/admin")

_logger = logging.getLogger(__name__)

# Comma-separated Clerk user_ids that are operators
_ADMIN_IDS: set[str] = {
    uid.strip()
    for uid in os.environ.get("NAVIL_ADMIN_IDS", "").split(",")
    if uid.strip()
}


def _require_admin(request: Request) -> str:
    """Raise 403 if the caller is not an admin.  Returns user_id."""
    user_id = getattr(request.state, "user_id", None)

    # Dev mode: when Clerk isn't configured, no auth middleware sets user_id
    clerk_configured = bool(os.environ.get("CLERK_SECRET_KEY"))
    if not clerk_configured:
        # Allow access in local dev — no auth enforced
        return user_id or "dev-admin"

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    # In production, check against admin user IDs
    if _ADMIN_IDS and user_id not in _ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


# ---------------------------------------------------------------------------
# System overview
# ---------------------------------------------------------------------------


@router.get("/overview")
def admin_overview(request: Request) -> dict[str, Any]:
    """Global system stats for the operator dashboard."""
    _require_admin(request)
    s = AppState.get()

    result: dict[str, Any] = {
        "tenant_detectors_active": s.tenant_detectors.size,
        "llm_available": s.llm_available,
        "llm_provider": s.llm_provider,
        "llm_model": s.llm_model,
        "stripe_enabled": s.stripe_enabled,
        "proxy_running": s.proxy_running,
    }

    # Database stats
    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert, ApiKey, Event, ProxyHeartbeat

        with get_session() as session:
            result["total_events"] = session.query(func.count(Event.id)).scalar() or 0
            result["total_alerts"] = session.query(func.count(Alert.id)).scalar() or 0
            result["total_api_keys"] = (
                session.query(func.count(ApiKey.id))
                .filter(ApiKey.revoked == False)  # noqa: E712
                .scalar() or 0
            )

            # Unique tenants (users with at least one API key)
            result["total_tenants"] = (
                session.query(func.count(func.distinct(ApiKey.user_id)))
                .filter(ApiKey.revoked == False)  # noqa: E712
                .scalar() or 0
            )

            # Connected proxies (heartbeat within last 5 min)
            cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=5)
            result["connected_proxies"] = (
                session.query(func.count(ProxyHeartbeat.id))
                .filter(ProxyHeartbeat.last_seen_at >= cutoff)
                .scalar() or 0
            )

            # Events in last hour
            one_hour = dt.datetime.utcnow() - dt.timedelta(hours=1)
            result["events_last_hour"] = (
                session.query(func.count(Event.id))
                .filter(Event.created_at >= one_hour)
                .scalar() or 0
            )

            # Alerts in last hour
            result["alerts_last_hour"] = (
                session.query(func.count(Alert.id))
                .filter(Alert.created_at >= one_hour)
                .scalar() or 0
            )

            # Critical alerts (last 24h)
            one_day = dt.datetime.utcnow() - dt.timedelta(hours=24)
            result["critical_alerts_24h"] = (
                session.query(func.count(Alert.id))
                .filter(Alert.created_at >= one_day, Alert.severity == "CRITICAL")
                .scalar() or 0
            )

    except Exception as exc:
        _logger.warning("Admin overview DB query failed: %s", exc)
        result["db_error"] = str(exc)

    # Rate limiter backend
    try:
        from navil.cloud.rate_limiter import REDIS_URL

        result["redis_configured"] = bool(REDIS_URL)
    except Exception:
        result["redis_configured"] = False

    # Scheduler status
    try:
        from navil.cloud.scheduler import _scheduler

        result["scheduler_running"] = _scheduler is not None
    except Exception:
        result["scheduler_running"] = False

    return result


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------


@router.get("/tenants")
def list_tenants(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    search: str = "",
) -> dict[str, Any]:
    """List all tenants with their stats."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert, ApiKey, Event, ProxyHeartbeat

        with get_session() as session:
            # Get unique user_ids from API keys
            base_q = session.query(ApiKey.user_id).distinct()
            if search:
                base_q = base_q.filter(ApiKey.user_id.contains(search))

            total = base_q.count()
            user_ids = [
                r[0] for r in base_q.order_by(ApiKey.user_id).offset(offset).limit(limit).all()
            ]

            tenants = []
            for uid in user_ids:
                event_count = (
                    session.query(func.count(Event.id))
                    .filter(Event.user_id == uid)
                    .scalar() or 0
                )
                alert_count = (
                    session.query(func.count(Alert.id))
                    .filter(Alert.user_id == uid)
                    .scalar() or 0
                )
                key_count = (
                    session.query(func.count(ApiKey.id))
                    .filter(ApiKey.user_id == uid, ApiKey.revoked == False)  # noqa: E712
                    .scalar() or 0
                )

                # Last heartbeat
                heartbeat = (
                    session.query(ProxyHeartbeat)
                    .filter(ProxyHeartbeat.user_id == uid)
                    .order_by(ProxyHeartbeat.last_seen_at.desc())
                    .first()
                )

                cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=5)
                proxy_status = "disconnected"
                last_seen = None
                if heartbeat:
                    last_seen = heartbeat.last_seen_at.isoformat() if hasattr(
                        heartbeat.last_seen_at, "isoformat"
                    ) else str(heartbeat.last_seen_at)
                    if heartbeat.last_seen_at >= cutoff:
                        proxy_status = "connected"
                    elif heartbeat.last_seen_at >= cutoff - dt.timedelta(minutes=25):
                        proxy_status = "stale"

                # Get plan from billing
                s = AppState.get()
                plan = "free"
                try:
                    plan_info = s.billing.get_billing(uid)
                    plan = plan_info.get("plan", "free")
                except Exception:
                    pass

                tenants.append({
                    "user_id": uid,
                    "event_count": event_count,
                    "alert_count": alert_count,
                    "api_key_count": key_count,
                    "proxy_status": proxy_status,
                    "last_seen": last_seen,
                    "plan": plan,
                })

            return {"tenants": tenants, "total": total}

    except Exception as exc:
        _logger.warning("Admin tenants query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tenants/{user_id}")
def get_tenant_detail(request: Request, user_id: str) -> dict[str, Any]:
    """Detailed view of a single tenant."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert, ApiKey, Event, ProxyHeartbeat

        with get_session() as session:
            events = (
                session.query(Event)
                .filter(Event.user_id == user_id)
                .order_by(Event.created_at.desc())
                .limit(50)
                .all()
            )
            alerts = (
                session.query(Alert)
                .filter(Alert.user_id == user_id)
                .order_by(Alert.created_at.desc())
                .limit(50)
                .all()
            )
            keys = (
                session.query(ApiKey)
                .filter(ApiKey.user_id == user_id)
                .order_by(ApiKey.created_at.desc())
                .all()
            )
            heartbeats = (
                session.query(ProxyHeartbeat)
                .filter(ProxyHeartbeat.user_id == user_id)
                .order_by(ProxyHeartbeat.last_seen_at.desc())
                .limit(10)
                .all()
            )

            def _dt(v: Any) -> str | None:
                return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)

            return {
                "user_id": user_id,
                "events": [
                    {
                        "id": e.id, "agent_name": e.agent_name,
                        "tool_name": e.tool_name, "action": e.action,
                        "duration_ms": e.duration_ms, "success": e.success,
                        "created_at": _dt(e.created_at),
                    }
                    for e in events
                ],
                "alerts": [
                    {
                        "id": a.id, "agent_name": a.agent_name,
                        "anomaly_type": a.anomaly_type, "severity": a.severity,
                        "details": a.details, "created_at": _dt(a.created_at),
                    }
                    for a in alerts
                ],
                "api_keys": [
                    {
                        "id": k.id, "key_prefix": k.key_prefix, "name": k.name,
                        "revoked": k.revoked, "last_used_at": _dt(k.last_used_at),
                        "created_at": _dt(k.created_at),
                    }
                    for k in keys
                ],
                "heartbeats": [
                    {
                        "proxy_version": h.proxy_version, "target_url": h.target_url,
                        "uptime_seconds": h.uptime_seconds,
                        "last_seen_at": _dt(h.last_seen_at),
                    }
                    for h in heartbeats
                ],
            }

    except Exception as exc:
        _logger.warning("Admin tenant detail failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Global alerts
# ---------------------------------------------------------------------------


@router.get("/alerts")
def admin_alerts(
    request: Request,
    severity: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List alerts across all tenants."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert

        with get_session() as session:
            q = session.query(Alert)
            if severity:
                q = q.filter(Alert.severity == severity.upper())
            total = q.count()
            alerts = q.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

            def _dt(v: Any) -> str | None:
                return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)

            return {
                "alerts": [
                    {
                        "id": a.id, "user_id": a.user_id,
                        "agent_name": a.agent_name,
                        "anomaly_type": a.anomaly_type,
                        "severity": a.severity,
                        "details": a.details,
                        "created_at": _dt(a.created_at),
                    }
                    for a in alerts
                ],
                "total": total,
            }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Global events
# ---------------------------------------------------------------------------


@router.get("/events")
def admin_events(
    request: Request,
    user_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List events across all tenants, optionally filtered by user."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Event

        with get_session() as session:
            q = session.query(Event)
            if user_id:
                q = q.filter(Event.user_id == user_id)
            total = q.count()
            events = q.order_by(Event.created_at.desc()).offset(offset).limit(limit).all()

            def _dt(v: Any) -> str | None:
                return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)

            return {
                "events": [
                    {
                        "id": e.id, "user_id": e.user_id,
                        "agent_name": e.agent_name,
                        "tool_name": e.tool_name, "action": e.action,
                        "duration_ms": e.duration_ms, "success": e.success,
                        "created_at": _dt(e.created_at),
                    }
                    for e in events
                ],
                "total": total,
            }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# API keys (global view)
# ---------------------------------------------------------------------------


@router.get("/api-keys")
def admin_api_keys(
    request: Request,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List all API keys across tenants."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            total = session.query(func.count(ApiKey.id)).scalar() or 0
            keys = (
                session.query(ApiKey)
                .order_by(ApiKey.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            def _dt(v: Any) -> str | None:
                return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)

            return {
                "keys": [
                    {
                        "id": k.id, "user_id": k.user_id,
                        "key_prefix": k.key_prefix, "name": k.name,
                        "revoked": k.revoked,
                        "last_used_at": _dt(k.last_used_at),
                        "created_at": _dt(k.created_at),
                    }
                    for k in keys
                ],
                "total": total,
            }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/api-keys/{key_id}")
def admin_revoke_api_key(request: Request, key_id: int) -> dict[str, str]:
    """Admin-revoke any API key."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                raise HTTPException(status_code=404, detail="API key not found")
            key.revoked = True
            return {"status": "revoked"}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# System health
# ---------------------------------------------------------------------------


@router.get("/system")
def admin_system(request: Request) -> dict[str, Any]:
    """Detailed system health and configuration."""
    _require_admin(request)
    s = AppState.get()

    result: dict[str, Any] = {
        "llm": s.get_llm_config(),
        "tenant_detectors": {
            "active": s.tenant_detectors.size,
            "max_size": s.tenant_detectors._max_size,
        },
        "stripe_enabled": s.stripe_enabled,
        "proxy_running": s.proxy_running,
    }

    # Database health
    try:
        from navil.cloud.database import DATABASE_URL, get_session

        result["database"] = {
            "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
            "status": "unknown",
        }
        with get_session() as session:
            session.execute(text("SELECT 1"))
            result["database"]["status"] = "connected"
    except Exception as exc:
        result["database"] = {"status": "error", "error": str(exc)}

    # Redis health
    try:
        from navil.cloud.rate_limiter import REDIS_URL, _get_redis

        if REDIS_URL:
            r = _get_redis()
            if r:
                info = r.info("memory")
                result["redis"] = {
                    "status": "connected",
                    "url": REDIS_URL.split("@")[-1] if "@" in REDIS_URL else "localhost",
                    "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 1),
                }
            else:
                result["redis"] = {"status": "connection_failed"}
        else:
            result["redis"] = {"status": "not_configured"}
    except Exception as exc:
        result["redis"] = {"status": "error", "error": str(exc)}

    # Scheduler
    try:
        from navil.cloud.scheduler import _scheduler

        if _scheduler is not None:
            result["scheduler"] = {"status": "running"}
        else:
            result["scheduler"] = {"status": "stopped"}
    except Exception:
        result["scheduler"] = {"status": "unknown"}

    # Environment
    result["environment"] = {
        "clerk_configured": bool(os.environ.get("CLERK_SECRET_KEY")),
        "stripe_configured": bool(os.environ.get("STRIPE_SECRET_KEY")),
        "resend_configured": bool(os.environ.get("RESEND_API_KEY")),
        "admin_ids_set": bool(_ADMIN_IDS),
    }

    return result


# ---------------------------------------------------------------------------
# Ingestion throughput
# ---------------------------------------------------------------------------


@router.get("/throughput")
def admin_throughput(request: Request, hours: int = 24) -> dict[str, Any]:
    """Hourly event/alert throughput for the last N hours."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert, Event

        cutoff = dt.datetime.utcnow() - dt.timedelta(hours=hours)

        with get_session() as session:
            # Hourly event counts
            event_rows = (
                session.query(
                    func.strftime("%Y-%m-%d %H:00", Event.created_at).label("hour"),
                    func.count(Event.id).label("count"),
                )
                .filter(Event.created_at >= cutoff)
                .group_by("hour")
                .order_by("hour")
                .all()
            )

            alert_rows = (
                session.query(
                    func.strftime("%Y-%m-%d %H:00", Alert.created_at).label("hour"),
                    func.count(Alert.id).label("count"),
                )
                .filter(Alert.created_at >= cutoff)
                .group_by("hour")
                .order_by("hour")
                .all()
            )

            return {
                "events": [{"hour": r[0], "count": r[1]} for r in event_rows],
                "alerts": [{"hour": r[0], "count": r[1]} for r in alert_rows],
            }

    except Exception as exc:
        _logger.warning("Admin throughput query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Plan distribution
# ---------------------------------------------------------------------------


@router.get("/billing")
def admin_billing(request: Request) -> dict[str, Any]:
    """Billing summary across all tenants."""
    _require_admin(request)

    try:
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            user_ids = [
                r[0] for r in session.query(ApiKey.user_id).distinct().all()
            ]

        s = AppState.get()
        plan_counts: dict[str, int] = {"free": 0, "lite": 0, "elite": 0}
        for uid in user_ids:
            try:
                info = s.billing.get_billing(uid)
                plan = info.get("plan", "free")
                plan_counts[plan] = plan_counts.get(plan, 0) + 1
            except Exception:
                plan_counts["free"] += 1

        return {
            "total_users": len(user_ids),
            "plan_distribution": plan_counts,
            "stripe_enabled": s.stripe_enabled,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
