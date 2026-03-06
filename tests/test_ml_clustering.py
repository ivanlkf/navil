"""Tests for agent behavior clustering (requires scikit-learn)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

sklearn = pytest.importorskip("sklearn")

from navil.anomaly_detector import ToolInvocation
from navil.ml.clustering import AgentClusterer


def _make_agent_invocations(
    agent: str, tool: str, n: int, duration: int = 50, data: int = 100
) -> list[ToolInvocation]:
    return [
        ToolInvocation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent,
            tool_name=tool,
            action="read",
            duration_ms=duration,
            data_accessed_bytes=data,
            success=True,
        )
        for _ in range(n)
    ]


class TestAgentClusterer:
    def test_cluster_two_groups(self) -> None:
        clusterer = AgentClusterer(n_clusters=2)
        profiles = {
            "reader-1": _make_agent_invocations("reader-1", "logs", 20, duration=10, data=50),
            "reader-2": _make_agent_invocations("reader-2", "logs", 20, duration=15, data=60),
            "admin-1": _make_agent_invocations(
                "admin-1", "admin_panel", 20, duration=500, data=10000
            ),
            "admin-2": _make_agent_invocations(
                "admin-2", "admin_panel", 20, duration=600, data=12000
            ),
        }
        result = clusterer.fit(profiles)
        assert result["n_clusters"] == 2
        # Readers should be in same cluster, admins in another
        assert result["assignments"]["reader-1"] == result["assignments"]["reader-2"]
        assert result["assignments"]["admin-1"] == result["assignments"]["admin-2"]
        assert result["assignments"]["reader-1"] != result["assignments"]["admin-1"]

    def test_cluster_single_agent(self) -> None:
        clusterer = AgentClusterer(n_clusters=3)
        profiles = {
            "agent-a": _make_agent_invocations("agent-a", "logs", 10),
        }
        result = clusterer.fit(profiles)
        assert result["n_clusters"] == 1  # Can't have more clusters than agents
        assert "agent-a" in result["assignments"]

    def test_cluster_assignments_complete(self) -> None:
        clusterer = AgentClusterer(n_clusters=2)
        profiles = {
            f"agent-{i}": _make_agent_invocations(f"agent-{i}", "logs", 10) for i in range(5)
        }
        result = clusterer.fit(profiles)
        assert len(result["assignments"]) == 5

    def test_empty_invocations_handled(self) -> None:
        clusterer = AgentClusterer(n_clusters=2)
        profiles = {
            "agent-a": _make_agent_invocations("agent-a", "logs", 10),
            "agent-b": [],
        }
        result = clusterer.fit(profiles)
        assert len(result["assignments"]) == 2
