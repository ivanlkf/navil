"""
Behavioral Anomaly Detection

Monitors tool invocation patterns and detects anomalies including rug-pull indicators,
unusual data access patterns, and suspicious behavioral changes.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of detected anomalies."""

    RUG_PULL = "RUG_PULL"  # Sudden behavior change
    DATA_EXFILTRATION = "DATA_EXFILTRATION"  # Unusual data access
    RATE_SPIKE = "RATE_SPIKE"  # Sudden increase in calls
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"  # Accessing higher privilege tools
    GEOGRAPHIC_ANOMALY = "GEOGRAPHIC_ANOMALY"  # Access from unusual location
    TIME_ANOMALY = "TIME_ANOMALY"  # Access at unusual time


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
    location: Optional[str] = None


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

    def __init__(self, baseline_window_hours: int = 24) -> None:
        """
        Initialize anomaly detector.

        Args:
            baseline_window_hours: Hours of historical data to use for baseline
        """
        self.baseline_window_hours = baseline_window_hours
        self.invocations: list[ToolInvocation] = []
        self.alerts: list[AnomalyAlert] = []
        self.baselines: dict[str, dict[str, Any]] = {}

    def record_invocation(
        self,
        agent_name: str,
        tool_name: str,
        action: str,
        duration_ms: int,
        data_accessed_bytes: int = 0,
        success: bool = True,
        location: str | None = None,
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
        )

        self.invocations.append(invocation)

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

    def _build_baseline(self, agent_name: str) -> None:
        """Build behavioral baseline for agent."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.baseline_window_hours)

        agent_invocations = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
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
            f"Built baseline for agent {agent_name}: "
            f"{baseline['invocation_count']} invocations"
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
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
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
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
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
                recommended_action="Immediately review data access and revoke credentials if unauthorized",
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
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
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
            tool
            for tool in baseline.get("common_tools", [])
            if tool[0] in sensitive_tools
        ]

        # If accessing new sensitive tools
        if recent and not baseline_sensitive:
            self._create_alert(
                anomaly_type=AnomalyType.PRIVILEGE_ESCALATION,
                severity="CRITICAL",
                agent_name=agent_name,
                description="Agent accessing sensitive administrative tools without baseline history",
                evidence=[
                    f"Sensitive tools accessed: {[inv.tool_name for inv in recent]}"
                ],
                recommended_action="Immediately review and revoke access if unauthorized",
            )

    def _detect_time_anomaly(self, agent_name: str) -> None:
        """Detect access at unusual times."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = [
            inv
            for inv in self.invocations
            if inv.agent_name == agent_name
            and datetime.fromisoformat(inv.timestamp) > cutoff_time
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
        logger.warning(
            f"ANOMALY DETECTED: {alert.anomaly_type} for {agent_name} - {description}"
        )

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
