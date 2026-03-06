"""Tests for the MCP Security Scanner."""

from __future__ import annotations

from typing import Any

import pytest

from navil.scanner import MCPSecurityScanner, RiskLevel


@pytest.fixture
def scanner() -> MCPSecurityScanner:
    return MCPSecurityScanner()


def test_scan_secure_config(
    scanner: MCPSecurityScanner, config_file, sample_secure_config: dict[str, Any]
) -> None:
    """Secure configuration should have high score and zero vulnerabilities."""
    path = config_file(sample_secure_config)
    result = scanner.scan(path)

    assert result["status"] == "completed"
    assert result["security_score"] > 70
    assert result["total_vulnerabilities"] == 0


def test_plaintext_credentials_detection(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect plaintext passwords and API keys."""
    config = {
        "server": {"name": "Test Server"},
        "database": {
            "password='supersecret123'": "value",
            "api_key='sk-1234567890abcdef'": "value",
        },
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    assert len(result["vulnerabilities"]) > 0


def test_over_privileged_permissions(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect wildcard permissions."""
    config = {
        "server": {"name": "Test Server"},
        "tools": [{"name": "dangerous_tool", "permissions": ["*"]}],
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    vulns = result["vulnerabilities"]
    assert any("privilege" in v.get("title", "").lower() for v in vulns)


def test_missing_authentication(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect missing authentication configuration."""
    config = {"server": {"name": "Test Server"}, "tools": []}
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    vulns = result["vulnerabilities"]
    assert any("authentication" in v.get("title", "").lower() for v in vulns)


def test_unencrypted_protocol(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect HTTP (unencrypted) protocol."""
    config = {
        "server": {"name": "Test Server", "protocol": "http"},
        "authentication": {"type": "api_key"},
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    vulns = result["vulnerabilities"]
    assert any("encrypted" in v.get("title", "").lower() for v in vulns)


def test_malicious_patterns_detection(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect malicious patterns like backdoor references."""
    config = {
        "server": {"name": "Test Server"},
        "tools": [
            {
                "name": "backdoor_tool",
                "description": "This tool has a hidden backdoor access mechanism",
            }
        ],
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    vulns = result["vulnerabilities"]
    assert any("malicious" in v.get("title", "").lower() for v in vulns)


def test_aws_key_detection(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect AWS access keys."""
    config = {
        "server": {"name": "Test Server"},
        "aws_credentials": "AKIA1234567890123456",
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0
    vulns = result["vulnerabilities"]
    assert any("credential" in v.get("title", "").lower() for v in vulns)


def test_jwt_token_detection(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect JWT tokens in config."""
    config = {
        "server": {"name": "Test Server"},
        "token": (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
            ".TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        ),
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] > 0


def test_nonexistent_file(scanner: MCPSecurityScanner) -> None:
    """Should handle nonexistent configuration file gracefully."""
    result = scanner.scan("/nonexistent/path/config.json")

    assert result["status"] == "error"
    assert result["security_score"] == 0


def test_security_score_calculation(scanner: MCPSecurityScanner, config_file) -> None:
    """Secure config should produce a score between 70 and 100."""
    config = {
        "server": {"protocol": "https", "verified": True},
        "authentication": {"type": "mTLS"},
        "tools": [{"name": "safe", "permissions": ["read"]}],
    }
    path = config_file(config)
    result = scanner.scan(path)

    score = result["security_score"]
    assert score > 70
    assert score <= 100


def test_vulnerability_grouping(scanner: MCPSecurityScanner, config_file) -> None:
    """Vulnerabilities should be grouped by risk level."""
    config = {
        "server": {"protocol": "http"},
        "tools": [{"name": "tool1", "permissions": ["*"]}],
    }
    path = config_file(config)
    result = scanner.scan(path)

    vulns_by_level = result["vulnerabilities_by_level"]
    assert "CRITICAL" in vulns_by_level
    assert "HIGH" in vulns_by_level
    assert "MEDIUM" in vulns_by_level


def test_multiple_vulnerabilities(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect multiple vulnerabilities in a single config."""
    config = {
        "server": {"protocol": "http"},
        "authentication": {"api_key": "secret123"},
        "tools": [
            {
                "name": "tool1",
                "permissions": ["*"],
                "allowed_actions": ["read", "destroy_data", "exfiltrate"],
            }
        ],
    }
    path = config_file(config)
    result = scanner.scan(path)

    assert result["total_vulnerabilities"] >= 3


def test_recommendation_generation(scanner: MCPSecurityScanner, config_file) -> None:
    """Should generate a non-empty recommendation."""
    config = {
        "server": {"protocol": "https", "verified": True},
        "authentication": {"type": "mTLS"},
        "tools": [],
    }
    path = config_file(config)
    result = scanner.scan(path)

    recommendation = result.get("recommendation", "")
    assert recommendation
    assert len(recommendation) > 0


def test_file_system_access_without_restrictions(scanner: MCPSecurityScanner, config_file) -> None:
    """Should detect unrestricted file system access."""
    config = {
        "server": {"name": "Test Server"},
        "tools": [{"name": "file_system", "permissions": ["file_system"]}],
    }
    path = config_file(config)
    result = scanner.scan(path)

    vulns = result["vulnerabilities"]
    assert any("file system" in v.get("description", "").lower() for v in vulns)


def test_risk_levels_exist() -> None:
    """All expected risk levels should exist."""
    levels = [
        RiskLevel.CRITICAL,
        RiskLevel.HIGH,
        RiskLevel.MEDIUM,
        RiskLevel.LOW,
        RiskLevel.INFO,
    ]
    for level in levels:
        assert level.value is not None
