# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Apache License, Version 2.0 (see LICENSE)
"""Natural language to YAML policy generation."""

from __future__ import annotations

from typing import Any

import yaml

from navil.llm.client import LLMClient

POLICY_GEN_SYSTEM_PROMPT = """\
You are a security policy generator for MCP servers.
Convert natural language policy descriptions into YAML policy format compatible with navil.

The YAML schema requires:
- version: "1.0"
- agents: dict of agent profiles with tools_allowed, tools_denied,
  rate_limit_per_hour, data_clearance
- tools: dict of tool policies with allowed_actions, denied_actions
- suspicious_patterns: list of patterns with name, tool, actions,
  alert_level

SECURITY RULES — always enforce these in generated policies:
1. Default-deny: if the user doesn't explicitly allow a tool or action, deny it.
2. Never generate policies that grant wildcard ("*") access to tools or paths.
3. Always include rate limits — default to 60 requests/hour if unspecified.
4. Never allow destructive actions (delete, destroy, drop, exfiltrate) \
unless the user explicitly requests them and names the specific agent/tool.
5. Restrict file system paths to specific directories — never allow root ("/") access.
6. Always include at least one suspicious_pattern entry for high-risk operations.
7. Set data_clearance to the minimum level needed (public < internal < confidential < restricted).

If the user's description is vague or overly permissive, generate a \
restrictive policy and add a comment explaining the constraint.

Respond ONLY with valid YAML. No explanation, no markdown code fences."""


class PolicyGenerator:
    """Generate YAML policies from natural language descriptions."""

    def __init__(self, client: LLMClient | None = None, **client_kwargs: Any) -> None:
        self.client = client or LLMClient(**client_kwargs)

    @staticmethod
    def _parse_yaml(response: str) -> dict[str, Any]:
        """Extract and parse YAML from an LLM response."""
        cleaned = response.strip()
        # Strip markdown code fences (```yaml ... ``` or ``` ... ```)
        if "```" in cleaned:
            import re

            match = re.search(r"```(?:ya?ml)?\s*\n(.*?)```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
            elif cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])
        # Strip leading prose before the YAML (some models add explanations)
        for prefix in ("version:", "agents:", "---"):
            idx = cleaned.find(prefix)
            if idx == 0:
                break  # YAML already starts at the beginning
            if idx > 0:
                cleaned = cleaned[idx:]
                break
        result = yaml.safe_load(cleaned)
        if not isinstance(result, dict) or not result:
            raise ValueError(f"LLM returned invalid or empty policy. Raw output: {response[:200]}")
        return result

    def generate(self, description: str) -> dict[str, Any]:
        """Generate a policy from a natural language description.

        Returns the parsed YAML as a dict, or ``{}`` if the LLM
        response is empty or unparseable.
        """
        response = self.client.complete(POLICY_GEN_SYSTEM_PROMPT, description)
        try:
            return self._parse_yaml(response)
        except (ValueError, yaml.YAMLError):
            return {}

    def refine(self, existing_policy: dict[str, Any], instruction: str) -> dict[str, Any]:
        """Refine an existing policy based on a natural language instruction."""
        policy_yaml = yaml.dump(existing_policy, default_flow_style=False)
        prompt = f"Current policy:\n\n{policy_yaml}\n\nModification requested:\n{instruction}"
        response = self.client.complete(POLICY_GEN_SYSTEM_PROMPT, prompt)
        return self._parse_yaml(response)
