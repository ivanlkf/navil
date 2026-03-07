# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""SQLAlchemy models for Navil Cloud persistent storage.

Tables
------
- **events**: Every MCP invocation recorded by the system.
- **alerts**: Persisted anomaly alerts with severity and details.
- **agent_metrics**: Periodic snapshots of per-agent behavioral baselines.
- **trust_scores**: Agent Trust Score history (Elite feature).
- **anomaly_trends**: Pre-aggregated anomaly rate time-series.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all Navil Cloud models."""


class Event(Base):
    """A single MCP tool invocation."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    agent_name = Column(String(256), nullable=False, index=True)
    tool_name = Column(String(256), nullable=False)
    action = Column(String(256), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    data_accessed_bytes = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_events_user_agent", "user_id", "agent_name"),
        Index("ix_events_created", "created_at"),
    )


class Alert(Base):
    """A persisted anomaly alert."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    agent_name = Column(String(256), nullable=False, index=True)
    anomaly_type = Column(String(128), nullable=False)
    severity = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    details = Column(Text, nullable=False, default="{}")  # JSON blob
    created_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_alerts_user_severity", "user_id", "severity"),
        Index("ix_alerts_created", "created_at"),
    )


class AgentMetric(Base):
    """Periodic snapshot of an agent's behavioral baseline."""

    __tablename__ = "agent_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    agent_name = Column(String(256), nullable=False)
    observation_count = Column(Integer, nullable=False, default=0)
    duration_mean = Column(Float, nullable=False, default=0.0)
    data_volume_mean = Column(Float, nullable=False, default=0.0)
    known_tools = Column(Text, nullable=False, default="[]")  # JSON array
    trust_score = Column(Float, nullable=True)  # 0-100, null if not computed
    created_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_agent_metrics_user_agent", "user_id", "agent_name"),
        Index("ix_agent_metrics_created", "created_at"),
    )


class TrustScore(Base):
    """Agent Trust Score history entry (Elite feature)."""

    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    agent_name = Column(String(256), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    # JSON: {policy_compliance, anomaly_frequency, data_pattern, behavioral_stability}
    components = Column(Text, nullable=False, default="{}")
    created_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_trust_scores_user_agent", "user_id", "agent_name"),
        Index("ix_trust_scores_created", "created_at"),
    )


class AnomalyTrend(Base):
    """Pre-aggregated anomaly trend data for time-series analytics."""

    __tablename__ = "anomaly_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    agent_name = Column(String(256), nullable=True)  # NULL = global aggregate
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_events = Column(Integer, nullable=False, default=0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    anomaly_rate = Column(Float, nullable=False, default=0.0)
    severity_breakdown = Column(Text, nullable=False, default="{}")  # JSON
    created_at = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.utcnow,
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_anomaly_trends_user_period", "user_id", "period_start"),)
