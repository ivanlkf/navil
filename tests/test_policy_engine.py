"""Tests for the PolicyEngine module."""

from __future__ import annotations

import pytest

from navil.policy_engine import PolicyDecision, PolicyEngine


@pytest.fixture
def engine(policy_file: str) -> PolicyEngine:
    """PolicyEngine loaded from the sample policy fixture."""
    return PolicyEngine(policy_file=policy_file)


def test_tool_allowed_for_agent(engine: PolicyEngine) -> None:
    """Reader agent should be allowed to use logs tool."""
    allowed, reason = engine.check_tool_call("reader", "logs", "read")
    assert allowed is True


def test_tool_denied_for_agent(engine: PolicyEngine) -> None:
    """Reader agent should be denied access to admin_panel."""
    allowed, reason = engine.check_tool_call("reader", "admin_panel", "read")
    assert allowed is False
    assert "not allowed" in reason.lower()


def test_action_denied_by_tool_policy(engine: PolicyEngine) -> None:
    """Delete action should be denied on logs (only read/export allowed)."""
    allowed, reason = engine.check_tool_call("reader", "logs", "delete")
    assert allowed is False


def test_action_allowed(engine: PolicyEngine) -> None:
    """Admin agent should be allowed to read logs."""
    allowed, reason = engine.check_tool_call("admin", "logs", "read")
    assert allowed is True


def test_rate_limit_exceeded(engine: PolicyEngine) -> None:
    """Exceed the rate limit (reader: 10/hour) and verify denial."""
    for _ in range(10):
        engine.check_tool_call("reader", "logs", "read")
    allowed, reason = engine.check_tool_call("reader", "logs", "read")
    assert allowed is False
    assert "rate limit" in reason.lower()


def test_data_sensitivity_denied(engine: PolicyEngine) -> None:
    """Reader (INTERNAL clearance) should be denied RESTRICTED data."""
    allowed, reason = engine.check_tool_call(
        "reader", "logs", "read", data_sensitivity="RESTRICTED"
    )
    assert allowed is False
    assert "authorized" in reason.lower()


def test_data_sensitivity_allowed(engine: PolicyEngine) -> None:
    """Admin (RESTRICTED clearance) should be allowed RESTRICTED data."""
    allowed, reason = engine.check_tool_call("admin", "logs", "read", data_sensitivity="RESTRICTED")
    assert allowed is True


def test_suspicious_pattern_still_allows(engine: PolicyEngine) -> None:
    """Suspicious patterns log an ALERT but still return True."""
    allowed, reason = engine.check_tool_call("admin", "logs", "export")
    assert allowed is True


def test_default_policy_fallback(tmp_path) -> None:
    """When policy file doesn't exist, engine uses defaults."""
    engine = PolicyEngine(policy_file=str(tmp_path / "nonexistent.yaml"))
    allowed, reason = engine.check_tool_call("default", "file_system", "read")
    assert allowed is True


def test_decisions_log_populated(engine: PolicyEngine) -> None:
    """Decisions log should be populated after a check."""
    engine.check_tool_call("reader", "logs", "read")
    decisions = engine.get_decisions_log()
    assert len(decisions) >= 1
    assert decisions[-1]["decision"] == PolicyDecision.ALLOW.value
