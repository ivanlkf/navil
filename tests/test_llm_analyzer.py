"""Tests for LLM analyzer (all mocked)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from navil.llm.analyzer import LLMAnalyzer


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    return client


class TestLLMAnalyzer:
    def test_analyze_config_parses_json(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = json.dumps(
            {
                "explanation": "Config has issues",
                "risks": ["plaintext creds"],
                "remediations": ["use vault"],
                "severity": "HIGH",
                "confidence": 0.9,
            }
        )
        analyzer = LLMAnalyzer(client=mock_client)
        result = analyzer.analyze_config({"server": {"protocol": "http"}})
        assert result["severity"] == "HIGH"
        assert len(result["risks"]) == 1

    def test_analyze_config_invalid_json_fallback(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "This is not JSON"
        analyzer = LLMAnalyzer(client=mock_client)
        result = analyzer.analyze_config({"test": True})
        assert result["explanation"] == "This is not JSON"
        assert result["severity"] == "UNKNOWN"

    def test_explain_anomaly_parses_json(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = json.dumps(
            {
                "explanation": "Agent is accessing admin tools",
                "likely_threat": True,
                "recommended_actions": ["revoke access"],
                "analysis": "Privilege escalation attempt",
            }
        )
        analyzer = LLMAnalyzer(client=mock_client)
        result = analyzer.explain_anomaly({"anomaly_type": "PRIVILEGE_ESCALATION"})
        assert result["likely_threat"] is True

    def test_explain_anomaly_invalid_json(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Not valid JSON response"
        analyzer = LLMAnalyzer(client=mock_client)
        result = analyzer.explain_anomaly({"anomaly_type": "RATE_SPIKE"})
        assert "explanation" in result
        assert result["likely_threat"] is False
