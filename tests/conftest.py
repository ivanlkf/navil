"""Shared test fixtures for the Navil (MCP Guardian) test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def sample_secure_config() -> dict[str, Any]:
    """A secure MCP server configuration with no vulnerabilities."""
    return {
        "server": {"name": "Secure Server", "protocol": "https", "verified": True},
        "authentication": {"type": "mTLS", "key_rotation": True},
        "tools": [
            {
                "name": "safe_tool",
                "permissions": ["read"],
                "restrictions": {"max_size": "10MB"},
                "rate_limit": 100,
            }
        ],
    }


@pytest.fixture
def sample_vulnerable_config() -> dict[str, Any]:
    """A vulnerable MCP server configuration."""
    return {
        "server": {"protocol": "http"},
        "tools": [
            {"name": "dangerous_tool", "permissions": ["*"]},
            {"name": "fs", "permissions": ["file_system"]},
        ],
    }


@pytest.fixture
def config_file(tmp_path: Path):
    """Factory fixture: write a dict to a temp JSON file and return the path."""

    def _make(config: dict[str, Any]) -> str:
        path = tmp_path / "config.json"
        path.write_text(json.dumps(config))
        return str(path)

    return _make


@pytest.fixture
def sample_policy_dict() -> dict[str, Any]:
    """A sample policy for testing PolicyEngine."""
    return {
        "version": "1.0",
        "agents": {
            "reader": {
                "tools_allowed": ["logs", "metrics"],
                "tools_denied": ["admin_panel"],
                "rate_limit_per_hour": 10,
                "data_clearance": "INTERNAL",
                "action_restrictions": {"logs": ["delete"]},
            },
            "admin": {
                "tools_allowed": ["*"],
                "tools_denied": [],
                "rate_limit_per_hour": 10000,
                "data_clearance": "RESTRICTED",
                "action_restrictions": {},
            },
        },
        "tools": {
            "logs": {"allowed_actions": ["read", "export"]},
            "metrics": {"allowed_actions": ["read"]},
            "admin_panel": {"allowed_actions": ["read", "write"]},
        },
        "suspicious_patterns": [
            {
                "name": "test_pattern",
                "tool": "logs",
                "actions": ["export"],
                "conditions": {},
            }
        ],
    }


@pytest.fixture
def policy_file(tmp_path: Path, sample_policy_dict: dict[str, Any]) -> str:
    """Write the sample policy to a YAML file and return its path."""
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.dump(sample_policy_dict))
    return str(path)
