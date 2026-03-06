"""Tests for LLM client (all mocked, no real API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestLLMClient:
    @patch("navil._compat.require_llm")
    def test_unsupported_provider_raises(self, mock_req: MagicMock) -> None:
        from navil.llm.client import LLMClient

        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(provider="invalid")

    @patch("navil._compat.require_llm")
    def test_complete_anthropic(self, mock_req: MagicMock) -> None:
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"result": "ok"}')]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from navil.llm.client import LLMClient

            client = LLMClient(provider="anthropic", api_key="test-key")
            result = client.complete("system prompt", "user message")
            assert result == '{"result": "ok"}'
            mock_client.messages.create.assert_called_once()

    @patch("navil._compat.require_llm")
    def test_complete_openai(self, mock_req: MagicMock) -> None:
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            from navil.llm.client import LLMClient

            client = LLMClient(provider="openai", api_key="test-key")
            result = client.complete("system prompt", "user message")
            assert result == '{"result": "ok"}'
