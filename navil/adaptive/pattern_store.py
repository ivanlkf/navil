"""Persistent store for learned patterns from confirmed incidents."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LearnedPattern:
    """A pattern extracted from a confirmed incident."""

    pattern_id: str
    anomaly_type: str
    description: str
    features: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    match_count: int = 0
    confidence_boost: float = 0.2

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class PatternStore:
    """Stores and matches learned patterns from confirmed anomalies.

    When an operator confirms an anomaly alert, the system can extract
    a pattern from the incident context and store it. Future anomaly
    checks query the pattern store for matches, boosting confidence
    when a known attack pattern is recognized.
    """

    def __init__(self, store_path: str | None = None) -> None:
        self.store_path = Path(store_path) if store_path else None
        self.patterns: list[LearnedPattern] = []
        self._load()

    def add_pattern(self, pattern: LearnedPattern) -> None:
        """Add a learned pattern to the store."""
        self.patterns.append(pattern)
        self._persist()
        logger.info(f"Learned pattern added: {pattern.pattern_id}")

    def match(self, context: dict[str, Any]) -> list[tuple[LearnedPattern, float]]:
        """Find matching patterns and return (pattern, match_score) pairs.

        Args:
            context: Current invocation context with keys like
                'recent_tools', 'current_data_volume', 'anomaly_type'

        Returns:
            List of (pattern, score) tuples sorted by score descending.
            Only patterns with score > 0.3 are returned.
        """
        matches = []
        for pattern in self.patterns:
            score = self._compute_match_score(pattern, context)
            if score > 0.3:
                pattern.match_count += 1
                matches.append((pattern, score))
        if matches:
            self._persist()
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def learn_from_incident(
        self,
        anomaly_type: str,
        agent_name: str,
        tool_sequence: list[str],
        data_volumes: list[int] | None = None,
        description: str = "",
    ) -> LearnedPattern:
        """Extract and store a pattern from a confirmed incident."""
        data_volumes = data_volumes or []
        pattern = LearnedPattern(
            pattern_id=f"learned_{len(self.patterns)}_{anomaly_type.lower()}",
            anomaly_type=anomaly_type,
            description=description or f"Learned from {agent_name} incident",
            features={
                "tool_sequence": tool_sequence,
                "avg_data_volume": (
                    sum(data_volumes) / len(data_volumes) if data_volumes else 0
                ),
                "tool_count": len(set(tool_sequence)),
            },
        )
        self.add_pattern(pattern)
        return pattern

    def _compute_match_score(
        self, pattern: LearnedPattern, context: dict[str, Any]
    ) -> float:
        """Score how well a context matches a pattern. Returns 0.0 to 1.0."""
        score = 0.0
        total_weight = 0.0

        features = pattern.features

        # Tool sequence overlap
        if "tool_sequence" in features and "recent_tools" in context:
            pattern_tools = set(features["tool_sequence"])
            context_tools = set(context["recent_tools"])
            if pattern_tools:
                overlap = len(pattern_tools & context_tools) / len(pattern_tools)
                score += overlap * 0.6
                total_weight += 0.6

        # Data volume similarity
        if "avg_data_volume" in features and "current_data_volume" in context:
            baseline_vol = max(features["avg_data_volume"], 1)
            ratio = context["current_data_volume"] / baseline_vol
            if ratio > 0.5:
                score += min(ratio / 2.0, 0.4) * 0.4
                total_weight += 0.4

        # Anomaly type match bonus
        if context.get("anomaly_type") == pattern.anomaly_type:
            score += 0.2
            total_weight += 0.2

        return score / total_weight if total_weight > 0 else 0.0

    def _persist(self) -> None:
        """Save patterns to disk."""
        if self.store_path is None:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w") as f:
            json.dump([asdict(p) for p in self.patterns], f, indent=2)

    def _load(self) -> None:
        """Load patterns from disk."""
        if self.store_path is None or not self.store_path.exists():
            return
        try:
            with open(self.store_path) as f:
                data = json.load(f)
            self.patterns = [LearnedPattern(**d) for d in data]
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Could not load patterns from {self.store_path}")
            self.patterns = []
