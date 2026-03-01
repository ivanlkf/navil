"""
MCP Server Security Scanner

Scans MCP server configuration files for common vulnerabilities and security issues.
Generates comprehensive security reports with risk assessment and recommendations.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Vulnerability:
    """Represents a detected vulnerability."""
    id: str
    title: str
    description: str
    risk_level: str
    affected_field: str
    remediation: str
    evidence: str = ""


class MCPSecurityScanner:
    """
    Scanner for MCP server configuration files.

    Detects common vulnerabilities including:
    - Plaintext credentials/API keys
    - Over-privileged permissions
    - Missing authentication
    - Unsigned/unverified sources
    - Known malicious patterns
    """

    # Patterns for detecting secrets
    SECRET_PATTERNS = {
        "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]+)['\"]?",
        "password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s\"']+)['\"]?",
        "token": r"(?i)(token|secret)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_\.]+)['\"]?",
        "aws_key": r"(?i)AKIA[0-9A-Z]{16}",
        "private_key": r"(?i)(private[_-]?key|-----begin.*private key)",
        "jwt": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.",
    }

    # Known malicious patterns
    MALICIOUS_PATTERNS = {
        "exfiltration": r"(?i)(exfiltrate|steal|leak|unauthorized.*send|socket.*send.*outside)",
        "privilege_escalation": r"(?i)(escalate|privilege|sudo|root|admin.*grant)",
        "data_destruction": r"(?i)(delete.*all|drop.*database|rm.*-rf|wipe|destroy)",
        "backdoor": r"(?i)(backdoor|hidden.*access|secret.*command|unauthorized.*entry)",
    }

    def __init__(self):
        """Initialize the scanner."""
        self.vulnerabilities: List[Vulnerability] = []
        self.warnings: List[str] = []

    def scan(self, config_path: str) -> Dict[str, Any]:
        """
        Scan an MCP server configuration file.

        Args:
            config_path: Path to the MCP configuration file (JSON format)

        Returns:
            Dictionary containing scan results and security score
        """
        self.vulnerabilities = []
        self.warnings = []

        try:
            config = self._load_config(config_path)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config: {e}")
            return {
                "status": "error",
                "message": f"Failed to load configuration: {str(e)}",
                "security_score": 0,
            }

        # Run all security checks
        self._check_plaintext_credentials(config)
        self._check_permissions(config)
        self._check_authentication(config)
        self._check_server_source(config)
        self._check_malicious_patterns(config)
        self._check_network_security(config)
        self._check_tool_safety(config)

        # Calculate security score
        security_score = self._calculate_score()

        # Generate report
        report = {
            "status": "completed",
            "config_path": str(config_path),
            "security_score": security_score,
            "total_vulnerabilities": len(self.vulnerabilities),
            "vulnerabilities_by_level": self._group_by_risk_level(),
            "vulnerabilities": [asdict(v) for v in self.vulnerabilities],
            "warnings": self.warnings,
            "recommendation": self._get_recommendation(security_score),
        }

        return report

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and parse configuration file."""
        path = Path(config_path)
        if not path.exists():
            raise IOError(f"Configuration file not found: {config_path}")

        with open(path, "r") as f:
            config = json.load(f)
        return config

    def _check_plaintext_credentials(self, config: Dict[str, Any]) -> None:
        """Check for plaintext credentials and API keys."""
        config_str = json.dumps(config)

        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, config_str)
            for match in matches:
                self.vulnerabilities.append(
                    Vulnerability(
                        id=f"CRED-{secret_type.upper()}",
                        title="Plaintext Credential Detected",
                        description=f"Found plaintext {secret_type} in configuration file",
                        risk_level=RiskLevel.CRITICAL.value,
                        affected_field=self._find_field_in_config(config, match.group(0)),
                        remediation="Use environment variables or secure vaults (AWS Secrets Manager, HashiCorp Vault) for credential storage",
                        evidence=f"Detected {secret_type} pattern",
                    )
                )

    def _check_permissions(self, config: Dict[str, Any]) -> None:
        """Check for over-privileged tool permissions."""
        tools = config.get("tools", [])

        for tool in tools:
            if isinstance(tool, dict):
                permissions = tool.get("permissions", [])
                name = tool.get("name", "unknown")

                # Check for overly broad permissions
                dangerous_permissions = ["*", "all", "unrestricted"]
                if any(perm in dangerous_permissions for perm in permissions):
                    self.vulnerabilities.append(
                        Vulnerability(
                            id="PERM-OVERPRIVILEGED",
                            title="Over-Privileged Tool Permissions",
                            description=f"Tool '{name}' has unrestricted permissions",
                            risk_level=RiskLevel.HIGH.value,
                            affected_field=f"tools[*].permissions",
                            remediation="Define specific permissions for each tool following the principle of least privilege",
                            evidence=f"Tool {name} has wildcard permissions",
                        )
                    )

                # Check for file system access without restrictions
                if "file_system" in permissions:
                    if "restrictions" not in tool or not tool.get("restrictions"):
                        self.vulnerabilities.append(
                            Vulnerability(
                                id="PERM-UNRESTRICTED-FS",
                                title="Unrestricted File System Access",
                                description=f"Tool '{name}' has unrestricted file system access",
                                risk_level=RiskLevel.HIGH.value,
                                affected_field=f"tools[*].permissions",
                                remediation="Restrict file system access to specific directories and file types",
                                evidence=f"Tool {name} has file_system permission without restrictions",
                            )
                        )

    def _check_authentication(self, config: Dict[str, Any]) -> None:
        """Check for missing authentication requirements."""
        if "authentication" not in config or not config.get("authentication"):
            self.vulnerabilities.append(
                Vulnerability(
                    id="AUTH-MISSING",
                    title="Missing Authentication Configuration",
                    description="No authentication mechanism configured for MCP server",
                    risk_level=RiskLevel.HIGH.value,
                    affected_field="authentication",
                    remediation="Implement strong authentication (OAuth2, mTLS, API keys) for server access",
                    evidence="Authentication field is missing or empty",
                )
            )
            return

        auth_config = config.get("authentication", {})

        if auth_config.get("type") == "api_key" and not auth_config.get("key_rotation"):
            self.warnings.append(
                "API key authentication configured without key rotation policy"
            )

    def _check_server_source(self, config: Dict[str, Any]) -> None:
        """Check for unsigned or unverified server sources."""
        server = config.get("server", {})

        if "source" in server:
            source = server["source"]
            if not server.get("verified") and not server.get("signature"):
                self.vulnerabilities.append(
                    Vulnerability(
                        id="SRC-UNVERIFIED",
                        title="Unverified Server Source",
                        description="Server binary/source is not cryptographically verified",
                        risk_level=RiskLevel.HIGH.value,
                        affected_field="server.source",
                        remediation="Use signed/verified binaries and implement signature verification before deployment",
                        evidence=f"Server source '{source}' lacks verification metadata",
                    )
                )

    def _check_malicious_patterns(self, config: Dict[str, Any]) -> None:
        """Check for known malicious patterns in tool definitions."""
        config_str = json.dumps(config).lower()

        for pattern_type, pattern in self.MALICIOUS_PATTERNS.items():
            if re.search(pattern, config_str):
                self.vulnerabilities.append(
                    Vulnerability(
                        id=f"MAL-{pattern_type.upper()}",
                        title=f"Malicious Pattern Detected: {pattern_type.title()}",
                        description=f"Configuration contains patterns associated with {pattern_type}",
                        risk_level=RiskLevel.CRITICAL.value,
                        affected_field="tools",
                        remediation="Review tool definitions and remove any suspicious or unauthorized functionality",
                        evidence=f"Pattern matching '{pattern_type}' detected in configuration",
                    )
                )

    def _check_network_security(self, config: Dict[str, Any]) -> None:
        """Check for insecure network configurations."""
        server = config.get("server", {})

        # Check for unencrypted communication
        if "protocol" in server:
            protocol = server.get("protocol", "").lower()
            if protocol == "http":
                self.vulnerabilities.append(
                    Vulnerability(
                        id="NET-UNENCRYPTED",
                        title="Unencrypted Communication",
                        description="Server is configured to use HTTP instead of HTTPS",
                        risk_level=RiskLevel.HIGH.value,
                        affected_field="server.protocol",
                        remediation="Use HTTPS/TLS for all server communications",
                        evidence="Protocol set to HTTP",
                    )
                )

        # Check for exposed ports
        if "port" in server:
            port = server.get("port")
            if port in [80, 8080, 3000]:
                self.warnings.append(f"Server exposed on commonly targeted port {port}")

    def _check_tool_safety(self, config: Dict[str, Any]) -> None:
        """Check for unsafe tool configurations."""
        tools = config.get("tools", [])

        for tool in tools:
            if not isinstance(tool, dict):
                continue

            name = tool.get("name", "unknown")

            # Check for tools with command injection risks
            if "command" in tool:
                command = tool.get("command", "")
                if "${" in command or "$(" in command:
                    self.warnings.append(
                        f"Tool '{name}' uses variable substitution in commands - ensure proper input validation"
                    )

            # Check for tools without rate limiting
            if "rate_limit" not in tool:
                self.warnings.append(
                    f"Tool '{name}' has no rate limiting configured"
                )

    def _find_field_in_config(self, config: Dict[str, Any], evidence: str) -> str:
        """Find the field path in config that matches evidence."""
        # Simple implementation - in production, would do proper path tracking
        return "unknown"

    def _calculate_score(self) -> int:
        """Calculate security score from 0-100."""
        if not self.vulnerabilities:
            return 100

        # Weight vulnerabilities by severity
        score = 100
        for vuln in self.vulnerabilities:
            if vuln.risk_level == RiskLevel.CRITICAL.value:
                score -= 25
            elif vuln.risk_level == RiskLevel.HIGH.value:
                score -= 15
            elif vuln.risk_level == RiskLevel.MEDIUM.value:
                score -= 8
            elif vuln.risk_level == RiskLevel.LOW.value:
                score -= 3

        return max(0, score)

    def _group_by_risk_level(self) -> Dict[str, int]:
        """Group vulnerabilities by risk level."""
        groups = {level.value: 0 for level in RiskLevel}
        for vuln in self.vulnerabilities:
            groups[vuln.risk_level] += 1
        return groups

    def _get_recommendation(self, score: int) -> str:
        """Get recommendation based on security score."""
        if score >= 80:
            return "Good security posture. Continue monitoring for updates."
        elif score >= 60:
            return "Address identified vulnerabilities before production deployment."
        elif score >= 40:
            return "Significant security issues detected. Immediate remediation required."
        else:
            return "Critical security issues found. Do not deploy until resolved."
