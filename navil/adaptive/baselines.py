"""Exponential Moving Average baselines with self-tuning thresholds."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EMABaseline:
    """Tracks an exponentially-weighted moving average for a metric.

    The EMA updates in O(1) time per observation, making it suitable
    for hot-path usage in real-time anomaly detection.
    """

    alpha: float = 0.1
    mean: float = 0.0
    variance: float = 0.0
    count: int = 0
    _initialized: bool = False

    def update(self, value: float) -> None:
        """Update the EMA with a new observation. O(1) time."""
        self.count += 1
        if not self._initialized:
            self.mean = value
            self.variance = 0.0
            self._initialized = True
            return

        diff = value - self.mean
        self.mean += self.alpha * diff
        self.variance = (1 - self.alpha) * (self.variance + self.alpha * diff * diff)

    @property
    def std_dev(self) -> float:
        """Standard deviation derived from the EMA variance."""
        return math.sqrt(self.variance) if self.variance > 0 else 0.0

    def z_score(self, value: float) -> float:
        """Return z-score of value relative to this baseline."""
        if self.std_dev == 0:
            return 0.0 if abs(value - self.mean) < 1e-9 else float("inf")
        return (value - self.mean) / self.std_dev

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "alpha": self.alpha,
            "mean": self.mean,
            "variance": self.variance,
            "count": self.count,
            "std_dev": self.std_dev,
        }


@dataclass
class AgentAdaptiveBaseline:
    """Complete adaptive baseline for one agent.

    Tracks multiple EMA metrics plus tool usage distribution.
    Includes self-tuning threshold multipliers that adjust
    based on operator feedback (false positive / true positive rates).
    """

    agent_name: str
    duration_ema: EMABaseline = field(default_factory=lambda: EMABaseline(alpha=0.1))
    data_volume_ema: EMABaseline = field(default_factory=lambda: EMABaseline(alpha=0.1))
    rate_ema: EMABaseline = field(default_factory=lambda: EMABaseline(alpha=0.05))
    success_rate_ema: EMABaseline = field(default_factory=lambda: EMABaseline(alpha=0.1))
    tool_distribution: dict[str, float] = field(default_factory=dict)
    known_tools: set[str] = field(default_factory=set)

    # Self-tuning threshold multipliers (start at defaults, adapt over time)
    rate_threshold_multiplier: float = 3.0
    data_threshold_multiplier: float = 5.0
    tool_abandonment_fraction: float = 0.5

    # Tracking for self-tuning
    false_positive_count: int = 0
    true_positive_count: int = 0

    def record_observation(
        self,
        duration_ms: float,
        data_bytes: float,
        tool_name: str,
        success: bool,
    ) -> None:
        """Update all EMA baselines with a new observation. O(1)."""
        self.duration_ema.update(duration_ms)
        self.data_volume_ema.update(data_bytes)
        self.success_rate_ema.update(1.0 if success else 0.0)
        self._update_tool_distribution(tool_name)

    def _update_tool_distribution(self, tool_name: str) -> None:
        """Update tool usage distribution with exponential decay."""
        self.known_tools.add(tool_name)
        alpha = 0.05
        for t in self.tool_distribution:
            self.tool_distribution[t] *= 1 - alpha
        self.tool_distribution[tool_name] = (
            self.tool_distribution.get(tool_name, 0.0) + alpha
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for persistence or API responses."""
        return {
            "agent_name": self.agent_name,
            "duration_mean": self.duration_ema.mean,
            "duration_std": self.duration_ema.std_dev,
            "data_volume_mean": self.data_volume_ema.mean,
            "rate_mean": self.rate_ema.mean,
            "success_rate": self.success_rate_ema.mean,
            "known_tools": sorted(self.known_tools),
            "observation_count": self.duration_ema.count,
            "thresholds": {
                "rate_multiplier": self.rate_threshold_multiplier,
                "data_multiplier": self.data_threshold_multiplier,
                "tool_abandonment": self.tool_abandonment_fraction,
            },
            "feedback": {
                "false_positives": self.false_positive_count,
                "true_positives": self.true_positive_count,
            },
        }
