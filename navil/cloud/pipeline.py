# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Data ingestion pipeline for Navil Cloud.

Bridges the in-memory anomaly detector / policy engine with the
persistent storage layer.  Call ``ingest_event`` on every invocation
to build the data foundation for analytics features.

Usage::

    from navil.cloud.pipeline import DataPipeline

    pipeline = DataPipeline()
    pipeline.ingest_event(user_id, agent_name, tool_name, ...)
    pipeline.ingest_alert(user_id, agent_name, anomaly_type, ...)
    pipeline.snapshot_agent_metrics(user_id, anomaly_detector)
    pipeline.aggregate_trends(user_id)
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DataPipeline:
    """Ingests events and alerts into the persistent storage layer."""

    # ── Event Ingestion ──────────────────────────────────────

    def ingest_event(
        self,
        user_id: str,
        agent_name: str,
        tool_name: str,
        action: str,
        duration_ms: int,
        data_accessed_bytes: int = 0,
        success: bool = True,
    ) -> None:
        """Persist a single MCP invocation event."""
        from navil.cloud.database import get_session
        from navil.cloud.models import Event

        try:
            with get_session() as session:
                session.add(
                    Event(
                        user_id=user_id,
                        agent_name=agent_name,
                        tool_name=tool_name,
                        action=action,
                        duration_ms=duration_ms,
                        data_accessed_bytes=data_accessed_bytes,
                        success=success,
                    )
                )
        except Exception:
            logger.exception("Failed to ingest event for agent=%s", agent_name)

    # ── Alert Ingestion ──────────────────────────────────────

    def ingest_alert(
        self,
        user_id: str,
        agent_name: str,
        anomaly_type: str,
        severity: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Persist an anomaly alert."""
        from navil.cloud.database import get_session
        from navil.cloud.models import Alert

        try:
            with get_session() as session:
                session.add(
                    Alert(
                        user_id=user_id,
                        agent_name=agent_name,
                        anomaly_type=anomaly_type,
                        severity=severity,
                        details=json.dumps(details or {}),
                    )
                )
        except Exception:
            logger.exception("Failed to ingest alert for agent=%s", agent_name)

    # ── Agent Metric Snapshots ───────────────────────────────

    def snapshot_agent_metrics(
        self,
        user_id: str,
        anomaly_detector: Any,
    ) -> int:
        """Snapshot current agent baselines into persistent storage.

        Typically called on a schedule (e.g., every 5 minutes) to capture
        the current state of adaptive baselines.  Returns the number of
        agents snapshotted.
        """
        from navil.cloud.database import get_session
        from navil.cloud.models import AgentMetric

        count = 0
        try:
            with get_session() as session:
                for name, bl in anomaly_detector.adaptive_baselines.items():
                    session.add(
                        AgentMetric(
                            user_id=user_id,
                            agent_name=name,
                            observation_count=bl.duration_ema.count,
                            duration_mean=round(bl.duration_ema.mean, 2),
                            data_volume_mean=round(bl.data_volume_ema.mean, 2),
                            known_tools=json.dumps(list(bl.known_tools)),
                        )
                    )
                    count += 1
        except Exception:
            logger.exception("Failed to snapshot agent metrics")
        return count

    # ── Trend Aggregation ────────────────────────────────────

    def aggregate_trends(
        self,
        user_id: str,
        period_hours: int = 1,
    ) -> int:
        """Aggregate events and alerts into trend entries.

        Looks at the most recent *period_hours* window and creates
        an ``AnomalyTrend`` row.  Returns the number of trend rows created.

        Typically called on a schedule (e.g., hourly) to build the
        time-series data for the analytics dashboard.
        """
        from sqlalchemy import func as sqlfunc

        from navil.cloud.database import get_session
        from navil.cloud.models import Alert, AnomalyTrend, Event

        now = dt.datetime.utcnow()
        period_start = now - dt.timedelta(hours=period_hours)

        try:
            with get_session() as session:
                # Get all agents active in this period
                agents = (
                    session.query(Event.agent_name)
                    .filter(
                        Event.user_id == user_id,
                        Event.created_at >= period_start,
                    )
                    .distinct()
                    .all()
                )
                agent_names: list[str | None] = [r[0] for r in agents]
                agent_names.append(None)  # global aggregate

                count = 0
                for agent in agent_names:
                    # Count events
                    eq = session.query(sqlfunc.count(Event.id)).filter(
                        Event.user_id == user_id,
                        Event.created_at >= period_start,
                    )
                    if agent is not None:
                        eq = eq.filter(Event.agent_name == agent)
                    total_events = eq.scalar() or 0

                    # Count alerts by severity
                    aq = session.query(Alert.severity, sqlfunc.count(Alert.id)).filter(
                        Alert.user_id == user_id,
                        Alert.created_at >= period_start,
                    )
                    if agent is not None:
                        aq = aq.filter(Alert.agent_name == agent)
                    severity_rows = aq.group_by(Alert.severity).all()

                    severity_breakdown = {sev: cnt for sev, cnt in severity_rows}
                    anomaly_count = sum(severity_breakdown.values())
                    anomaly_rate = anomaly_count / max(total_events, 1)

                    session.add(
                        AnomalyTrend(
                            user_id=user_id,
                            agent_name=agent,
                            period_start=period_start,
                            period_end=now,
                            total_events=total_events,
                            anomaly_count=anomaly_count,
                            anomaly_rate=round(anomaly_rate, 6),
                            severity_breakdown=json.dumps(severity_breakdown),
                        )
                    )
                    count += 1

                return count
        except Exception:
            logger.exception("Failed to aggregate trends")
            return 0
