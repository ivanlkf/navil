# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Apache License, Version 2.0 (see LICENSE)
"""LLM-powered security analysis and anomaly explanation."""

from __future__ import annotations

import json
from typing import Any

from navil.llm import extract_json
from navil.llm.client import LLMClient

ANALYSIS_SYSTEM_PROMPT = """\
You are a security analyst for MCP server configurations.
Analyze the provided configuration or anomaly data and provide:
1. A clear explanation of security implications
2. Specific risks identified
3. Actionable remediation steps
4. A risk severity rating (CRITICAL, HIGH, MEDIUM, LOW, INFO)

Be concise and technical. Format your response as JSON with keys:
explanation, risks (list), remediations (list), severity, confidence (0.0-1.0)."""

ANOMALY_EXPLANATION_PROMPT = """\
You are a security analyst explaining behavioral anomalies
in MCP agent systems. Given the anomaly data, explain:
1. What the anomaly means in plain language
2. Whether it is likely a true threat or a false positive
3. What actions the operator should take
4. What the contributing factors suggest

Format as JSON with keys:
explanation, likely_threat (bool), recommended_actions (list), analysis."""


class LLMAnalyzer:
    """LLM-powered analysis for configs and anomalies."""

    def __init__(self, client: LLMClient | None = None, **client_kwargs: Any) -> None:
        self.client = client or LLMClient(**client_kwargs)

    def analyze_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Analyze an MCP config for security issues using LLM."""
        config_str = json.dumps(config, indent=2)
        response = self.client.complete(
            ANALYSIS_SYSTEM_PROMPT,
            f"Analyze this MCP server configuration:\n\n{config_str}",
        )
        try:
            return json.loads(extract_json(response))
        except (json.JSONDecodeError, ValueError):
            return {
                "explanation": response[:500],
                "risks": [],
                "remediations": [],
                "severity": "UNKNOWN",
            }

    def explain_anomaly(self, anomaly_data: dict[str, Any]) -> dict[str, Any]:
        """Generate a human-readable explanation of an anomaly."""
        anomaly_str = json.dumps(anomaly_data, indent=2)
        response = self.client.complete(
            ANOMALY_EXPLANATION_PROMPT,
            f"Explain this behavioral anomaly:\n\n{anomaly_str}",
        )
        try:
            return json.loads(extract_json(response))
        except (json.JSONDecodeError, ValueError):
            return {
                "explanation": response[:500],
                "likely_threat": False,
                "recommended_actions": [],
            }
