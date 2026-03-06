"""Tests for the BehavioralAnomalyDetector module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from navil.anomaly_detector import AnomalyType, BehavioralAnomalyDetector


@pytest.fixture
def detector() -> BehavioralAnomalyDetector:
    return BehavioralAnomalyDetector(baseline_window_hours=24)


def test_record_invocation(detector: BehavioralAnomalyDetector) -> None:
    """Recording an invocation should add it to the list."""
    detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    assert len(detector.invocations) == 1


def test_baseline_builds_on_first_invocation(detector: BehavioralAnomalyDetector) -> None:
    """Baseline should be built on first invocation."""
    detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    baseline = detector.get_baseline("agent-a")
    assert "avg_duration_ms" in baseline


def test_default_baseline_for_new_agent(detector: BehavioralAnomalyDetector) -> None:
    """New agents should get a default baseline."""
    baseline = detector.get_baseline("agent-x")
    assert baseline["invocation_count"] == 0


def test_rug_pull_detection(detector: BehavioralAnomalyDetector) -> None:
    """Rug-pull: agent suddenly uses 4+ new tools."""
    # Build baseline with one tool
    for _ in range(10):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    # Force baseline rebuild
    detector._build_baseline("agent-a")
    # Now access many new tools rapidly
    for tool in [
        "admin_panel",
        "credential_manager",
        "system_config",
        "user_management",
        "secret_vault",
    ]:
        detector.record_invocation("agent-a", tool, "read", duration_ms=50)
    alerts = detector.get_alerts(agent_name="agent-a")
    rug_pull_alerts = [a for a in alerts if a["anomaly_type"] == AnomalyType.RUG_PULL.value]
    assert len(rug_pull_alerts) >= 1


def test_data_exfiltration_detection(detector: BehavioralAnomalyDetector) -> None:
    """Data exfiltration: accessing 5x normal data volume."""
    # Build baseline with small data access
    for _ in range(10):
        detector.record_invocation(
            "agent-a", "logs", "read", duration_ms=50, data_accessed_bytes=100
        )
    detector._build_baseline("agent-a")
    # Now access huge data
    for _ in range(10):
        detector.record_invocation(
            "agent-a", "logs", "read", duration_ms=50, data_accessed_bytes=10000
        )
    alerts = detector.get_alerts(agent_name="agent-a")
    exfil_alerts = [
        a for a in alerts if a["anomaly_type"] == AnomalyType.DATA_EXFILTRATION.value
    ]
    assert len(exfil_alerts) >= 1


def test_rate_spike_detection(detector: BehavioralAnomalyDetector) -> None:
    """Rate spike: 3x normal invocation rate in 30 minutes."""
    for _ in range(10):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    detector._build_baseline("agent-a")
    # Rapid burst
    for _ in range(50):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=10)
    alerts = detector.get_alerts(agent_name="agent-a")
    rate_alerts = [a for a in alerts if a["anomaly_type"] == AnomalyType.RATE_SPIKE.value]
    assert len(rate_alerts) >= 1


def test_privilege_escalation_detection(detector: BehavioralAnomalyDetector) -> None:
    """Accessing sensitive tools without baseline history should alert."""
    for _ in range(10):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    detector._build_baseline("agent-a")
    detector.record_invocation("agent-a", "admin_panel", "read", duration_ms=50)
    alerts = detector.get_alerts(agent_name="agent-a")
    priv_alerts = [
        a for a in alerts if a["anomaly_type"] == AnomalyType.PRIVILEGE_ESCALATION.value
    ]
    assert len(priv_alerts) >= 1


def test_alerts_filter_by_severity(detector: BehavioralAnomalyDetector) -> None:
    """Filter alerts by severity level."""
    for _ in range(10):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    detector._build_baseline("agent-a")
    detector.record_invocation("agent-a", "admin_panel", "read", duration_ms=50)
    critical = detector.get_alerts(severity="CRITICAL")
    assert all(a["severity"] == "CRITICAL" for a in critical)


def test_no_alerts_for_normal_behavior(detector: BehavioralAnomalyDetector) -> None:
    """Normal behavior should not generate alerts after baseline is established."""
    # Build baseline with invocations timestamped 2 hours ago (outside 30-min window)
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    with patch("navil.anomaly_detector.datetime") as mock_dt:
        mock_dt.now.return_value = old_time
        mock_dt.fromisoformat = datetime.fromisoformat
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        for _ in range(100):
            detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    detector._build_baseline("agent-a")
    detector.alerts.clear()

    # Now record a few normal invocations at current time — within baseline rate
    for _ in range(3):
        detector.record_invocation("agent-a", "logs", "read", duration_ms=50)
    alerts = detector.get_alerts(agent_name="agent-a")
    assert len(alerts) == 0
