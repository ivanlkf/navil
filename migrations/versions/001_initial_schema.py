"""Initial schema: events, alerts, agent_metrics, trust_scores, anomaly_trends.

Revision ID: 001
Revises: None
Create Date: 2026-03-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── events ───────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("tool_name", sa.String(256), nullable=False),
        sa.Column("action", sa.String(256), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("data_accessed_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_user_id", "events", ["user_id"])
    op.create_index("ix_events_agent_name", "events", ["agent_name"])
    op.create_index("ix_events_user_agent", "events", ["user_id", "agent_name"])
    op.create_index("ix_events_created", "events", ["created_at"])

    # ── alerts ───────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("anomaly_type", sa.String(128), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("details", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_agent_name", "alerts", ["agent_name"])
    op.create_index("ix_alerts_user_severity", "alerts", ["user_id", "severity"])
    op.create_index("ix_alerts_created", "alerts", ["created_at"])

    # ── agent_metrics ────────────────────────────────────────
    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("observation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_mean", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("data_volume_mean", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("known_tools", sa.Text, nullable=False, server_default="[]"),
        sa.Column("trust_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_metrics_user_id", "agent_metrics", ["user_id"])
    op.create_index("ix_agent_metrics_user_agent", "agent_metrics", ["user_id", "agent_name"])
    op.create_index("ix_agent_metrics_created", "agent_metrics", ["created_at"])

    # ── trust_scores ─────────────────────────────────────────
    op.create_table(
        "trust_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("components", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trust_scores_user_id", "trust_scores", ["user_id"])
    op.create_index("ix_trust_scores_user_agent", "trust_scores", ["user_id", "agent_name"])
    op.create_index("ix_trust_scores_created", "trust_scores", ["created_at"])

    # ── anomaly_trends ───────────────────────────────────────
    op.create_table(
        "anomaly_trends",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("agent_name", sa.String(256), nullable=True),
        sa.Column("period_start", sa.DateTime, nullable=False),
        sa.Column("period_end", sa.DateTime, nullable=False),
        sa.Column("total_events", sa.Integer, nullable=False, server_default="0"),
        sa.Column("anomaly_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("anomaly_rate", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("severity_breakdown", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_anomaly_trends_user_id", "anomaly_trends", ["user_id"])
    op.create_index("ix_anomaly_trends_user_period", "anomaly_trends", ["user_id", "period_start"])


def downgrade() -> None:
    op.drop_table("anomaly_trends")
    op.drop_table("trust_scores")
    op.drop_table("agent_metrics")
    op.drop_table("alerts")
    op.drop_table("events")
