"""
Navil (MCP Guardian) -- Supply-chain security for MCP (Model Context Protocol) servers.

Provides configuration scanning, credential lifecycle management,
policy enforcement, behavioral anomaly detection, adaptive baselines,
ML-powered detection, and LLM-powered analysis.
"""

from __future__ import annotations

# Optional compatibility checks
from navil._compat import has_llm, has_ml

# Adaptive module (always available, zero extra deps)
from navil.adaptive.baselines import AgentAdaptiveBaseline, EMABaseline
from navil.adaptive.confidence import AnomalyScore, ConfidenceLevel
from navil.adaptive.feedback import FeedbackLoop
from navil.adaptive.pattern_store import PatternStore
from navil.anomaly_detector import AnomalyAlert, AnomalyType, BehavioralAnomalyDetector
from navil.credential_manager import Credential, CredentialManager, CredentialStatus
from navil.policy_engine import PolicyDecision, PolicyEngine, PolicyEvaluationResult
from navil.scanner import MCPSecurityScanner, RiskLevel, Vulnerability

__version__ = "0.1.0"
__author__ = "Pantheon Lab Limited"
__all__ = [
    # Core
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
    # Adaptive (always available)
    "EMABaseline",
    "AgentAdaptiveBaseline",
    "AnomalyScore",
    "ConfidenceLevel",
    "FeedbackLoop",
    "PatternStore",
    # Compatibility
    "has_ml",
    "has_llm",
]
