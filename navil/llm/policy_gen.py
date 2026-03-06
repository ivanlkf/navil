# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Natural language to YAML policy generation."""

from __future__ import annotations

from typing import Any

import yaml

from navil.llm.client import LLMClient

POLICY_GEN_SYSTEM_PROMPT = """You are a security policy generator for MCP (Model Context Protocol) servers.
Convert natural language policy descriptions into YAML policy format compatible with navil.

The YAML schema requires:
- version: "1.0"
- agents: dict of agent profiles with tools_allowed, tools_denied, rate_limit_per_hour, data_clearance
- tools: dict of tool policies with allowed_actions, denied_actions
- suspicious_patterns: list of patterns with name, tool, actions, alert_level

Respond ONLY with valid YAML. No explanation, no markdown code fences."""


class PolicyGenerator:
    """Generate YAML policies from natural language descriptions."""

    def __init__(
        self, client: LLMClient | None = None, **client_kwargs: Any
    ) -> None:
        self.client = client or LLMClient(**client_kwargs)

    def generate(self, description: str) -> dict[str, Any]:
        """Generate a policy from a natural language description.

        Returns the parsed YAML as a dict.
        """
        response = self.client.complete(POLICY_GEN_SYSTEM_PROMPT, description)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return yaml.safe_load(cleaned) or {}

    def refine(
        self, existing_policy: dict[str, Any], instruction: str
    ) -> dict[str, Any]:
        """Refine an existing policy based on a natural language instruction."""
        policy_yaml = yaml.dump(existing_policy, default_flow_style=False)
        prompt = f"Current policy:\n\n{policy_yaml}\n\nModification requested:\n{instruction}"
        response = self.client.complete(POLICY_GEN_SYSTEM_PROMPT, prompt)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return yaml.safe_load(cleaned) or {}
