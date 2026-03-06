"""Tests for the 6 new SAFE-MCP anomaly detectors."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from navil.anomaly_detector import BehavioralAnomalyDetector


@pytest.fixture
def detector() -> BehavioralAnomalyDetector:
    return BehavioralAnomalyDetector()


class TestReconnaissance:
    """RECONNAISSANCE — excessive tools/list probing."""

    def test_no_alert_below_threshold(self, detector: BehavioralAnomalyDetector) -> None:
        """5 or fewer tools/list calls should not trigger an alert."""
        for _ in range(5):
            detector.record_invocation(
                agent_name="agent-a",
                tool_name="__tools_list__",
                action="tools/list",
                duration_ms=10,
                is_list_tools=True,
            )
        recon_alerts = [a for a in detector.alerts if a.anomaly_type == "RECONNAISSANCE"]
        assert len(recon_alerts) == 0

    def test_alert_above_threshold(self, detector: BehavioralAnomalyDetector) -> None:
        """More than 5 tools/list calls in 10 min should trigger RECONNAISSANCE alert."""
        for _ in range(7):
            detector.record_invocation(
                agent_name="agent-a",
                tool_name="__tools_list__",
                action="tools/list",
                duration_ms=10,
                is_list_tools=True,
            )
        recon_alerts = [a for a in detector.alerts if a.anomaly_type == "RECONNAISSANCE"]
        assert len(recon_alerts) >= 1
        assert recon_alerts[0].severity == "MEDIUM"
        assert recon_alerts[0].agent_name == "agent-a"


class TestPersistence:
    """PERSISTENCE — bot-like periodic reconnection patterns."""

    def test_regular_interval_detected(self, detector: BehavioralAnomalyDetector) -> None:
        """Regular 30s intervals should trigger PERSISTENCE alert."""
        from navil.anomaly_detector import ToolInvocation

        base = datetime.now(timezone.utc) - timedelta(minutes=10)
        for i in range(8):
            ts = base + timedelta(seconds=i * 30)
            detector.invocations.append(
                ToolInvocation(
                    timestamp=ts.isoformat(),
                    agent_name="agent-b",
                    tool_name="heartbeat",
                    action="ping",
                    duration_ms=5,
                    data_accessed_bytes=0,
                    success=True,
                )
            )

        detector._detect_persistence("agent-b")
        persist_alerts = [a for a in detector.alerts if a.anomaly_type == "PERSISTENCE"]
        assert len(persist_alerts) >= 1
        assert persist_alerts[0].severity == "HIGH"

    def test_irregular_interval_no_alert(self, detector: BehavioralAnomalyDetector) -> None:
        """Irregular intervals should NOT trigger PERSISTENCE alert."""
        from navil.anomaly_detector import ToolInvocation

        base = datetime.now(timezone.utc) - timedelta(minutes=10)
        intervals = [0, 5, 23, 8, 45, 12, 3]
        cumulative = 0
        for dt in intervals:
            cumulative += dt
            ts = base + timedelta(seconds=cumulative)
            detector.invocations.append(
                ToolInvocation(
                    timestamp=ts.isoformat(),
                    agent_name="agent-c",
                    tool_name="work",
                    action="do",
                    duration_ms=100,
                    data_accessed_bytes=0,
                    success=True,
                )
            )

        detector._detect_persistence("agent-c")
        persist_alerts = [a for a in detector.alerts if a.anomaly_type == "PERSISTENCE"]
        assert len(persist_alerts) == 0


class TestDefenseEvasion:
    """DEFENSE_EVASION — encoding tricks and prompt injection."""

    def test_large_arguments_flagged(self, detector: BehavioralAnomalyDetector) -> None:
        """Arguments larger than 5000 bytes should trigger DEFENSE_EVASION."""
        detector.record_invocation(
            agent_name="agent-d",
            tool_name="execute",
            action="run",
            duration_ms=100,
            arguments_size_bytes=6000,
        )
        evasion_alerts = [a for a in detector.alerts if a.anomaly_type == "DEFENSE_EVASION"]
        assert len(evasion_alerts) >= 1
        assert evasion_alerts[0].severity == "HIGH"

    def test_normal_arguments_no_alert(self, detector: BehavioralAnomalyDetector) -> None:
        """Normal argument sizes should not trigger DEFENSE_EVASION."""
        detector.record_invocation(
            agent_name="agent-e",
            tool_name="read",
            action="get",
            duration_ms=50,
            arguments_size_bytes=200,
        )
        evasion_alerts = [a for a in detector.alerts if a.anomaly_type == "DEFENSE_EVASION"]
        assert len(evasion_alerts) == 0


class TestLateralMovement:
    """LATERAL_MOVEMENT — cross-server tool chaining."""

    def test_multiple_servers_flagged(self, detector: BehavioralAnomalyDetector) -> None:
        """Talking to >3 MCP servers in 5 min should trigger LATERAL_MOVEMENT."""
        servers = [
            "http://server-1:3000",
            "http://server-2:3000",
            "http://server-3:3000",
            "http://server-4:3000",
        ]
        for server in servers:
            detector.record_invocation(
                agent_name="agent-f",
                tool_name="query",
                action="tools/call",
                duration_ms=50,
                target_server=server,
            )
        lateral_alerts = [a for a in detector.alerts if a.anomaly_type == "LATERAL_MOVEMENT"]
        assert len(lateral_alerts) >= 1
        assert lateral_alerts[0].severity == "HIGH"

    def test_single_server_no_alert(self, detector: BehavioralAnomalyDetector) -> None:
        """Talking to a single server should not trigger LATERAL_MOVEMENT."""
        for _ in range(5):
            detector.record_invocation(
                agent_name="agent-g",
                tool_name="query",
                action="tools/call",
                duration_ms=50,
                target_server="http://server-1:3000",
            )
        lateral_alerts = [a for a in detector.alerts if a.anomaly_type == "LATERAL_MOVEMENT"]
        assert len(lateral_alerts) == 0


class TestCommandAndControl:
    """COMMAND_AND_CONTROL — beaconing patterns."""

    def test_beaconing_detected(self, detector: BehavioralAnomalyDetector) -> None:
        """Regular intervals with small consistent responses = beaconing."""
        from navil.anomaly_detector import ToolInvocation

        base = datetime.now(timezone.utc) - timedelta(minutes=5)
        for i in range(8):
            ts = base + timedelta(seconds=i * 10)
            detector.invocations.append(
                ToolInvocation(
                    timestamp=ts.isoformat(),
                    agent_name="agent-h",
                    tool_name="status",
                    action="check",
                    duration_ms=20,
                    data_accessed_bytes=0,
                    success=True,
                    response_size_bytes=256,  # Small, consistent
                )
            )

        detector._detect_command_and_control("agent-h")
        c2_alerts = [a for a in detector.alerts if a.anomaly_type == "COMMAND_AND_CONTROL"]
        assert len(c2_alerts) >= 1
        assert c2_alerts[0].severity == "CRITICAL"


class TestSupplyChain:
    """SUPPLY_CHAIN — unknown/tampered tool registration."""

    def test_unknown_tool_flagged(self, detector: BehavioralAnomalyDetector) -> None:
        """Calling a tool not in registered tools/list should trigger SUPPLY_CHAIN."""
        server = "http://mcp-server:3000"
        detector.register_server_tools(server, ["read", "write", "list"])

        detector.record_invocation(
            agent_name="agent-i",
            tool_name="inject_backdoor",  # Not in registered tools
            action="tools/call",
            duration_ms=100,
            target_server=server,
        )

        supply_alerts = [a for a in detector.alerts if a.anomaly_type == "SUPPLY_CHAIN"]
        assert len(supply_alerts) >= 1
        assert supply_alerts[0].severity == "CRITICAL"
        assert "inject_backdoor" in supply_alerts[0].description

    def test_known_tool_no_alert(self, detector: BehavioralAnomalyDetector) -> None:
        """Calling a known registered tool should not trigger SUPPLY_CHAIN."""
        server = "http://mcp-server:3000"
        detector.register_server_tools(server, ["read", "write", "list"])

        detector.record_invocation(
            agent_name="agent-j",
            tool_name="read",  # Known tool
            action="tools/call",
            duration_ms=100,
            target_server=server,
        )

        supply_alerts = [a for a in detector.alerts if a.anomaly_type == "SUPPLY_CHAIN"]
        assert len(supply_alerts) == 0

    def test_unregistered_server_no_alert(self, detector: BehavioralAnomalyDetector) -> None:
        """Calling a tool on an unregistered server should not trigger SUPPLY_CHAIN."""
        detector.record_invocation(
            agent_name="agent-k",
            tool_name="unknown_tool",
            action="tools/call",
            duration_ms=100,
            target_server="http://new-server:3000",  # Not registered
        )

        supply_alerts = [a for a in detector.alerts if a.anomaly_type == "SUPPLY_CHAIN"]
        assert len(supply_alerts) == 0


class TestRegisterServerTools:
    """Test the register_server_tools helper."""

    def test_register_and_retrieve(self, detector: BehavioralAnomalyDetector) -> None:
        detector.register_server_tools("http://s1:3000", ["tool_a", "tool_b"])
        assert "http://s1:3000" in detector.registered_tools
        assert detector.registered_tools["http://s1:3000"] == {"tool_a", "tool_b"}

    def test_overwrites_existing(self, detector: BehavioralAnomalyDetector) -> None:
        detector.register_server_tools("http://s1:3000", ["tool_a"])
        detector.register_server_tools("http://s1:3000", ["tool_b", "tool_c"])
        assert detector.registered_tools["http://s1:3000"] == {"tool_b", "tool_c"}
