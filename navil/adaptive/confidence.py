"""Confidence scoring for anomaly detection results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConfidenceLevel(Enum):
    """Human-readable confidence buckets."""

    NEGLIGIBLE = "NEGLIGIBLE"  # 0.0 - 0.2
    LOW = "LOW"  # 0.2 - 0.4
    MEDIUM = "MEDIUM"  # 0.4 - 0.6
    HIGH = "HIGH"  # 0.6 - 0.8
    CRITICAL = "CRITICAL"  # 0.8 - 1.0


@dataclass
class AnomalyScore:
    """Result of a confidence-scored anomaly check."""

    anomaly_type: str
    confidence: float  # 0.0 to 1.0
    z_score: float  # Raw statistical z-score
    evidence: list[str] = field(default_factory=list)
    contributing_factors: dict[str, float] = field(default_factory=dict)

    @property
    def level(self) -> ConfidenceLevel:
        """Map confidence to a human-readable level."""
        if self.confidence >= 0.8:
            return ConfidenceLevel.CRITICAL
        elif self.confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.2:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.NEGLIGIBLE

    @property
    def should_alert(self) -> bool:
        """Whether this score warrants an alert (threshold: 0.5)."""
        return self.confidence >= 0.5

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "anomaly_type": self.anomaly_type,
            "confidence": self.confidence,
            "level": self.level.value,
            "z_score": self.z_score,
            "should_alert": self.should_alert,
            "evidence": self.evidence,
            "contributing_factors": self.contributing_factors,
        }


def z_score_to_confidence(z: float) -> float:
    """Convert a z-score to a 0-1 confidence using the sigmoid function.

    Maps z=0 -> ~0.18, z=1.5 -> 0.5, z=3 -> ~0.82, z=5 -> ~0.97
    The shift ensures moderate deviations (1-2 sigma) give low confidence,
    while extreme deviations (3+ sigma) give high confidence.
    """
    shifted = z - 1.5  # Shift so z=1.5 maps to 0.5
    return 1.0 / (1.0 + math.exp(-shifted))


def multi_signal_confidence(signals: dict[str, float]) -> float:
    """Combine multiple independent confidence signals using Bayesian product.

    Each signal is a probability that the anomaly is real.
    Returns combined probability: 1 - product(1 - p_i).

    Args:
        signals: Mapping of signal_name -> confidence (0.0 to 1.0)

    Returns:
        Combined confidence score (0.0 to 1.0)
    """
    if not signals:
        return 0.0
    complement_product = 1.0
    for p in signals.values():
        complement_product *= 1.0 - max(0.0, min(1.0, p))
    return 1.0 - complement_product
