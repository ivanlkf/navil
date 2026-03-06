"""Tests for self-healing engine (all mocked)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from navil.llm.self_healing import SelfHealingEngine


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_policy_engine() -> MagicMock:
    pe = MagicMock()
    pe.policy = {"agents": {"agent-a": {"tools_allowed": ["logs"], "rate_limit_per_hour": 1000}}}
    return pe


@pytest.fixture
def mock_detector() -> MagicMock:
    from navil.adaptive.baselines import AgentAdaptiveBaseline
    detector = MagicMock()
    detector.adaptive_baselines = {
        "agent-a": AgentAdaptiveBaseline(agent_name="agent-a")
    }
    return detector


class TestSelfHealingEngine:
    def test_suggest_remediation(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = json.dumps({
            "actions": [
                {
                    "type": "threshold_adjustment",
                    "target": "agent-a",
                    "value": {"rate_multiplier": 5.0},
                    "reason": "Too many false positives",
                    "confidence": 0.85,
                    "reversible": True,
                }
            ],
            "summary": "Adjusting thresholds due to false positives",
            "risk_assessment": "LOW",
        })
        engine = SelfHealingEngine(client=mock_client)
        result = engine.suggest_remediation([], {})
        assert len(result["actions"]) == 1
        assert len(engine.pending_actions) == 1

    def test_suggest_invalid_json_fallback(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Not valid JSON"
        engine = SelfHealingEngine(client=mock_client)
        result = engine.suggest_remediation([], {})
        assert result["risk_assessment"] == "UNKNOWN"

    def test_apply_threshold_adjustment(
        self, mock_client: MagicMock, mock_detector: MagicMock
    ) -> None:
        engine = SelfHealingEngine(client=mock_client)
        action = {
            "type": "threshold_adjustment",
            "target": "agent-a",
            "value": {"rate_multiplier": 5.0},
            "confidence": 0.95,
            "reversible": True,
        }
        result = engine.apply_action(action, MagicMock(), mock_detector)
        assert result is True
        assert mock_detector.adaptive_baselines["agent-a"].rate_threshold_multiplier == 5.0

    def test_apply_policy_update(
        self, mock_client: MagicMock, mock_policy_engine: MagicMock
    ) -> None:
        engine = SelfHealingEngine(client=mock_client)
        action = {
            "type": "policy_update",
            "target": "agent-a",
            "value": {"rate_limit_per_hour": 500},
            "confidence": 0.9,
            "reversible": True,
        }
        result = engine.apply_action(action, mock_policy_engine, MagicMock())
        assert result is True
        assert mock_policy_engine.policy["agents"]["agent-a"]["rate_limit_per_hour"] == 500

    def test_apply_agent_block(
        self, mock_client: MagicMock, mock_policy_engine: MagicMock
    ) -> None:
        engine = SelfHealingEngine(client=mock_client)
        action = {
            "type": "agent_block",
            "target": "agent-a",
            "confidence": 0.99,
            "reversible": False,
        }
        result = engine.apply_action(action, mock_policy_engine, MagicMock())
        assert result is True
        assert mock_policy_engine.policy["agents"]["agent-a"]["tools_denied"] == ["*"]

    def test_auto_remediate_above_threshold(
        self, mock_client: MagicMock, mock_detector: MagicMock
    ) -> None:
        engine = SelfHealingEngine(client=mock_client, auto_apply=True, auto_apply_confidence_threshold=0.9)
        engine.pending_actions = [
            {"type": "threshold_adjustment", "target": "agent-a", "value": {"rate_multiplier": 4.0}, "confidence": 0.95, "reversible": True},
        ]
        applied = engine.auto_remediate(MagicMock(), mock_detector)
        assert len(applied) == 1
        assert len(engine.pending_actions) == 0

    def test_auto_remediate_below_threshold(self, mock_client: MagicMock) -> None:
        engine = SelfHealingEngine(client=mock_client, auto_apply=True, auto_apply_confidence_threshold=0.9)
        engine.pending_actions = [
            {"type": "threshold_adjustment", "target": "agent-a", "value": {}, "confidence": 0.5, "reversible": True},
        ]
        applied = engine.auto_remediate(MagicMock(), MagicMock())
        assert len(applied) == 0
        assert len(engine.pending_actions) == 1

    def test_auto_remediate_skips_irreversible(self, mock_client: MagicMock) -> None:
        engine = SelfHealingEngine(client=mock_client, auto_apply=True, auto_apply_confidence_threshold=0.9)
        engine.pending_actions = [
            {"type": "agent_block", "target": "agent-a", "confidence": 0.99, "reversible": False},
        ]
        applied = engine.auto_remediate(MagicMock(), MagicMock())
        assert len(applied) == 0
        assert len(engine.pending_actions) == 1


class TestFullAutoRemediate:
    """Tests for the full auto-remediation cycle."""

    def test_full_cycle_partitions_actions(
        self, mock_client: MagicMock, mock_policy_engine: MagicMock, mock_detector: MagicMock,
    ) -> None:
        """High-confidence reversible actions are auto-applied, others go to manual review."""
        mock_client.complete.return_value = json.dumps({
            "summary": "Critical anomalies detected",
            "risk_assessment": "HIGH",
            "actions": [
                {"type": "threshold_adjustment", "target": "agent-a", "value": {"rate_multiplier": 5.0},
                 "reason": "Too many false positives", "confidence": 0.95, "reversible": True},
                {"type": "agent_block", "target": "agent-b", "value": {},
                 "reason": "Suspicious behavior", "confidence": 0.99, "reversible": False},
            ],
        })
        mock_detector.get_alerts.return_value = []

        engine = SelfHealingEngine(client=mock_client, auto_apply_confidence_threshold=0.9)
        result = engine.full_auto_remediate(
            alerts=[{"agent": "agent-a", "severity": "HIGH"}],
            current_policy={}, baselines={},
            policy_engine=mock_policy_engine, detector=mock_detector,
        )

        assert len(result["auto_applied"]) == 1
        assert result["auto_applied"][0]["type"] == "threshold_adjustment"
        assert len(result["manual_review"]) == 1
        assert result["manual_review"][0]["type"] == "agent_block"
        assert result["initial_analysis"]["risk_assessment"] == "HIGH"
        assert result["llm_calls_used"] == 1

    def test_full_cycle_no_actions(self, mock_client: MagicMock) -> None:
        """When LLM suggests no actions, result is clean."""
        mock_client.complete.return_value = json.dumps({
            "summary": "All clear", "risk_assessment": "LOW", "actions": [],
        })
        detector = MagicMock()
        detector.get_alerts.return_value = []

        engine = SelfHealingEngine(client=mock_client)
        result = engine.full_auto_remediate(
            alerts=[], current_policy={}, baselines={},
            policy_engine=MagicMock(), detector=detector,
        )

        assert result["auto_applied"] == []
        assert result["manual_review"] == []
        assert result["post_status"]["healthy"] is True
        assert result["llm_calls_used"] == 1

    def test_full_cycle_custom_threshold(
        self, mock_client: MagicMock, mock_detector: MagicMock,
    ) -> None:
        """Custom confidence threshold overrides the engine default."""
        mock_client.complete.return_value = json.dumps({
            "summary": "test", "risk_assessment": "MEDIUM",
            "actions": [
                {"type": "threshold_adjustment", "target": "agent-a",
                 "value": {"rate_multiplier": 3.0}, "reason": "test",
                 "confidence": 0.8, "reversible": True},
            ],
        })
        mock_detector.get_alerts.return_value = []

        engine = SelfHealingEngine(client=mock_client, auto_apply_confidence_threshold=0.9)

        # Default threshold 0.9 → 0.8 confidence goes to manual_review
        result = engine.full_auto_remediate(
            alerts=[{"agent": "agent-a"}], current_policy={}, baselines={},
            policy_engine=MagicMock(), detector=mock_detector,
        )
        assert len(result["manual_review"]) == 1
        assert len(result["auto_applied"]) == 0

        # Override threshold to 0.7 → 0.8 confidence is auto-applied
        result2 = engine.full_auto_remediate(
            alerts=[{"agent": "agent-a"}], current_policy={}, baselines={},
            policy_engine=MagicMock(), detector=mock_detector,
            confidence_threshold=0.7,
        )
        assert len(result2["auto_applied"]) == 1
        assert len(result2["manual_review"]) == 0

    def test_full_cycle_post_status_reflects_remaining_alerts(
        self, mock_client: MagicMock, mock_detector: MagicMock,
    ) -> None:
        """Post-status correctly reports remaining alerts after remediation."""
        mock_client.complete.return_value = json.dumps({
            "summary": "test", "risk_assessment": "HIGH",
            "actions": [
                {"type": "threshold_adjustment", "target": "agent-a",
                 "value": {"rate_multiplier": 5.0}, "reason": "test",
                 "confidence": 0.95, "reversible": True},
            ],
        })
        # Simulate remaining alerts after remediation
        mock_detector.get_alerts.return_value = [
            {"agent": "agent-b", "severity": "MEDIUM"},
        ]

        engine = SelfHealingEngine(client=mock_client, auto_apply_confidence_threshold=0.9)
        result = engine.full_auto_remediate(
            alerts=[{"agent": "agent-a"}], current_policy={}, baselines={},
            policy_engine=MagicMock(), detector=mock_detector,
        )

        assert result["post_status"]["healthy"] is False
        assert result["post_status"]["remaining_alert_count"] == 1

    def test_full_cycle_all_healthy(
        self, mock_client: MagicMock, mock_detector: MagicMock,
    ) -> None:
        """When all alerts are resolved, post_status reports healthy."""
        mock_client.complete.return_value = json.dumps({
            "summary": "test", "risk_assessment": "HIGH",
            "actions": [
                {"type": "threshold_adjustment", "target": "agent-a",
                 "value": {"rate_multiplier": 5.0}, "reason": "test",
                 "confidence": 0.95, "reversible": True},
            ],
        })
        mock_detector.get_alerts.return_value = []

        engine = SelfHealingEngine(client=mock_client, auto_apply_confidence_threshold=0.9)
        result = engine.full_auto_remediate(
            alerts=[{"agent": "agent-a"}], current_policy={}, baselines={},
            policy_engine=MagicMock(), detector=mock_detector,
        )

        assert result["post_status"]["healthy"] is True
        assert result["post_status"]["remaining_alert_count"] == 0
        assert len(result["auto_applied"]) == 1
