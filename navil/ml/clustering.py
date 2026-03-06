"""Agent behavior clustering for profile identification."""

from __future__ import annotations

import logging
from typing import Any

from navil._compat import require_ml
from navil.anomaly_detector import ToolInvocation

logger = logging.getLogger(__name__)


class AgentClusterer:
    """Clusters agents by behavioral similarity.

    Uses KMeans clustering on aggregate agent profiles to identify
    behavioral groups and detect outlier agents.
    """

    def __init__(self, n_clusters: int = 5) -> None:
        require_ml("Agent clustering")
        self.n_clusters = n_clusters
        self.is_fitted = False

    def fit(
        self, agent_profiles: dict[str, list[ToolInvocation]]
    ) -> dict[str, Any]:
        """Cluster agents based on their invocation profiles.

        Args:
            agent_profiles: Mapping of agent_name -> list of invocations

        Returns:
            Clustering results with agent -> cluster assignments
        """
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        agent_names = list(agent_profiles.keys())
        feature_vectors = []

        for agent_name in agent_names:
            invocations = agent_profiles[agent_name]
            feature_vectors.append(self._profile_features(invocations))

        X = np.array(feature_vectors)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        actual_clusters = min(self.n_clusters, len(agent_names))
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        self.is_fitted = True

        assignments = {
            name: int(label) for name, label in zip(agent_names, labels)
        }

        clusters: dict[int, list[str]] = {}
        for name, label in assignments.items():
            clusters.setdefault(label, []).append(name)

        return {
            "n_clusters": actual_clusters,
            "assignments": assignments,
            "clusters": clusters,
        }

    def _profile_features(
        self, invocations: list[ToolInvocation]
    ) -> list[float]:
        """Extract aggregate profile features for one agent."""
        import numpy as np

        if not invocations:
            return [0.0] * 8

        durations = [inv.duration_ms for inv in invocations]
        data_vols = [inv.data_accessed_bytes for inv in invocations]
        unique_tools = len({inv.tool_name for inv in invocations})
        success_rate = (
            sum(1 for inv in invocations if inv.success) / len(invocations)
        )

        return [
            float(np.mean(durations)),
            float(np.std(durations)) if len(durations) > 1 else 0.0,
            float(np.mean(data_vols)),
            float(np.max(data_vols)),
            float(unique_tools),
            float(len(invocations)),
            success_rate,
            float(unique_tools / max(len(invocations), 1)),
        ]
