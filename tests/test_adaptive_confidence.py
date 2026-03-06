"""Tests for confidence scoring module."""

from __future__ import annotations

from navil.adaptive.confidence import (
    AnomalyScore,
    ConfidenceLevel,
    multi_signal_confidence,
    z_score_to_confidence,
)


class TestZScoreToConfidence:
    def test_zero_z_gives_low_confidence(self) -> None:
        c = z_score_to_confidence(0.0)
        assert c < 0.3  # z=0 means at the mean, not anomalous

    def test_high_z_gives_high_confidence(self) -> None:
        c = z_score_to_confidence(5.0)
        assert c > 0.9

    def test_midpoint_at_1_5(self) -> None:
        c = z_score_to_confidence(1.5)
        assert abs(c - 0.5) < 0.01

    def test_negative_z_gives_very_low(self) -> None:
        c = z_score_to_confidence(-2.0)
        assert c < 0.05

    def test_monotonically_increasing(self) -> None:
        prev = 0.0
        for z in range(0, 10):
            c = z_score_to_confidence(float(z))
            assert c >= prev
            prev = c


class TestMultiSignalConfidence:
    def test_empty_signals(self) -> None:
        assert multi_signal_confidence({}) == 0.0

    def test_single_signal_passthrough(self) -> None:
        c = multi_signal_confidence({"a": 0.7})
        assert abs(c - 0.7) < 0.01

    def test_two_signals_higher_than_either(self) -> None:
        c = multi_signal_confidence({"a": 0.5, "b": 0.5})
        assert c > 0.5
        # 1 - (0.5 * 0.5) = 0.75
        assert abs(c - 0.75) < 0.01

    def test_zero_signal_no_effect(self) -> None:
        c1 = multi_signal_confidence({"a": 0.8})
        c2 = multi_signal_confidence({"a": 0.8, "b": 0.0})
        assert abs(c1 - c2) < 0.01

    def test_clamps_to_range(self) -> None:
        c = multi_signal_confidence({"a": 1.5, "b": -0.5})
        assert 0.0 <= c <= 1.0


class TestAnomalyScore:
    def test_level_critical(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.9, z_score=5.0)
        assert s.level == ConfidenceLevel.CRITICAL

    def test_level_high(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.7, z_score=3.0)
        assert s.level == ConfidenceLevel.HIGH

    def test_level_medium(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.5, z_score=2.0)
        assert s.level == ConfidenceLevel.MEDIUM

    def test_level_low(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.3, z_score=1.0)
        assert s.level == ConfidenceLevel.LOW

    def test_level_negligible(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.1, z_score=0.5)
        assert s.level == ConfidenceLevel.NEGLIGIBLE

    def test_should_alert_above_threshold(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.6, z_score=3.0)
        assert s.should_alert is True

    def test_should_not_alert_below_threshold(self) -> None:
        s = AnomalyScore(anomaly_type="TEST", confidence=0.3, z_score=1.0)
        assert s.should_alert is False

    def test_to_dict(self) -> None:
        s = AnomalyScore(
            anomaly_type="RATE_SPIKE",
            confidence=0.75,
            z_score=3.5,
            evidence=["high rate"],
            contributing_factors={"rate": 3.5},
        )
        d = s.to_dict()
        assert d["anomaly_type"] == "RATE_SPIKE"
        assert d["confidence"] == 0.75
        assert d["level"] == "HIGH"
        assert d["should_alert"] is True
