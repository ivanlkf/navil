# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Background scheduler for Navil Cloud periodic jobs.

Jobs
----

- **Metrics snapshot** (every 5 min) — persist aggregated agent metrics
- **Trend aggregation** (hourly) — roll up event counts for trend charts
- **Detector cache eviction** (every 10 min) — remove idle tenant detectors
- **Alert digest** (hourly) — send email digests (Phase 5)

Uses ``APScheduler`` when available, otherwise falls back to a simple
``threading.Timer``-based scheduler for environments without the dependency.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class _SimpleScheduler:
    """Minimal recurring-task scheduler using daemon threads.

    Fallback for when APScheduler is not installed.
    """

    def __init__(self) -> None:
        self._jobs: list[tuple[str, float, Any, bool]] = []
        self._running = False
        self._threads: list[threading.Thread] = []

    def add_job(
        self,
        func: Any,
        name: str,
        interval_seconds: float,
    ) -> None:
        self._jobs.append((name, interval_seconds, func, True))

    def start(self) -> None:
        self._running = True
        for name, interval, func, _ in self._jobs:
            t = threading.Thread(
                target=self._loop,
                args=(name, interval, func),
                daemon=True,
                name=f"navil-sched-{name}",
            )
            t.start()
            self._threads.append(t)
        logger.info("Simple scheduler started with %d jobs", len(self._jobs))

    def _loop(self, name: str, interval: float, func: Any) -> None:
        while self._running:
            time.sleep(interval)
            if not self._running:
                break
            try:
                func()
            except Exception:
                logger.exception("Scheduler job %s failed", name)

    def shutdown(self) -> None:
        self._running = False
        logger.info("Simple scheduler stopped")


def _create_scheduler() -> Any:
    """Create APScheduler or fallback."""
    try:
        from apscheduler.schedulers.background import (
            BackgroundScheduler,  # type: ignore[import-untyped]
        )

        scheduler = BackgroundScheduler(daemon=True)
        logger.info("Using APScheduler backend")
        return scheduler
    except ImportError:
        logger.info("APScheduler not installed, using simple scheduler")
        return _SimpleScheduler()


# ---------------------------------------------------------------------------
# Job definitions
# ---------------------------------------------------------------------------


def _metrics_snapshot() -> None:
    """Persist aggregated agent metrics for dashboard charts."""
    try:
        from navil.cloud.pipeline import DataPipeline
        from navil.cloud.state import AppState

        s = AppState.get()
        pipeline = DataPipeline()
        # Snapshot metrics for each active tenant
        for uid, detector in list(
            s.tenant_detectors._cache.items()  # noqa: SLF001
        ):
            pipeline.snapshot_agent_metrics(uid, detector)
        logger.debug("Metrics snapshot completed")
    except Exception:
        logger.exception("Metrics snapshot failed")


def _trend_aggregation() -> None:
    """Roll up event counts for trend charts."""
    try:
        from navil.cloud.pipeline import DataPipeline
        from navil.cloud.state import AppState

        s = AppState.get()
        pipeline = DataPipeline()
        for uid in list(s.tenant_detectors._cache.keys()):  # noqa: SLF001
            pipeline.aggregate_trends(uid)
        logger.debug("Trend aggregation completed")
    except Exception:
        logger.exception("Trend aggregation failed")


def _alert_digest() -> None:
    """Send alert digest emails to users with new alerts."""
    try:
        from navil.cloud.database import get_session
        from navil.cloud.email import get_email_service
        from navil.cloud.models import Alert, EmailPreference

        svc = get_email_service()
        if svc._resend is None:
            return  # Email not configured

        import datetime as dt

        one_hour_ago = dt.datetime.utcnow() - dt.timedelta(hours=1)

        with get_session() as session:
            # Get users with recent alerts
            recent_alerts = (
                session.query(Alert)
                .filter(Alert.created_at >= one_hour_ago)
                .all()
            )
            if not recent_alerts:
                return

            # Group by user_id
            user_alerts: dict[str, list] = {}
            for alert in recent_alerts:
                user_alerts.setdefault(alert.user_id, []).append({
                    "severity": alert.severity,
                    "agent": alert.agent_name,
                    "anomaly_type": alert.anomaly_type,
                    "description": alert.details or "",
                })

            # Send digests (only to users who have critical/high alerts)
            for uid, alerts in user_alerts.items():
                has_urgent = any(
                    a["severity"] in ("CRITICAL", "HIGH") for a in alerts
                )
                if not has_urgent:
                    continue

                # Look up user email (would need Clerk API or stored email)
                # For now, skip users without stored email preferences
                pref = (
                    session.query(EmailPreference)
                    .filter(EmailPreference.user_id == uid)
                    .first()
                )
                if pref and hasattr(pref, "email"):
                    svc.send_alert_digest(pref.email, alerts, "hourly")

        logger.debug("Alert digest check completed")
    except Exception:
        logger.exception("Alert digest failed")


def _detector_cache_eviction() -> None:
    """Evict idle tenant detectors to free memory."""
    try:
        from navil.cloud.state import AppState

        s = AppState.get()
        evicted = s.tenant_detectors.evict_stale()
        if evicted:
            logger.info(
                "Evicted %d idle tenant detectors (size: %d)",
                evicted, s.tenant_detectors.size,
            )
    except Exception:
        logger.exception("Detector cache eviction failed")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_scheduler: Any = None


def start_scheduler() -> Any:
    """Start the background scheduler with all jobs registered."""
    global _scheduler  # noqa: PLW0603

    _scheduler = _create_scheduler()

    if isinstance(_scheduler, _SimpleScheduler):
        _scheduler.add_job(_metrics_snapshot, "metrics_snapshot", 300)
        _scheduler.add_job(_trend_aggregation, "trend_aggregation", 3600)
        _scheduler.add_job(_detector_cache_eviction, "detector_eviction", 600)
        _scheduler.add_job(_alert_digest, "alert_digest", 3600)
    else:
        # APScheduler
        _scheduler.add_job(
            _metrics_snapshot,
            "interval",
            minutes=5,
            id="metrics_snapshot",
            name="Metrics Snapshot",
        )
        _scheduler.add_job(
            _trend_aggregation,
            "interval",
            hours=1,
            id="trend_aggregation",
            name="Trend Aggregation",
        )
        _scheduler.add_job(
            _detector_cache_eviction,
            "interval",
            minutes=10,
            id="detector_eviction",
            name="Detector Cache Eviction",
        )
        _scheduler.add_job(
            _alert_digest,
            "interval",
            hours=1,
            id="alert_digest",
            name="Alert Digest Emails",
        )

    _scheduler.start()
    logger.info("Background scheduler started")
    return _scheduler


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Background scheduler stopped")
