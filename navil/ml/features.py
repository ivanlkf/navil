"""Feature extraction pipeline: ToolInvocation -> numpy feature vectors."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from navil._compat import require_ml
from navil.anomaly_detector import ToolInvocation


class FeatureExtractor:
    """Extracts numerical features from ToolInvocation sequences for ML models.

    Produces a 15-dimensional feature vector per invocation including
    temporal features, windowed aggregates, and encoded categorical variables.
    """

    FEATURE_NAMES = [
        "duration_ms",
        "data_accessed_bytes",
        "success_flag",
        "hour_of_day",
        "minute_of_hour",
        "is_weekend",
        "tool_index",
        "action_index",
        "invocations_last_5min",
        "invocations_last_30min",
        "unique_tools_last_30min",
        "data_volume_last_30min",
        "avg_duration_last_10",
        "std_duration_last_10",
        "success_rate_last_10",
    ]

    def __init__(self) -> None:
        require_ml("Feature extraction")
        self.tool_encoder: dict[str, int] = {}
        self.action_encoder: dict[str, int] = {}
        self._next_tool_id = 0
        self._next_action_id = 0

    def extract_single(
        self, invocation: ToolInvocation, history: list[ToolInvocation]
    ) -> list[float]:
        """Extract feature vector from a single invocation + recent history."""
        import numpy as np

        ts = datetime.fromisoformat(invocation.timestamp)

        tool_idx = self._encode_tool(invocation.tool_name)
        action_idx = self._encode_action(invocation.action)

        hour = ts.hour
        minute = ts.minute
        is_weekend = 1.0 if ts.weekday() >= 5 else 0.0

        recent_5 = self._filter_recent(history, invocation.agent_name, minutes=5)
        recent_30 = self._filter_recent(history, invocation.agent_name, minutes=30)
        recent_10 = [h for h in history if h.agent_name == invocation.agent_name][-10:]

        features = [
            float(invocation.duration_ms),
            float(invocation.data_accessed_bytes),
            1.0 if invocation.success else 0.0,
            float(hour),
            float(minute),
            is_weekend,
            float(tool_idx),
            float(action_idx),
            float(len(recent_5)),
            float(len(recent_30)),
            float(len({h.tool_name for h in recent_30})),
            float(sum(h.data_accessed_bytes for h in recent_30)),
            float(np.mean([h.duration_ms for h in recent_10])) if recent_10 else 0.0,
            float(np.std([h.duration_ms for h in recent_10])) if len(recent_10) > 1 else 0.0,
            float(sum(1 for h in recent_10 if h.success) / len(recent_10)) if recent_10 else 1.0,
        ]

        return features

    def extract_batch(self, invocations: list[ToolInvocation]) -> Any:
        """Extract feature matrix from a sequence of invocations.

        Returns:
            numpy.ndarray of shape (n_invocations, 15)
        """
        import numpy as np

        features = []
        for i, inv in enumerate(invocations):
            history = invocations[:i]
            features.append(self.extract_single(inv, history))
        return np.array(features)

    def _encode_tool(self, tool_name: str) -> int:
        if tool_name not in self.tool_encoder:
            self.tool_encoder[tool_name] = self._next_tool_id
            self._next_tool_id += 1
        return self.tool_encoder[tool_name]

    def _encode_action(self, action: str) -> int:
        if action not in self.action_encoder:
            self.action_encoder[action] = self._next_action_id
            self._next_action_id += 1
        return self.action_encoder[action]

    def _filter_recent(
        self, history: list[ToolInvocation], agent_name: str, minutes: int
    ) -> list[ToolInvocation]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            h
            for h in history
            if h.agent_name == agent_name and datetime.fromisoformat(h.timestamp) > cutoff
        ]
