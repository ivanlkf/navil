# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Apache License, Version 2.0 (see LICENSE)
"""Unified LLM client supporting Claude, OpenAI, Gemini, and Ollama."""

from __future__ import annotations

import logging
from typing import Any

from navil._compat import require_llm

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client with provider abstraction.

    Supports Anthropic (Claude), OpenAI, and Google Gemini APIs
    with a unified interface.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> None:
        require_llm(f"LLM client ({provider})")
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature

        if provider == "anthropic":
            import anthropic

            kwargs: dict[str, Any] = {}
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["base_url"] = base_url
            self.client: Any = anthropic.Anthropic(**kwargs)
            self.model = model or "claude-sonnet-4-20250514"
        elif provider == "ollama":
            import openai

            ollama_base = base_url or "http://localhost:11434/v1"
            self.client = openai.OpenAI(
                api_key="ollama",  # Ollama doesn't require a real key
                base_url=ollama_base,
            )
            self.model = model or self._detect_ollama_model(ollama_base)
            # Ollama uses the OpenAI-compatible chat API
            self.provider = "openai"
        elif provider in ("openai", "openai_compatible"):
            import openai

            kwargs = {}
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["base_url"] = base_url
            self.client = openai.OpenAI(**kwargs)
            self.model = model or ("gpt-4o" if provider == "openai" else "default")
            # Normalize provider for completion routing
            self.provider = "openai"
        elif provider == "gemini":
            import google.generativeai as genai

            if api_key:
                genai.configure(api_key=api_key)
            self.client = genai
            self.model = model or "gemini-2.0-flash"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def _detect_ollama_model(base_url: str) -> str:
        """Query Ollama for available models and pick the first local one."""
        import urllib.request

        # base_url is like http://localhost:11434/v1 — strip /v1
        host = base_url.rstrip("/").removesuffix("/v1")
        try:
            import json as _json

            req = urllib.request.Request(
                f"{host}/api/tags", method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = _json.loads(resp.read())
            models = data.get("models", [])
            # Prefer local models (skip cloud/remote ones)
            for m in models:
                name = m.get("name", "")
                if m.get("size", 0) > 1000:  # skip tiny cloud stubs
                    logger.info("Auto-detected Ollama model: %s", name)
                    return name
            # Fallback to first model if all are small
            if models:
                return models[0].get("name", "llama3.2")
        except Exception:
            logger.debug("Could not query Ollama models, using default")
        return "llama3.2"

    def complete(self, system_prompt: str, user_message: str) -> str:
        """Synchronous completion."""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        elif self.provider == "gemini":
            model = self.client.GenerativeModel(
                self.model,
                system_instruction=system_prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            response = model.generate_content(user_message)
            return response.text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            msg = response.choices[0].message
            content = msg.content or ""
            # Some thinking models (e.g. glm-4) put output in reasoning
            if not content.strip():
                reasoning = (
                    getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None) or ""
                )
                if reasoning:
                    logger.debug("Empty content, falling back to reasoning field")
                    content = reasoning
            return content
