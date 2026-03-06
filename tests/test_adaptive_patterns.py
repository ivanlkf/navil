"""Tests for pattern store module."""

from __future__ import annotations

import tempfile
from pathlib import Path

from navil.adaptive.pattern_store import LearnedPattern, PatternStore


class TestLearnedPattern:
    def test_auto_timestamp(self) -> None:
        p = LearnedPattern(pattern_id="test-1", anomaly_type="RUG_PULL", description="test")
        assert p.created_at != ""

    def test_default_confidence_boost(self) -> None:
        p = LearnedPattern(pattern_id="test-1", anomaly_type="RUG_PULL", description="test")
        assert p.confidence_boost == 0.2


class TestPatternStore:
    def test_add_pattern(self) -> None:
        ps = PatternStore()
        p = LearnedPattern("p1", "RUG_PULL", "test pattern")
        ps.add_pattern(p)
        assert len(ps.patterns) == 1

    def test_learn_from_incident(self) -> None:
        ps = PatternStore()
        pattern = ps.learn_from_incident(
            anomaly_type="RUG_PULL",
            agent_name="agent-a",
            tool_sequence=["logs", "admin_panel", "cred_mgr"],
            data_volumes=[100, 200, 300],
        )
        assert pattern.anomaly_type == "RUG_PULL"
        assert pattern.features["tool_count"] == 3
        assert pattern.features["avg_data_volume"] == 200

    def test_match_returns_matching_patterns(self) -> None:
        ps = PatternStore()
        ps.learn_from_incident(
            anomaly_type="RUG_PULL",
            agent_name="agent-a",
            tool_sequence=["logs", "admin_panel", "cred_mgr"],
        )
        context = {
            "recent_tools": ["logs", "admin_panel", "cred_mgr"],
            "anomaly_type": "RUG_PULL",
        }
        matches = ps.match(context)
        assert len(matches) >= 1
        assert matches[0][1] > 0.3  # Score above threshold

    def test_match_returns_empty_for_no_match(self) -> None:
        ps = PatternStore()
        ps.learn_from_incident(
            anomaly_type="RUG_PULL",
            agent_name="agent-a",
            tool_sequence=["admin_panel", "cred_mgr", "secret_vault"],
        )
        context = {
            "recent_tools": ["totally_different_tool"],
            "anomaly_type": "DATA_EXFILTRATION",
        }
        matches = ps.match(context)
        assert len(matches) == 0

    def test_match_count_increments(self) -> None:
        ps = PatternStore()
        ps.learn_from_incident(
            anomaly_type="RUG_PULL",
            agent_name="agent-a",
            tool_sequence=["logs", "admin"],
        )
        context = {"recent_tools": ["logs", "admin"], "anomaly_type": "RUG_PULL"}
        ps.match(context)
        assert ps.patterns[0].match_count == 1
        ps.match(context)
        assert ps.patterns[0].match_count == 2

    def test_persistence_round_trip(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        ps = PatternStore(store_path=path)
        ps.learn_from_incident("RUG_PULL", "agent-a", ["logs", "admin"])

        ps2 = PatternStore(store_path=path)
        assert len(ps2.patterns) == 1
        assert ps2.patterns[0].anomaly_type == "RUG_PULL"

        Path(path).unlink()

    def test_data_volume_matching(self) -> None:
        ps = PatternStore()
        ps.learn_from_incident(
            anomaly_type="DATA_EXFILTRATION",
            agent_name="agent-a",
            tool_sequence=["logs"],
            data_volumes=[1000, 2000],
        )
        context = {
            "recent_tools": ["logs"],
            "current_data_volume": 1500,
            "anomaly_type": "DATA_EXFILTRATION",
        }
        matches = ps.match(context)
        assert len(matches) >= 1
