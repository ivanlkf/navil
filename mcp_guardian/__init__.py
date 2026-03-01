"""
Navil (MCP Guardian) -- Supply-chain security for MCP (Model Context Protocol) servers.

Provides configuration scanning, credential lifecycle management,
policy enforcement, and behavioral anomaly detection.
"""

from __future__ import annotations

from mcp_guardian.anomaly_detector import AnomalyAlert, AnomalyType, BehavioralAnomalyDetector
from mcp_guardian.credential_manager import Credential, CredentialManager, CredentialStatus
from mcp_guardian.policy_engine import PolicyDecision, PolicyEngine, PolicyEvaluationResult
from mcp_guardian.scanner import MCPSecurityScanner, RiskLevel, Vulnerability

__version__ = "0.1.0"
__author__ = "Pantheon Lab Limited"
__all__ = [
    "MCPSecurityScanner",
    "RiskLevel",
    "Vulnerability",
    "CredentialManager",
    "Credential",
    "CredentialStatus",
    "PolicyEngine",
    "PolicyDecision",
    "PolicyEvaluationResult",
    "BehavioralAnomalyDetector",
    "AnomalyAlert",
    "AnomalyType",
]
