# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Seed demo data so the dashboard isn't empty on first launch."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from navil.cloud.state import AppState


def seed_demo_data(state: AppState) -> None:
    """Populate the dashboard with realistic demo data."""
    if state.demo_seeded:
        return
    state.demo_seeded = True

    rng = random.Random(42)
    datetime.now(timezone.utc)

    agents: dict[str, dict[str, Any]] = {
        "data-reader": {
            "tools": ["logs", "metrics", "files"],
            "normal_duration": 30,
            "normal_data": 200,
        },
        "code-assistant": {
            "tools": ["code_search", "file_edit", "terminal"],
            "normal_duration": 80,
            "normal_data": 500,
        },
        "admin-bot": {
            "tools": ["admin_panel", "user_mgmt", "config"],
            "normal_duration": 120,
            "normal_data": 1000,
        },
        "monitoring-agent": {
            "tools": ["logs", "alerts", "health_check"],
            "normal_duration": 15,
            "normal_data": 50,
        },
        "deploy-agent": {
            "tools": ["docker", "kubernetes", "ci_pipeline"],
            "normal_duration": 200,
            "normal_data": 2000,
        },
    }

    # Record normal invocations (builds baselines)
    for agent_name, profile in agents.items():
        n_normal = rng.randint(20, 40)
        for _i in range(n_normal):
            tools: list[str] = profile["tools"]  # type: ignore[assignment]
            tool = rng.choice(tools)
            dur_mean = float(profile["normal_duration"])
            data_mean = float(profile["normal_data"])
            duration = max(5, int(rng.gauss(dur_mean, dur_mean * 0.3)))
            data = max(0, int(rng.gauss(data_mean, data_mean * 0.3)))
            state.anomaly_detector.record_invocation(
                agent_name=agent_name,
                tool_name=tool,
                action=rng.choice(["read", "write", "list"]),
                duration_ms=duration,
                data_accessed_bytes=data,
                success=rng.random() > 0.05,
            )

    # Clear the baseline buildup alerts — they're noisy and not interesting
    state.anomaly_detector.alerts.clear()

    # Inject some anomalous behavior for data-reader (data exfiltration)
    for _ in range(5):
        state.anomaly_detector.record_invocation(
            agent_name="data-reader",
            tool_name="files",
            action="read",
            duration_ms=500,
            data_accessed_bytes=50000,  # 250x normal
            success=True,
        )

    # Inject rate spike for monitoring-agent
    for _ in range(30):
        state.anomaly_detector.record_invocation(
            agent_name="monitoring-agent",
            tool_name="logs",
            action="read",
            duration_ms=5,
            data_accessed_bytes=10,
            success=True,
        )

    # Inject privilege escalation for code-assistant
    state.anomaly_detector.record_invocation(
        agent_name="code-assistant",
        tool_name="admin_panel",
        action="write",
        duration_ms=300,
        data_accessed_bytes=5000,
        success=True,
    )

    # Issue some credentials
    for agent_name in agents:
        state.credential_manager.issue_credential(
            agent_name=agent_name,
            scope="read:tools write:logs",
            ttl_seconds=3600,
        )

    # Revoke one credential (the admin-bot's)
    creds = state.credential_manager.list_credentials(agent_name="admin-bot")
    if creds:
        state.credential_manager.revoke_credential(creds[0]["token_id"], reason="Security review")

    # Run some policy checks
    state.policy_engine.check_tool_call("data-reader", "logs", "read")
    state.policy_engine.check_tool_call("code-assistant", "admin_panel", "write")
    state.policy_engine.check_tool_call("admin-bot", "config", "delete")
