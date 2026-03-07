# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Analytics engine for Navil Cloud (Elite feature).

Computes Agent Trust Scores, behavioral profiles, and anomaly trends
from the persistent storage layer.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrustScoreResult:
    """Result of a trust-score computation for a single agent."""

    agent_name: str
    score: float  # 0-100
    components: dict[str, float]
    verdict: str  # "trusted", "moderate", "untrusted"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "score": round(self.score, 1),
            "components": {k: round(v, 1) for k, v in self.components.items()},
            "verdict": self.verdict,
        }


class AnalyticsEngine:
    """Computes trust scores and analytics from stored data.

    All methods accept a SQLAlchemy session and operate on the
    persistent tables (events, alerts, agent_metrics, trust_scores).
    """

    # ── Trust Score Weights ──────────────────────────────────

    WEIGHT_POLICY_COMPLIANCE = 0.30
    WEIGHT_ANOMALY_FREQUENCY = 0.25
    WEIGHT_DATA_PATTERN = 0.20
    WEIGHT_BEHAVIORAL_STABILITY = 0.25

    # ── Trust Score ──────────────────────────────────────────

    def compute_trust_score(
        self,
        user_id: str,
        agent_name: str,
        *,
        session: Any = None,
    ) -> TrustScoreResult:
        """Compute the Agent Trust Score (0-100) for a single agent.

        Components:
        - **policy_compliance**: % of events that were policy-compliant.
        - **anomaly_frequency**: Inverse of anomaly rate (fewer = higher score).
        - **data_pattern**: Score based on data access consistency.
        - **behavioral_stability**: How stable the agent's behavior is over time.

        When no data is available, returns a neutral score of 50.
        """
        if session is None:
            from navil.cloud.database import get_session

            with get_session() as s:
                return self._compute_trust_score_impl(s, user_id, agent_name)
        return self._compute_trust_score_impl(session, user_id, agent_name)

    def _compute_trust_score_impl(
        self,
        session: Any,
        user_id: str,
        agent_name: str,
    ) -> TrustScoreResult:
        from navil.cloud.models import Alert, Event

        # Fetch recent events (last 1000)
        events = (
            session.query(Event)
            .filter(Event.user_id == user_id, Event.agent_name == agent_name)
            .order_by(Event.created_at.desc())
            .limit(1000)
            .all()
        )
        if not events:
            return TrustScoreResult(
                agent_name=agent_name,
                score=50.0,
                components={
                    "policy_compliance": 50.0,
                    "anomaly_frequency": 50.0,
                    "data_pattern": 50.0,
                    "behavioral_stability": 50.0,
                },
                verdict="moderate",
            )

        # Fetch alerts for this agent
        alerts = (
            session.query(Alert)
            .filter(Alert.user_id == user_id, Alert.agent_name == agent_name)
            .order_by(Alert.created_at.desc())
            .limit(500)
            .all()
        )

        # 1. Policy compliance: success rate
        success_count = sum(1 for e in events if e.success)
        policy_compliance = (success_count / len(events)) * 100.0

        # 2. Anomaly frequency: inverse of alert rate
        alert_rate = len(alerts) / max(len(events), 1)
        anomaly_frequency = max(0.0, 100.0 - (alert_rate * 500.0))  # scaled

        # 3. Data pattern: consistency of data access volumes
        volumes = [e.data_accessed_bytes for e in events if e.data_accessed_bytes > 0]
        if volumes:
            mean_vol = sum(volumes) / len(volumes)
            variance = sum((v - mean_vol) ** 2 for v in volumes) / len(volumes)
            cv = (variance**0.5) / max(mean_vol, 1.0)  # coefficient of variation
            data_pattern = max(0.0, 100.0 - (cv * 50.0))
        else:
            data_pattern = 75.0  # neutral-positive if no data access

        # 4. Behavioral stability: consistency of duration patterns
        durations = [e.duration_ms for e in events]
        mean_dur = sum(durations) / len(durations)
        dur_variance = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
        dur_cv = (dur_variance**0.5) / max(mean_dur, 1.0)
        behavioral_stability = max(0.0, 100.0 - (dur_cv * 50.0))

        # Weighted composite
        score = (
            policy_compliance * self.WEIGHT_POLICY_COMPLIANCE
            + anomaly_frequency * self.WEIGHT_ANOMALY_FREQUENCY
            + data_pattern * self.WEIGHT_DATA_PATTERN
            + behavioral_stability * self.WEIGHT_BEHAVIORAL_STABILITY
        )
        score = max(0.0, min(100.0, score))

        if score >= 70:
            verdict = "trusted"
        elif score >= 40:
            verdict = "moderate"
        else:
            verdict = "untrusted"

        components = {
            "policy_compliance": policy_compliance,
            "anomaly_frequency": anomaly_frequency,
            "data_pattern": data_pattern,
            "behavioral_stability": behavioral_stability,
        }

        # Persist the score
        from navil.cloud.models import TrustScore as TrustScoreModel

        session.add(
            TrustScoreModel(
                user_id=user_id,
                agent_name=agent_name,
                score=score,
                components=json.dumps(components),
            )
        )

        return TrustScoreResult(
            agent_name=agent_name,
            score=score,
            components=components,
            verdict=verdict,
        )

    # ── Behavioral Profile ───────────────────────────────────

    def get_behavioral_profile(
        self,
        user_id: str,
        agent_name: str,
        *,
        session: Any = None,
    ) -> dict[str, Any]:
        """Build a behavioral profile for an agent from stored events.

        Returns tool usage breakdown, timing patterns, and data access summary.
        """
        if session is None:
            from navil.cloud.database import get_session

            with get_session() as s:
                return self._behavioral_profile_impl(s, user_id, agent_name)
        return self._behavioral_profile_impl(session, user_id, agent_name)

    def _behavioral_profile_impl(
        self,
        session: Any,
        user_id: str,
        agent_name: str,
    ) -> dict[str, Any]:
        from sqlalchemy import func as sqlfunc

        from navil.cloud.models import Event

        # Tool usage breakdown
        tool_stats = (
            session.query(
                Event.tool_name,
                sqlfunc.count(Event.id).label("count"),
                sqlfunc.avg(Event.duration_ms).label("avg_duration"),
                sqlfunc.sum(Event.data_accessed_bytes).label("total_bytes"),
            )
            .filter(Event.user_id == user_id, Event.agent_name == agent_name)
            .group_by(Event.tool_name)
            .all()
        )

        total_events = sum(r.count for r in tool_stats)

        tools = []
        for row in tool_stats:
            tools.append(
                {
                    "tool_name": row.tool_name,
                    "invocation_count": row.count,
                    "percentage": round((row.count / max(total_events, 1)) * 100, 1),
                    "avg_duration_ms": round(float(row.avg_duration or 0), 1),
                    "total_data_bytes": int(row.total_bytes or 0),
                }
            )

        return {
            "agent_name": agent_name,
            "total_events": total_events,
            "tools": sorted(tools, key=lambda t: t["invocation_count"], reverse=True),
        }

    # ── Anomaly Trends ───────────────────────────────────────

    def get_anomaly_trends(
        self,
        user_id: str,
        *,
        agent_name: str | None = None,
        limit: int = 30,
        session: Any = None,
    ) -> list[dict[str, Any]]:
        """Return pre-aggregated anomaly trend entries.

        Returns the most recent *limit* entries, optionally filtered by agent.
        """
        if session is None:
            from navil.cloud.database import get_session

            with get_session() as s:
                return self._anomaly_trends_impl(s, user_id, agent_name, limit)
        return self._anomaly_trends_impl(session, user_id, agent_name, limit)

    def _anomaly_trends_impl(
        self,
        session: Any,
        user_id: str,
        agent_name: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        from navil.cloud.models import AnomalyTrend

        q = session.query(AnomalyTrend).filter(AnomalyTrend.user_id == user_id)
        if agent_name is not None:
            q = q.filter(AnomalyTrend.agent_name == agent_name)
        else:
            q = q.filter(AnomalyTrend.agent_name.is_(None))

        rows = q.order_by(AnomalyTrend.period_start.desc()).limit(limit).all()

        return [
            {
                "period_start": r.period_start.isoformat(),
                "period_end": r.period_end.isoformat(),
                "total_events": r.total_events,
                "anomaly_count": r.anomaly_count,
                "anomaly_rate": round(r.anomaly_rate, 4),
                "severity_breakdown": json.loads(r.severity_breakdown),
            }
            for r in reversed(rows)
        ]

    # ── Trust Score History ──────────────────────────────────

    def get_trust_score_history(
        self,
        user_id: str,
        agent_name: str,
        *,
        limit: int = 30,
        session: Any = None,
    ) -> list[dict[str, Any]]:
        """Return recent trust score entries for an agent."""
        if session is None:
            from navil.cloud.database import get_session

            with get_session() as s:
                return self._trust_history_impl(s, user_id, agent_name, limit)
        return self._trust_history_impl(session, user_id, agent_name, limit)

    def _trust_history_impl(
        self,
        session: Any,
        user_id: str,
        agent_name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        from navil.cloud.models import TrustScore

        rows = (
            session.query(TrustScore)
            .filter(TrustScore.user_id == user_id, TrustScore.agent_name == agent_name)
            .order_by(TrustScore.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "score": round(r.score, 1),
                "components": json.loads(r.components),
                "created_at": r.created_at.isoformat(),
            }
            for r in reversed(rows)
        ]
