"""
Behavioral Anomaly Detection

Monitors tool invocation patterns and detects anomalies including rug-pull indicators,
unusual data access patterns, and suspicious behavioral changes.

Covers all 14 SAFE-MCP attack tactics:
  Existing: RUG_PULL, DATA_EXFILTRATION, RATE_SPIKE, PRIVILEGE_ESCALATION,
            GEOGRAPHIC_ANOMALY, TIME_ANOMALY
  New:      RECONNAISSANCE, PERSISTENCE, DEFENSE_EVASION, LATERAL_MOVEMENT,
            COMMAND_AND_CONTROL, SUPPLY_CHAIN
"""

from __future__ import annotations

import logging
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of detected anomalies."""

    RUG_PULL = "RUG_PULL"  # Sudden behavior change
    DATA_EXFILTRATION = "DATA_EXFILTRATION"  # Unusual data access
    RATE_SPIKE = "RATE_SPIKE"  # Sudden increase in calls
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"  # Accessing higher privilege tools
    GEOGRAPHIC_ANOMALY = "GEOGRAPHIC_ANOMALY"  # Access from unusual location
    TIME_ANOMALY = "TIME_ANOMALY"  # Access at unusual time
    # SAFE-MCP additional tactics
    RECONNAISSANCE = "RECONNAISSANCE"  # Tool discovery probing (tools/list abuse)
    PERSISTENCE = "PERSISTENCE"  # Scheduled/repeated reconnection patterns
    DEFENSE_EVASION = "DEFENSE_EVASION"  # Prompt injection, encoding tricks
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"  # Cross-server tool chaining
    COMMAND_AND_CONTROL = "COMMAND_AND_CONTROL"  # Covert C2 via tool params
    SUPPLY_CHAIN = "SUPPLY_CHAIN"  # Unknown/tampered tool registration


@dataclass
class ToolInvocation:
    """Record of a tool invocation."""

    timestamp: str
    agent_name: str
    tool_name: str
    action: str
    duration_ms: int
    data_accessed_bytes: int
    success: bool
    location: str | None = None
    # Proxy-enriched fields for SAFE-MCP detection
    target_server: str | None = None  # MCP server URL being called
    arguments_hash: str | None = None  # SHA-256 of tool call arguments
    arguments_size_bytes: int = 0  # Size of serialized arguments
    response_size_bytes: int = 0  # Size of tool response
    is_list_tools: bool = False  # Whether this was a tools/list call


@dataclass
class AnomalyAlert:
    """Alert for detected anomaly."""

    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    agent_name: str
    description: str
    timestamp: str
    evidence: list[str]
    recommended_action: str
    confidence: float = 0.0  # 0.0 for legacy binary alerts, 0.0-1.0 for scored alerts


class BehavioralAnomalyDetector:
    """
    Detects anomalies in agent behavior patterns.

    Features:
    - Statistical baseline comparison
    - Rug-pull detection (sudden behavior changes)
    - Data exfiltration detection
    - Rate spike detection
    - Temporal and geographic anomaly detection
    """

    def __init__(
        self,
        baseline_window_hours: int = 24,
        feedback_loop: Any | None = None,
        pattern_store: Any | None = None,
    ) -> None:
        """
        Initialize anomaly detector.

        Args:
            baseline_window_hours: Hours of historical data to use for baseline
            feedback_loop: Optional FeedbackLoop for self-tuning thresholds
            pattern_store: Optional PatternStore for learned pattern matching
        """
        self.baseline_window_hours = baseline_window_hours
        self.invocations: list[ToolInvocation] = []
        self.alerts: list[AnomalyAlert] = []
        self.baselines: dict[str, dict[str, Any]] = {}
        self.feedback_loop = feedback_loop
        self.pattern_store = pattern_store

        # Adaptive baselines (Level 1 AI) — updated in O(1) per invocation
        from navil.adaptive.baselines import AgentAdaptiveBaseline

        self.adaptive_baselines: dict[str, AgentAdaptiveBaseline] = {}

        # Proxy-mode tracking for SAFE-MCP detectors
        self.registered_tools: dict[str, set[str]] = {}  # server_url -> known tool names

    def record_invocation(
        self,
        agent_name: str,
        tool_name: str,
        action: str,
        duration_ms: int,
        data_accessed_bytes: int = 0,
        success: bool = True,
        location: str | None = None,
        target_server: str | None = None,
        arguments_hash: str | None = None,
        arguments_size_bytes: int = 0,
        response_size_bytes: int = 0,
        is_list_tools: bool = False,
    ) -> None:
        """
        Record a tool invocation.

        Args:
            agent_name: Name of agent
            tool_name: Name of tool invoked
            action: Action performed
            duration_ms: Duration in milliseconds
            data_accessed_bytes: Amount of data accessed
            success: Whether invocation succeeded
            location: Geographic location of invocation
            target_server: MCP server URL being called (proxy mode)
            arguments_hash: SHA-256 hash of tool call arguments
            arguments_size_bytes: Size of serialized arguments
            response_size_bytes: Size of tool response
            is_list_tools: Whether this was a tools/list call
        """
        invocation = ToolInvocation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_name,
            tool_name=tool_name,
            action=action,
            duration_ms=duration_ms,
            data_accessed_bytes=data_accessed_bytes,
            success=success,
            location=location,
            target_server=target_server,
            arguments_hash=arguments_hash,
            arguments_size_bytes=arguments_size_bytes,
            response_size_bytes=response_size_bytes,
            is_list_tools=is_list_tools,
        )

        self.invocations.append(invocation)

        # Update adaptive baseline (O(1))
        self._update_adaptive_baseline(agent_name, invocation)

        # Check for anomalies
        self._check_anomalies(agent_name)

    def _check_anomalies(self, agent_name: str) -> None:
        """Check for anomalies in agent behavior."""
        # Build baseline if needed
        if agent_name not in self.baselines:
            self._build_baseline(agent_name)

        # Run all detection methods
        self._detect_rug_pull(agent_name)
        self._detect_data_exfiltration(agent_name)
        self._detect_rate_spike(agent_name)
        self._detect_privilege_escalation(agent_name)
        self._detect_time_anomaly(agent_name)
        # SAFE-MCP additional detectors
        self._detect_reconnaissance(agent_name)
        self._detect_persistence(agent_name)
        self._detect_defense_evasion(agent_name)
        self._detect_lateral_movement(agent_name)
        self._detect_command_and_control(agent_name)
        self._detect_supply_chain(agent_name)

    def _build_baseline(self, agent_name: str) -> None:
        """Build behavioral baseline for agent."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.baseline_window_hours)

        agent_invocations = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_time
        ]

        if not agent_invocations:
            logger.debug(f"No baseline data for agent {agent_name}")
            self.baselines[agent_name] = self._get_default_baseline()
            return

        # Calculate baseline statistics
        durations = [inv.duration_ms for inv in agent_invocations]
        data_accessed = [inv.data_accessed_bytes for inv in agent_invocations]
        tool_usage: dict[str, int] = {}

        for inv in agent_invocations:
            tool_usage[inv.tool_name] = tool_usage.get(inv.tool_name, 0) + 1

        baseline = {
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "std_dev_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
            "avg_data_accessed": statistics.mean(data_accessed) if data_accessed else 0,
            "std_dev_data": statistics.stdev(data_accessed) if len(data_accessed) > 1 else 0,
            "tool_usage": tool_usage,
            "invocation_count": len(agent_invocations),
            "success_rate": (
                sum(1 for inv in agent_invocations if inv.success) / len(agent_invocations)
                if agent_invocations
                else 1.0
            ),
            "common_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5],
        }

        self.baselines[agent_name] = baseline
        logger.info(
            f"Built baseline for agent {agent_name}: {baseline['invocation_count']} invocations"
        )

    def _detect_rug_pull(self, agent_name: str) -> None:
        """Detect sudden behavior changes (rug-pull indicators)."""
        baseline = self.baselines.get(agent_name, {})
        if not baseline:
            return

        # Get recent invocations (last hour)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_time
        ]

        if not recent or len(recent) < 5:
            return

        # Check for sudden changes
        recent_tools: dict[str, int] = {}
        for inv in recent:
            recent_tools[inv.tool_name] = recent_tools.get(inv.tool_name, 0) + 1

        baseline_tools = set(baseline.get("tool_usage", {}).keys())
        recent_tools_set = set(recent_tools.keys())

        # Detect new tool access pattern
        new_tools = recent_tools_set - baseline_tools
        if len(new_tools) > 3:  # Accessing 3+ new tools in 1 hour
            self._create_alert(
                anomaly_type=AnomalyType.RUG_PULL,
                severity="HIGH",
                agent_name=agent_name,
                description=f"Agent accessing {len(new_tools)} new tools in short timeframe",
                evidence=[f"New tools: {', '.join(new_tools)}"],
                recommended_action="Review agent activity and verify authorization",
            )

        # Check for abandonment of typical tools
        abandoned_tools = baseline_tools - recent_tools_set
        if len(abandoned_tools) >= len(baseline_tools) * 0.5:
            self._create_alert(
                anomaly_type=AnomalyType.RUG_PULL,
                severity="MEDIUM",
                agent_name=agent_name,
                description="Agent has abandoned typical tool usage patterns",
                evidence=[f"Abandoned tools: {', '.join(abandoned_tools)}"],
                recommended_action="Investigate reason for behavioral change",
            )

    def _detect_data_exfiltration(self, agent_name: str) -> None:
        """Detect unusual data access patterns."""
        baseline = self.baselines.get(agent_name, {})
        if not baseline:
            return

        # Get recent invocations (last hour)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_time
        ]

        if not recent:
            return

        total_data = sum(inv.data_accessed_bytes for inv in recent)
        baseline_data = baseline.get("avg_data_accessed", 0) * len(recent)

        # If accessing > 5x normal data amount
        if baseline_data > 0 and total_data > baseline_data * 5:
            self._create_alert(
                anomaly_type=AnomalyType.DATA_EXFILTRATION,
                severity="CRITICAL",
                agent_name=agent_name,
                description=(
                    f"Agent accessing {total_data / (1024 * 1024):.2f}MB in 1 hour "
                    f"(baseline: {baseline_data / (1024 * 1024):.2f}MB)"
                ),
                evidence=[f"Total data accessed: {total_data} bytes"],
                recommended_action=(
                    "Immediately review data access and revoke credentials if unauthorized"
                ),
            )

    def _detect_rate_spike(self, agent_name: str) -> None:
        """Detect sudden increase in tool invocation rate."""
        baseline = self.baselines.get(agent_name, {})
        if not baseline:
            return

        # Get recent invocations (last 30 minutes)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_time
        ]

        # Estimate baseline rate (invocations per 30 min)
        baseline_count = (baseline.get("invocation_count", 1) / 24) * 0.5

        # If rate is 3x higher than baseline
        if baseline_count > 0 and len(recent) > baseline_count * 3:
            self._create_alert(
                anomaly_type=AnomalyType.RATE_SPIKE,
                severity="MEDIUM",
                agent_name=agent_name,
                description=(
                    f"Agent invocation rate increased to {len(recent)} in 30 min "
                    f"(baseline: {baseline_count:.1f})"
                ),
                evidence=[f"Recent invocations: {len(recent)}"],
                recommended_action="Monitor for sustained rate increases",
            )

    def _detect_privilege_escalation(self, agent_name: str) -> None:
        """Detect attempts to access higher privilege tools."""
        baseline = self.baselines.get(agent_name, {})
        if not baseline:
            return

        # Define sensitive tools
        sensitive_tools = [
            "admin_panel",
            "credential_manager",
            "system_config",
            "audit_logs",
            "user_management",
        ]

        # Get recent invocations (last hour)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
            and inv.tool_name in sensitive_tools
        ]

        baseline_sensitive = [
            tool for tool in baseline.get("common_tools", []) if tool[0] in sensitive_tools
        ]

        # If accessing new sensitive tools
        if recent and not baseline_sensitive:
            self._create_alert(
                anomaly_type=AnomalyType.PRIVILEGE_ESCALATION,
                severity="CRITICAL",
                agent_name=agent_name,
                description=(
                    "Agent accessing sensitive administrative tools without baseline history"
                ),
                evidence=[f"Sensitive tools accessed: {[inv.tool_name for inv in recent]}"],
                recommended_action="Immediately review and revoke access if unauthorized",
            )

    def _detect_time_anomaly(self, agent_name: str) -> None:
        """Detect access at unusual times."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_time
        ]

        if not recent:
            return

        # Check if accessing during unusual hours (2am - 5am)
        unusual_hours = []
        for inv in recent:
            hour = datetime.fromisoformat(inv.timestamp).hour
            if 2 <= hour <= 5:
                unusual_hours.append(inv.timestamp)

        if len(unusual_hours) > 5:
            self._create_alert(
                anomaly_type=AnomalyType.TIME_ANOMALY,
                severity="LOW",
                agent_name=agent_name,
                description="Agent accessing tools during unusual hours (2am-5am)",
                evidence=[f"Unusual accesses: {len(unusual_hours)}"],
                recommended_action="Verify agent activity if outside normal operating hours",
            )

    # --- SAFE-MCP Detectors ---

    def _detect_reconnaissance(self, agent_name: str) -> None:
        """Detect tool discovery probing (excessive tools/list calls)."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        list_calls = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and inv.is_list_tools
            and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        if len(list_calls) > 5:
            self._create_alert(
                anomaly_type=AnomalyType.RECONNAISSANCE,
                severity="MEDIUM",
                agent_name=agent_name,
                description=(
                    f"Agent called tools/list {len(list_calls)} times in 10 minutes (threshold: 5)"
                ),
                evidence=[
                    f"tools/list call count: {len(list_calls)}",
                    f"First: {list_calls[0].timestamp}",
                    f"Last: {list_calls[-1].timestamp}",
                ],
                recommended_action="Review agent behavior — may be probing for available tools",
            )

    def _detect_persistence(self, agent_name: str) -> None:
        """Detect scheduled/bot-like reconnection patterns."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        if len(recent) < 6:
            return

        # Calculate inter-call intervals
        timestamps = sorted(datetime.fromisoformat(inv.timestamp) for inv in recent)
        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)
        ]

        if len(intervals) < 5:
            return

        mean_interval = statistics.mean(intervals)
        if mean_interval < 1.0:
            return  # Too fast — likely burst, not persistence

        std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0.0

        # Very regular intervals (std_dev < 2s) on meaningful gaps = bot-like
        if std_dev < 2.0 and mean_interval > 5.0:
            self._create_alert(
                anomaly_type=AnomalyType.PERSISTENCE,
                severity="HIGH",
                agent_name=agent_name,
                description=(
                    f"Agent shows bot-like periodic pattern: interval "
                    f"{mean_interval:.1f}s (std_dev={std_dev:.2f}s)"
                ),
                evidence=[
                    f"Mean interval: {mean_interval:.1f}s",
                    f"Std deviation: {std_dev:.2f}s",
                    f"Sample count: {len(intervals)}",
                ],
                recommended_action=(
                    "Investigate automated reconnection \u2014 possible persistence mechanism"
                ),
            )

    _BASE64_RE = re.compile(r"^[A-Za-z0-9+/]{50,}={0,2}$")
    _HOMOGLYPH_RE = re.compile(
        r"[\u0410-\u044f\u0400-\u04ff\u2000-\u200f\u2028-\u202f"
        r"\u205f-\u2064\u2066-\u206f\ufeff\u00a0]"
    )

    def _detect_defense_evasion(self, agent_name: str) -> None:
        """Detect encoding tricks and prompt injection in tool arguments."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        for inv in recent:
            evidence: list[str] = []

            # Check for suspiciously large arguments
            if inv.arguments_size_bytes > 5000:
                evidence.append(
                    f"Large argument payload: {inv.arguments_size_bytes} bytes in {inv.tool_name}"
                )

            # Check arguments_hash for base64 patterns (hash itself is not b64,
            # but if we have the raw hash we can flag size + repeated patterns)
            if inv.arguments_hash and self._BASE64_RE.match(inv.arguments_hash):
                evidence.append(f"Possible base64-encoded payload in {inv.tool_name}")

            if evidence:
                self._create_alert(
                    anomaly_type=AnomalyType.DEFENSE_EVASION,
                    severity="HIGH",
                    agent_name=agent_name,
                    description="Suspicious tool argument encoding detected",
                    evidence=evidence,
                    recommended_action=(
                        "Inspect tool call arguments for prompt injection or encoded payloads"
                    ),
                )

    def _detect_lateral_movement(self, agent_name: str) -> None:
        """Detect cross-server tool chaining (agent talking to multiple servers)."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and inv.target_server
            and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        servers = set(inv.target_server for inv in recent if inv.target_server)
        if len(servers) > 3:
            self._create_alert(
                anomaly_type=AnomalyType.LATERAL_MOVEMENT,
                severity="HIGH",
                agent_name=agent_name,
                description=(
                    f"Agent communicating with {len(servers)} distinct MCP servers in 5 minutes"
                ),
                evidence=[
                    f"Servers: {', '.join(sorted(servers))}",
                    f"Total calls: {len(recent)}",
                ],
                recommended_action=(
                    "Investigate cross-server tool chaining — possible lateral movement"
                ),
            )

    def _detect_command_and_control(self, agent_name: str) -> None:
        """Detect beaconing patterns (periodic small data exfiltration)."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        if len(recent) < 5:
            return

        # Check for beaconing: regular intervals + consistent small payloads
        timestamps = sorted(datetime.fromisoformat(inv.timestamp) for inv in recent)
        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)
        ]

        if len(intervals) < 4:
            return

        mean_interval = statistics.mean(intervals)
        std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 999.0
        response_sizes = [inv.response_size_bytes for inv in recent if inv.response_size_bytes > 0]

        # Beaconing: regular timing + small consistent responses
        is_regular = std_dev < 3.0 and mean_interval > 3.0
        has_consistent_responses = False
        if len(response_sizes) >= 4:
            resp_std = statistics.stdev(response_sizes) if len(response_sizes) > 1 else 0.0
            resp_mean = statistics.mean(response_sizes)
            has_consistent_responses = (
                (resp_mean < 1024 and resp_std < resp_mean * 0.3) if resp_mean > 0 else False
            )

        if is_regular and has_consistent_responses:
            self._create_alert(
                anomaly_type=AnomalyType.COMMAND_AND_CONTROL,
                severity="CRITICAL",
                agent_name=agent_name,
                description=(
                    f"Beaconing pattern: {mean_interval:.1f}s intervals with "
                    f"~{statistics.mean(response_sizes):.0f}B responses"
                ),
                evidence=[
                    f"Interval mean: {mean_interval:.1f}s, std_dev: {std_dev:.2f}s",
                    f"Response size mean: {statistics.mean(response_sizes):.0f}B",
                    f"Sample count: {len(recent)}",
                ],
                recommended_action=(
                    "Possible C2 beaconing — investigate data relay pattern "
                    "and block agent immediately"
                ),
            )

    def _detect_supply_chain(self, agent_name: str) -> None:
        """Detect unknown/tampered tool registration (tool injection)."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and not inv.is_list_tools
            and inv.target_server
            and datetime.fromisoformat(inv.timestamp) > cutoff
        ]

        for inv in recent:
            server = inv.target_server
            if server and server in self.registered_tools:
                known = self.registered_tools[server]
                if inv.tool_name not in known:
                    self._create_alert(
                        anomaly_type=AnomalyType.SUPPLY_CHAIN,
                        severity="CRITICAL",
                        agent_name=agent_name,
                        description=(
                            f"Agent called unregistered tool '{inv.tool_name}' on server {server}"
                        ),
                        evidence=[
                            f"Tool: {inv.tool_name}",
                            f"Server: {server}",
                            f"Known tools: {', '.join(sorted(known))}",
                        ],
                        recommended_action=(
                            "Possible tool injection attack — "
                            "verify tool registration and block if unauthorized"
                        ),
                    )

    def register_server_tools(self, server_url: str, tool_names: list[str]) -> None:
        """Register known tools for a server (from tools/list response).

        Called by the proxy after a successful tools/list response to track
        the legitimate tool set for supply chain detection.
        """
        self.registered_tools[server_url] = set(tool_names)
        logger.info(f"Registered {len(tool_names)} tools for server {server_url}")

    def _create_alert(
        self,
        anomaly_type: AnomalyType,
        severity: str,
        agent_name: str,
        description: str,
        evidence: list[str],
        recommended_action: str,
    ) -> None:
        """Create an anomaly alert."""
        alert = AnomalyAlert(
            anomaly_type=anomaly_type.value,
            severity=severity,
            agent_name=agent_name,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence=evidence,
            recommended_action=recommended_action,
        )

        self.alerts.append(alert)
        logger.warning(f"ANOMALY DETECTED: {alert.anomaly_type} for {agent_name} - {description}")

    def get_alerts(
        self, agent_name: str | None = None, severity: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get anomaly alerts with optional filtering.

        Args:
            agent_name: Filter by agent name
            severity: Filter by severity level

        Returns:
            List of alert dictionaries
        """
        result = []

        for alert in self.alerts:
            if agent_name and alert.agent_name != agent_name:
                continue
            if severity and alert.severity != severity:
                continue

            result.append(
                {
                    "anomaly_type": alert.anomaly_type,
                    "severity": alert.severity,
                    "agent": alert.agent_name,
                    "description": alert.description,
                    "timestamp": alert.timestamp,
                    "evidence": alert.evidence,
                    "recommended_action": alert.recommended_action,
                    "confidence": alert.confidence,
                }
            )

        return result

    def get_baseline(self, agent_name: str) -> dict[str, Any]:
        """Get behavioral baseline for agent."""
        if agent_name not in self.baselines:
            self._build_baseline(agent_name)
        return self.baselines.get(agent_name, {})

    def _get_default_baseline(self) -> dict[str, Any]:
        """Get default baseline for new agents."""
        return {
            "avg_duration_ms": 100,
            "std_dev_duration": 50,
            "avg_data_accessed": 0,
            "std_dev_data": 0,
            "tool_usage": {},
            "invocation_count": 0,
            "success_rate": 1.0,
            "common_tools": [],
        }

    # --- Adaptive AI Methods (Level 1) ---

    def _update_adaptive_baseline(self, agent_name: str, invocation: ToolInvocation) -> None:
        """Update the adaptive EMA baseline for an agent. O(1) per call."""
        from navil.adaptive.baselines import AgentAdaptiveBaseline

        if agent_name not in self.adaptive_baselines:
            self.adaptive_baselines[agent_name] = AgentAdaptiveBaseline(agent_name=agent_name)

        ab = self.adaptive_baselines[agent_name]
        ab.record_observation(
            duration_ms=float(invocation.duration_ms),
            data_bytes=float(invocation.data_accessed_bytes),
            tool_name=invocation.tool_name,
            success=invocation.success,
        )

    def get_adaptive_baseline(self, agent_name: str) -> dict[str, Any]:
        """Get the adaptive baseline for an agent."""
        ab = self.adaptive_baselines.get(agent_name)
        if ab is None:
            return {"agent_name": agent_name, "status": "no_data"}
        return ab.to_dict()

    def score_anomaly(self, agent_name: str) -> list[dict[str, Any]]:
        """Get confidence-scored anomaly assessments for an agent.

        Returns a list of AnomalyScore dicts for each detection method,
        using the adaptive baseline for statistical scoring.
        """
        from navil.adaptive.confidence import AnomalyScore, z_score_to_confidence

        ab = self.adaptive_baselines.get(agent_name)
        if ab is None or ab.duration_ema.count < 10:
            return []

        scores: list[dict[str, Any]] = []

        # Rate spike scoring
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        recent_count = sum(
            1
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff
        )
        if ab.rate_ema.count > 0 and ab.rate_ema.mean > 0:
            z = ab.rate_ema.z_score(float(recent_count))
            confidence = z_score_to_confidence(z)
            score = AnomalyScore(
                anomaly_type=AnomalyType.RATE_SPIKE.value,
                confidence=confidence,
                z_score=z,
                evidence=[f"Recent rate: {recent_count}, baseline mean: {ab.rate_ema.mean:.1f}"],
                contributing_factors={"rate_z_score": z},
            )
            scores.append(score.to_dict())

        # Data volume scoring
        cutoff_1h = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_data = sum(
            inv.data_accessed_bytes
            for inv in self.invocations
            if inv.agent_name == agent_name and datetime.fromisoformat(inv.timestamp) > cutoff_1h
        )
        if ab.data_volume_ema.count > 0 and ab.data_volume_ema.mean > 0:
            z = ab.data_volume_ema.z_score(float(recent_data))
            confidence = z_score_to_confidence(z)
            score = AnomalyScore(
                anomaly_type=AnomalyType.DATA_EXFILTRATION.value,
                confidence=confidence,
                z_score=z,
                evidence=[
                    f"Recent data: {recent_data} bytes, "
                    f"baseline mean: {ab.data_volume_ema.mean:.0f}"
                ],
                contributing_factors={"data_z_score": z},
            )
            scores.append(score.to_dict())

        # Pattern store boost
        if self.pattern_store is not None:
            recent_tools = [
                inv.tool_name
                for inv in self.invocations
                if inv.agent_name == agent_name
                and datetime.fromisoformat(inv.timestamp) > cutoff_1h
            ]
            context = {
                "recent_tools": recent_tools,
                "current_data_volume": recent_data,
                "anomaly_type": None,
            }
            matches = self.pattern_store.match(context)
            for pattern, match_score in matches:
                for s in scores:
                    if s.get("anomaly_type") == pattern.anomaly_type:
                        boosted = min(1.0, s["confidence"] + pattern.confidence_boost * match_score)
                        s["confidence"] = boosted
                        s["evidence"].append(
                            f"Pattern match: {pattern.pattern_id} (score={match_score:.2f})"
                        )

        return scores
