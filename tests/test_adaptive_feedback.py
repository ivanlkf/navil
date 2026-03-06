"""Tests for feedback loop module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from navil.adaptive.baselines import AgentAdaptiveBaseline
from navil.adaptive.feedback import FeedbackEntry, FeedbackLoop


class TestFeedbackEntry:
    def test_auto_timestamp(self) -> None:
        entry = FeedbackEntry(
            alert_timestamp="2026-01-01T00:00:00",
            anomaly_type="RATE_SPIKE",
            agent_name="agent-a",
            verdict="confirmed",
        )
        assert entry.feedback_timestamp != ""

    def test_explicit_timestamp_preserved(self) -> None:
        entry = FeedbackEntry(
            alert_timestamp="2026-01-01T00:00:00",
            anomaly_type="RATE_SPIKE",
            agent_name="agent-a",
            verdict="dismissed",
            feedback_timestamp="2026-01-02T00:00:00",
        )
        assert entry.feedback_timestamp == "2026-01-02T00:00:00"


class TestFeedbackLoop:
    def test_submit_feedback(self) -> None:
        fl = FeedbackLoop()
        entry = fl.submit_feedback(
            alert_timestamp="2026-01-01T00:00:00",
            anomaly_type="RATE_SPIKE",
            agent_name="agent-a",
            verdict="confirmed",
        )
        assert len(fl.entries) == 1
        assert entry.verdict == "confirmed"

    def test_compute_adjustments_not_enough_data(self) -> None:
        fl = FeedbackLoop()
        for i in range(3):
            fl.submit_feedback(f"ts-{i}", "RATE_SPIKE", "a", "dismissed")
        assert fl.compute_adjustments("RATE_SPIKE") == {}

    def test_compute_adjustments_high_false_positive(self) -> None:
        fl = FeedbackLoop()
        for i in range(10):
            fl.submit_feedback(f"ts-{i}", "RATE_SPIKE", "a", "dismissed")
        adj = fl.compute_adjustments("RATE_SPIKE")
        assert adj.get("threshold_multiplier_delta", 0) > 0

    def test_compute_adjustments_high_true_positive(self) -> None:
        fl = FeedbackLoop()
        for i in range(10):
            fl.submit_feedback(f"ts-{i}", "RATE_SPIKE", "a", "confirmed")
        adj = fl.compute_adjustments("RATE_SPIKE")
        assert adj.get("threshold_multiplier_delta", 0) < 0

    def test_apply_adjustments_rate_spike(self) -> None:
        fl = FeedbackLoop()
        for i in range(10):
            fl.submit_feedback(f"ts-{i}", "RATE_SPIKE", "a", "dismissed")
        ab = AgentAdaptiveBaseline(agent_name="a")
        original = ab.rate_threshold_multiplier
        fl.apply_adjustments_to_baseline(ab, "RATE_SPIKE")
        assert ab.rate_threshold_multiplier > original

    def test_apply_adjustments_data_exfiltration(self) -> None:
        fl = FeedbackLoop()
        for i in range(10):
            fl.submit_feedback(f"ts-{i}", "DATA_EXFILTRATION", "a", "dismissed")
        ab = AgentAdaptiveBaseline(agent_name="a")
        original = ab.data_threshold_multiplier
        fl.apply_adjustments_to_baseline(ab, "DATA_EXFILTRATION")
        assert ab.data_threshold_multiplier > original

    def test_persistence_round_trip(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        fl = FeedbackLoop(persistence_path=path)
        fl.submit_feedback("ts-1", "RATE_SPIKE", "a", "confirmed", "real threat")
        fl.submit_feedback("ts-2", "RATE_SPIKE", "a", "dismissed", "false alarm")

        fl2 = FeedbackLoop(persistence_path=path)
        assert len(fl2.entries) == 2
        assert fl2.entries[0].verdict == "confirmed"
        assert fl2.entries[1].operator_notes == "false alarm"

        Path(path).unlink()

    def test_get_stats(self) -> None:
        fl = FeedbackLoop()
        fl.submit_feedback("ts-1", "RATE_SPIKE", "a", "confirmed")
        fl.submit_feedback("ts-2", "RATE_SPIKE", "a", "dismissed")
        fl.submit_feedback("ts-3", "DATA_EXFILTRATION", "b", "escalated")
        stats = fl.get_stats()
        assert stats["total_entries"] == 3
        assert stats["by_anomaly_type"]["RATE_SPIKE"]["confirmed"] == 1
        assert stats["by_anomaly_type"]["DATA_EXFILTRATION"]["escalated"] == 1

    def test_minimum_threshold_enforced(self) -> None:
        fl = FeedbackLoop()
        for i in range(20):
            fl.submit_feedback(f"ts-{i}", "RATE_SPIKE", "a", "dismissed")
        ab = AgentAdaptiveBaseline(agent_name="a")
        ab.rate_threshold_multiplier = 1.5  # At minimum
        fl.apply_adjustments_to_baseline(ab, "RATE_SPIKE")
        assert ab.rate_threshold_multiplier >= 1.5
