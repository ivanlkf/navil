# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Shared application state for the Navil Cloud dashboard."""

from __future__ import annotations

import logging
import os
from typing import Any

from navil._compat import has_llm
from navil.adaptive.feedback import FeedbackLoop
from navil.cloud.billing import BillingManager
from navil.adaptive.pattern_store import PatternStore
from navil.anomaly_detector import BehavioralAnomalyDetector
from navil.credential_manager import CredentialManager
from navil.policy_engine import PolicyEngine
from navil.scanner import MCPSecurityScanner

logger = logging.getLogger(__name__)


class AppState:
    """Singleton holding all navil component instances."""

    _instance: AppState | None = None

    def __init__(self) -> None:
        self.feedback_loop = FeedbackLoop()
        self.pattern_store = PatternStore()
        self.scanner = MCPSecurityScanner()
        self.credential_manager = CredentialManager()
        self.policy_engine = PolicyEngine()
        self.anomaly_detector = BehavioralAnomalyDetector(
            feedback_loop=self.feedback_loop,
            pattern_store=self.pattern_store,
        )
        self.demo_seeded = False
        self.billing = BillingManager()

        # Proxy state (set when proxy is started from Cloud API)
        self.proxy: Any = None
        self.proxy_running: bool = False

        # LLM components (optional — require navil[llm])
        self.llm_available = has_llm()
        self.llm_analyzer: Any = None
        self.policy_generator: Any = None
        self.self_healing: Any = None
        self.llm_provider: str = ""
        self.llm_model: str = ""
        self.llm_base_url: str = ""
        self.llm_api_key_configured: bool = False

        if self.llm_available:
            # Auto-detect provider from available API keys
            provider = "anthropic"  # default
            api_key: str | None = None

            gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if gemini_key:
                provider = "gemini"
                api_key = gemini_key
            elif os.environ.get("OPENAI_API_KEY"):
                provider = "openai"
            elif os.environ.get("ANTHROPIC_API_KEY"):
                provider = "anthropic"
            elif self._ollama_available():
                provider = "ollama"
                api_key = "ollama"

            try:
                self._init_llm_components(provider, api_key)
            except (ImportError, ValueError, RuntimeError, TypeError) as e:
                logger.warning(f"LLM initialization failed: {e}")

    @staticmethod
    def _ollama_available() -> bool:
        """Check if Ollama is running locally."""
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1):
                return True
        except Exception:
            return False

    def _init_llm_components(
        self,
        provider: str,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Create LLM client and inject into all components."""
        from navil.llm.analyzer import LLMAnalyzer
        from navil.llm.client import LLMClient
        from navil.llm.policy_gen import PolicyGenerator
        from navil.llm.self_healing import SelfHealingEngine

        client = LLMClient(
            provider=provider, api_key=api_key, base_url=base_url, model=model,
        )
        self.llm_analyzer = LLMAnalyzer(client=client)
        self.policy_generator = PolicyGenerator(client=client)
        self.self_healing = SelfHealingEngine(client=client)
        self.llm_provider = provider
        self.llm_model = client.model
        self.llm_base_url = base_url or ""
        self.llm_api_key_configured = api_key is not None or provider == "ollama" or bool(
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )

    def configure_llm(
        self,
        provider: str,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Reconfigure LLM at runtime with a new provider and API key."""
        if not self.llm_available:
            raise RuntimeError(
                "LLM SDKs not installed. Install with: pip install navil[llm]"
            )
        self._init_llm_components(provider, api_key, base_url=base_url, model=model)
        self.llm_api_key_configured = True

    def get_llm_config(self) -> dict[str, Any]:
        """Return current LLM configuration (never exposes the actual key)."""
        return {
            "available": self.llm_available,
            "api_key_set": self.llm_api_key_configured,
            "provider": self.llm_provider,
            "model": self.llm_model,
            "base_url": self.llm_base_url,
        }

    @classmethod
    def get(cls) -> AppState:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
