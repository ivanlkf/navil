"""Tests for LLM policy generation (all mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from navil.llm.policy_gen import PolicyGenerator


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


class TestPolicyGenerator:
    def test_generate_policy_from_description(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = """
version: "1.0"
agents:
  reader:
    tools_allowed: ["logs"]
    rate_limit_per_hour: 100
"""
        gen = PolicyGenerator(client=mock_client)
        policy = gen.generate("Only allow readers to access logs")
        assert policy["version"] == "1.0"
        assert "reader" in policy["agents"]

    def test_generate_strips_markdown_fences(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = """```yaml
version: "1.0"
agents:
  admin:
    tools_allowed: ["*"]
```"""
        gen = PolicyGenerator(client=mock_client)
        policy = gen.generate("Allow admin full access")
        assert policy["version"] == "1.0"

    def test_refine_includes_existing_policy(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = """
version: "1.0"
agents:
  reader:
    tools_allowed: ["logs"]
    rate_limit_per_hour: 50
"""
        gen = PolicyGenerator(client=mock_client)
        existing = {"version": "1.0", "agents": {"reader": {"rate_limit_per_hour": 100}}}
        gen.refine(existing, "Reduce rate limit to 50")
        call_args = mock_client.complete.call_args
        assert "rate_limit_per_hour: 100" in call_args[0][1]

    def test_generate_empty_response(self, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = ""
        gen = PolicyGenerator(client=mock_client)
        policy = gen.generate("invalid request")
        assert policy == {}
