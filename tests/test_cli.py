"""Tests for the Navil CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from navil.cli import main


@pytest.fixture
def vulnerable_config_path() -> str:
    """Path to the bundled vulnerable sample config."""
    p = Path(__file__).parent.parent / "navil" / "sample_configs" / "vulnerable_server.json"
    assert p.exists(), f"Sample config not found at {p}"
    return str(p)


@pytest.fixture
def secure_config_path() -> str:
    """Path to the bundled secure sample config."""
    p = Path(__file__).parent.parent / "navil" / "sample_configs" / "secure_server.json"
    assert p.exists(), f"Sample config not found at {p}"
    return str(p)


def test_scan_vulnerable_config(vulnerable_config_path: str, capsys) -> None:
    """Scanning a vulnerable config should return exit code 1 (score < 60)."""
    with patch.object(sys, "argv", ["navil", "scan", vulnerable_config_path]):
        exit_code = main()
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Security Score" in captured.out


def test_scan_secure_config(secure_config_path: str, capsys) -> None:
    """Scanning a secure config should print a Security Score."""
    with patch.object(sys, "argv", ["navil", "scan", secure_config_path]):
        main()
    captured = capsys.readouterr()
    assert "Security Score" in captured.out


def test_scan_nonexistent_file(capsys) -> None:
    """Scanning a nonexistent file should return exit code 1."""
    with patch.object(sys, "argv", ["navil", "scan", "/nonexistent.json"]):
        exit_code = main()
    assert exit_code == 1


def test_scan_with_output(vulnerable_config_path: str, tmp_path, capsys) -> None:
    """Scan with -o should write a JSON report file."""
    out_file = str(tmp_path / "report.json")
    with patch.object(sys, "argv", ["navil", "scan", vulnerable_config_path, "-o", out_file]):
        main()
    report = json.loads((tmp_path / "report.json").read_text())
    assert "vulnerabilities" in report


def test_no_command_prints_help(capsys) -> None:
    """Running without a command should print help and return 1."""
    with patch.object(sys, "argv", ["navil"]):
        exit_code = main()
    assert exit_code == 1


def test_report_command(capsys) -> None:
    """Report command should output JSON with summary."""
    with patch.object(sys, "argv", ["navil", "report"]):
        exit_code = main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "total_credentials" in captured.out


def test_policy_check_command(capsys) -> None:
    """Policy check should print a Policy Decision."""
    with patch.object(
        sys,
        "argv",
        [
            "navil",
            "policy",
            "check",
            "--tool",
            "file_system",
            "--agent",
            "default",
            "--action",
            "read",
        ],
    ):
        main()
    captured = capsys.readouterr()
    assert "Policy Decision" in captured.out
