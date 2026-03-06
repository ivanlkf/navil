"""Tests for adaptive baselines (EMA and AgentAdaptiveBaseline)."""

from __future__ import annotations

from navil.adaptive.baselines import AgentAdaptiveBaseline, EMABaseline


class TestEMABaseline:
    def test_initial_state(self) -> None:
        ema = EMABaseline(alpha=0.1)
        assert ema.count == 0
        assert ema.mean == 0.0
        assert ema.std_dev == 0.0

    def test_first_update_sets_mean(self) -> None:
        ema = EMABaseline(alpha=0.1)
        ema.update(100.0)
        assert ema.mean == 100.0
        assert ema.count == 1
        assert ema.variance == 0.0

    def test_second_update_moves_mean(self) -> None:
        ema = EMABaseline(alpha=0.5)
        ema.update(100.0)
        ema.update(200.0)
        # mean = 100 + 0.5 * (200 - 100) = 150
        assert ema.mean == 150.0
        assert ema.count == 2

    def test_convergence_to_true_mean(self) -> None:
        ema = EMABaseline(alpha=0.1)
        for _ in range(200):
            ema.update(50.0)
        assert abs(ema.mean - 50.0) < 0.1

    def test_z_score_at_mean_is_zero(self) -> None:
        ema = EMABaseline(alpha=0.1)
        for v in [10, 20, 30, 40, 50]:
            ema.update(float(v))
        z = ema.z_score(ema.mean)
        assert abs(z) < 0.01

    def test_z_score_above_mean_positive(self) -> None:
        ema = EMABaseline(alpha=0.1)
        for _ in range(50):
            ema.update(100.0)
        # Force some variance
        ema.update(200.0)
        assert ema.z_score(300.0) > 0

    def test_z_score_zero_variance(self) -> None:
        ema = EMABaseline(alpha=0.1)
        ema.update(42.0)
        # Same value -> zero std_dev
        assert ema.z_score(42.0) == 0.0
        assert ema.z_score(100.0) == float("inf")

    def test_std_dev_positive_after_varied_data(self) -> None:
        ema = EMABaseline(alpha=0.2)
        for v in [10, 50, 10, 50, 10, 50]:
            ema.update(float(v))
        assert ema.std_dev > 0

    def test_to_dict(self) -> None:
        ema = EMABaseline(alpha=0.1)
        ema.update(100.0)
        d = ema.to_dict()
        assert "mean" in d
        assert "variance" in d
        assert "count" in d
        assert "std_dev" in d
        assert d["count"] == 1


class TestAgentAdaptiveBaseline:
    def test_creation(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        assert ab.agent_name == "test-agent"
        assert ab.duration_ema.count == 0

    def test_record_observation_updates_all(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        ab.record_observation(duration_ms=100.0, data_bytes=1024.0, tool_name="logs", success=True)
        assert ab.duration_ema.count == 1
        assert ab.data_volume_ema.count == 1
        assert ab.success_rate_ema.count == 1
        assert "logs" in ab.known_tools

    def test_tool_distribution_updates(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        for _ in range(10):
            ab.record_observation(100.0, 0.0, "logs", True)
        ab.record_observation(100.0, 0.0, "admin", True)
        assert "logs" in ab.tool_distribution
        assert "admin" in ab.tool_distribution
        assert ab.tool_distribution["logs"] > ab.tool_distribution["admin"]

    def test_known_tools_tracks_all(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        ab.record_observation(100.0, 0.0, "logs", True)
        ab.record_observation(100.0, 0.0, "admin", True)
        ab.record_observation(100.0, 0.0, "db", True)
        assert ab.known_tools == {"logs", "admin", "db"}

    def test_to_dict_complete(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        ab.record_observation(100.0, 512.0, "logs", True)
        d = ab.to_dict()
        assert d["agent_name"] == "test-agent"
        assert d["observation_count"] == 1
        assert "thresholds" in d
        assert "feedback" in d
        assert d["known_tools"] == ["logs"]

    def test_default_thresholds(self) -> None:
        ab = AgentAdaptiveBaseline(agent_name="test-agent")
        assert ab.rate_threshold_multiplier == 3.0
        assert ab.data_threshold_multiplier == 5.0
        assert ab.tool_abandonment_fraction == 0.5
