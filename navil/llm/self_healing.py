# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Self-healing policy and detection adjustments."""

from __future__ import annotations

import json
import logging
from typing import Any

from navil.llm import extract_json
from navil.llm.client import LLMClient

logger = logging.getLogger(__name__)

SELF_HEALING_SYSTEM_PROMPT = """You are a security automation engine for MCP Guardian (navil).
Given anomaly alerts and current policy, suggest specific remediation actions.

Respond with ONLY valid JSON (no markdown fences, no explanation).
Keep reasons brief (one sentence).
Schema:
{
  "summary": "one-sentence summary",
  "risk_assessment": "CRITICAL | HIGH | MEDIUM | LOW",
  "actions": [
    {
      "type": "policy_update | threshold_adjustment | credential_rotation
              | agent_block | alert_escalation",
      "target": "agent or tool name",
      "value": "new value or action",
      "reason": "brief reason",
      "confidence": 0.0-1.0,
      "reversible": true/false
    }
  ]
}
Put summary and risk_assessment BEFORE actions."""


class SelfHealingEngine:
    """Generates and optionally applies self-healing remediations.

    Can operate in two modes:
    - Suggestion mode (default): generates suggestions for operator review
    - Auto-apply mode: automatically applies high-confidence reversible actions
    """

    def __init__(
        self,
        client: LLMClient | None = None,
        auto_apply: bool = False,
        auto_apply_confidence_threshold: float = 0.9,
        **client_kwargs: Any,
    ) -> None:
        self.client = client or LLMClient(**client_kwargs)
        self.auto_apply = auto_apply
        self.auto_apply_threshold = auto_apply_confidence_threshold
        self.pending_actions: list[dict[str, Any]] = []
        self.applied_actions: list[dict[str, Any]] = []

    def suggest_remediation(
        self,
        alerts: list[dict[str, Any]],
        current_policy: dict[str, Any],
        baselines: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate remediation suggestions based on alerts and current state."""
        context = {
            "alerts": alerts,
            "current_policy": current_policy,
            "baselines": baselines or {},
        }

        # Self-healing needs more tokens than default (1024) for detailed actions
        prev_max = getattr(self.client, "max_tokens", 1024)
        if isinstance(prev_max, int) and prev_max < 4096:
            self.client.max_tokens = 4096
        try:
            response = self.client.complete(
                SELF_HEALING_SYSTEM_PROMPT,
                f"Analyze and suggest remediations:\n\n{json.dumps(context, indent=2)}",
            )
        finally:
            self.client.max_tokens = prev_max

        try:
            suggestions = json.loads(extract_json(response))
        except (json.JSONDecodeError, ValueError):
            suggestions = {
                "actions": [],
                "summary": response[:500],
                "risk_assessment": "UNKNOWN",
            }

        self.pending_actions.extend(suggestions.get("actions", []))
        return suggestions

    def apply_action(self, action: dict[str, Any], policy_engine: Any, detector: Any) -> bool:
        """Apply a single remediation action.

        Returns True if applied successfully.
        """
        action_type = action.get("type", "")
        target = action.get("target", "")
        value = action.get("value", {})

        try:
            if action_type == "threshold_adjustment":
                if (
                    hasattr(detector, "adaptive_baselines")
                    and target in detector.adaptive_baselines
                ):
                    ab = detector.adaptive_baselines[target]
                    if isinstance(value, dict) and "rate_multiplier" in value:
                        ab.rate_threshold_multiplier = float(value["rate_multiplier"])
                    elif isinstance(value, dict) and "data_multiplier" in value:
                        ab.data_threshold_multiplier = float(value["data_multiplier"])

            elif action_type == "policy_update":
                if hasattr(policy_engine, "policy"):
                    agents = policy_engine.policy.setdefault("agents", {})
                    if target in agents and isinstance(value, dict):
                        agents[target].update(value)

            elif action_type == "agent_block" and hasattr(policy_engine, "policy"):
                agents = policy_engine.policy.setdefault("agents", {})
                agents[target] = {
                    "tools_allowed": [],
                    "tools_denied": ["*"],
                }

            # Clear alerts for the remediated agent so re-analysis
            # reflects the updated state.
            if hasattr(detector, "alerts") and target:
                detector.alerts = [a for a in detector.alerts if a.agent_name != target]

            self.applied_actions.append(action)
            logger.info(f"Self-healing action applied: {action_type} on {target}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply self-healing action: {e}")
            return False

    def auto_remediate(self, policy_engine: Any, detector: Any) -> list[dict[str, Any]]:
        """Auto-apply pending actions above the confidence threshold.

        Only applies actions that are:
        - Above the confidence threshold
        - Marked as reversible
        """
        applied = []
        remaining = []

        for action in self.pending_actions:
            confidence = action.get("confidence", 0.0)
            reversible = action.get("reversible", False)

            if self.auto_apply and confidence >= self.auto_apply_threshold and reversible:
                if self.apply_action(action, policy_engine, detector):
                    applied.append(action)
                else:
                    remaining.append(action)
            else:
                remaining.append(action)

        self.pending_actions = remaining
        return applied

    def full_auto_remediate(
        self,
        alerts: list[dict[str, Any]],
        current_policy: dict[str, Any],
        baselines: dict[str, Any] | None,
        policy_engine: Any,
        detector: Any,
        confidence_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Run full auto-remediation cycle: analyze, apply safe actions, report.

        Steps:
        1. Call suggest_remediation() to get LLM analysis
        2. Partition actions into auto-applicable (high confidence + reversible)
           vs. manual-review
        3. Apply auto-applicable actions
        4. Check remaining alerts to determine post-remediation status

        Returns dict with keys:
          - initial_analysis: {summary, risk_assessment}
          - auto_applied: list of actions that were auto-applied
          - failed_to_apply: list of actions that failed during apply
          - manual_review: list of actions needing human review
          - post_status: {healthy: bool, remaining_alert_count: int}
          - llm_calls_used: int (for billing)
        """
        threshold = confidence_threshold or self.auto_apply_threshold
        llm_calls = 0

        # Step 1: Analyze
        suggestion = self.suggest_remediation(alerts, current_policy, baselines)
        llm_calls += 1

        initial_analysis = {
            "summary": suggestion.get("summary", ""),
            "risk_assessment": suggestion.get("risk_assessment", "UNKNOWN"),
        }

        actions = suggestion.get("actions", [])
        if not actions:
            remaining_alerts = detector.get_alerts() if hasattr(detector, "get_alerts") else []
            return {
                "initial_analysis": initial_analysis,
                "auto_applied": [],
                "failed_to_apply": [],
                "manual_review": [],
                "post_status": {
                    "healthy": len(remaining_alerts) == 0,
                    "remaining_alert_count": len(remaining_alerts),
                },
                "llm_calls_used": llm_calls,
            }

        # Step 2: Partition actions
        auto_eligible: list[dict[str, Any]] = []
        manual_review: list[dict[str, Any]] = []
        for action in actions:
            confidence = action.get("confidence", 0.0)
            reversible = action.get("reversible", False)
            if confidence >= threshold and reversible:
                auto_eligible.append(action)
            else:
                manual_review.append(action)

        # Step 3: Apply auto-eligible actions
        auto_applied: list[dict[str, Any]] = []
        failed_to_apply: list[dict[str, Any]] = []
        for action in auto_eligible:
            if self.apply_action(action, policy_engine, detector):
                auto_applied.append(action)
            else:
                failed_to_apply.append(action)

        # Step 4: Check post-remediation status
        remaining_alerts = detector.get_alerts() if hasattr(detector, "get_alerts") else []

        # Clean up pending_actions populated by suggest_remediation
        handled = set(id(a) for a in auto_applied + failed_to_apply)
        self.pending_actions = [a for a in self.pending_actions if id(a) not in handled]

        return {
            "initial_analysis": initial_analysis,
            "auto_applied": auto_applied,
            "failed_to_apply": failed_to_apply,
            "manual_review": manual_review,
            "post_status": {
                "healthy": len(remaining_alerts) == 0,
                "remaining_alert_count": len(remaining_alerts),
            },
            "llm_calls_used": llm_calls,
        }
