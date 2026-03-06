"""
Agent Credential Lifecycle Manager

Manages generation, rotation, revocation, and lifecycle of credentials
for agent-to-service communication.
Implements Just-In-Time (JIT) credential provisioning and comprehensive audit logging.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt

logger = logging.getLogger(__name__)


class CredentialStatus:
    """Credential lifecycle status constants."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INACTIVE = "INACTIVE"


@dataclass
class CredentialAuditLog:
    """Record of credential operation for audit trail."""

    timestamp: str
    token_id: str
    agent_name: str
    operation: str  # issued, rotated, revoked, accessed, expired
    details: str
    ip_address: str | None = None


@dataclass
class Credential:
    """Represents an issued credential."""

    token_id: str
    agent_name: str
    scope: str  # e.g., "read:tools write:logs"
    token: str  # JWT token
    issued_at: str
    expires_at: str
    status: str
    rotation_count: int = 0
    last_used: str | None = None
    used_count: int = 0
    secret_hash: str = ""  # Hash of token for verification without storing plaintext


class CredentialManager:
    """
    Manages credential lifecycle for MCP agent-to-service communication.

    Features:
    - JWT token generation with custom claims
    - Credential rotation policies
    - Just-In-Time (JIT) credential provisioning
    - Usage tracking and monitoring
    - Comprehensive audit logging
    - Revocation support
    """

    def __init__(
        self,
        secret_key: str = "",
        audit_log_path: str | None = None,
    ) -> None:
        """
        Initialize credential manager.

        Args:
            secret_key: Secret key for JWT signing (if empty, generates secure key)
            audit_log_path: Path to write audit logs (None disables file logging)
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.audit_log_path: Path | None = Path(audit_log_path) if audit_log_path else None
        self.credentials: dict[str, Credential] = {}
        self.rotation_policies: dict[str, dict[str, Any]] = {}

    def issue_credential(
        self,
        agent_name: str,
        scope: str,
        ttl_seconds: int = 3600,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Issue a new credential for an agent.

        Args:
            agent_name: Name of the agent
            scope: Permission scope (e.g., "read:tools write:logs")
            ttl_seconds: Time to live in seconds (default 1 hour)
            metadata: Additional metadata to include in token

        Returns:
            Dictionary containing token and credential information
        """
        token_id = self._generate_token_id()
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(seconds=ttl_seconds)

        # Create JWT payload
        payload = {
            "token_id": token_id,
            "agent_name": agent_name,
            "scope": scope,
            "iat": issued_at.isoformat(),
            "exp": expires_at.isoformat(),
            **(metadata or {}),
        }

        # Sign JWT
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")

        # Store credential
        credential = Credential(
            token_id=token_id,
            agent_name=agent_name,
            scope=scope,
            token=token,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
            status=CredentialStatus.ACTIVE,
            secret_hash=self._hash_token(token),
        )

        self.credentials[token_id] = credential

        # Log operation
        self._log_audit(
            token_id=token_id,
            agent_name=agent_name,
            operation="issued",
            details=f"Credential issued with scope: {scope}, TTL: {ttl_seconds}s",
        )

        logger.info(f"Issued credential {token_id} for agent {agent_name}")

        return {
            "token_id": token_id,
            "token": token,
            "agent_name": agent_name,
            "scope": scope,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_seconds": ttl_seconds,
        }

    def rotate_credential(self, token_id: str) -> dict[str, Any]:
        """
        Rotate an existing credential (issue new token, revoke old).

        Args:
            token_id: ID of credential to rotate

        Returns:
            Dictionary containing new token information
        """
        if token_id not in self.credentials:
            raise ValueError(f"Credential not found: {token_id}")

        old_credential = self.credentials[token_id]

        if old_credential.status == CredentialStatus.REVOKED:
            raise ValueError(f"Cannot rotate revoked credential: {token_id}")

        # Issue new credential with same scope
        new_cred_info = self.issue_credential(
            agent_name=old_credential.agent_name,
            scope=old_credential.scope,
            ttl_seconds=int(
                (
                    datetime.fromisoformat(old_credential.expires_at) - datetime.now(timezone.utc)
                ).total_seconds()
            ),
        )

        # Update old credential status
        old_credential.status = CredentialStatus.EXPIRED
        self.credentials[token_id] = old_credential

        # Log rotation
        self._log_audit(
            token_id=token_id,
            agent_name=old_credential.agent_name,
            operation="rotated",
            details=f"Rotated to new credential: {new_cred_info['token_id']}",
        )

        logger.info(f"Rotated credential {token_id}")

        return new_cred_info

    def revoke_credential(self, token_id: str, reason: str = "Manual revocation") -> bool:
        """
        Revoke a credential immediately.

        Args:
            token_id: ID of credential to revoke
            reason: Reason for revocation

        Returns:
            True if revocation successful
        """
        if token_id not in self.credentials:
            raise ValueError(f"Credential not found: {token_id}")

        credential = self.credentials[token_id]
        credential.status = CredentialStatus.REVOKED
        self.credentials[token_id] = credential

        self._log_audit(
            token_id=token_id,
            agent_name=credential.agent_name,
            operation="revoked",
            details=f"Revoked: {reason}",
        )

        logger.info(f"Revoked credential {token_id}: {reason}")
        return True

    def verify_credential(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a token.

        Args:
            token: JWT token to verify

        Returns:
            Dictionary containing decoded payload

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            token_id = payload.get("token_id")
            if token_id and token_id in self.credentials:
                credential = self.credentials[token_id]
                if credential.status == CredentialStatus.REVOKED:
                    raise jwt.InvalidTokenError("Credential has been revoked")

            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")  # noqa: B904
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {e!s}")  # noqa: B904

    def record_usage(self, token_id: str, ip_address: str | None = None) -> None:
        """
        Record usage of a credential.

        Args:
            token_id: ID of credential being used
            ip_address: IP address of usage (optional)
        """
        if token_id not in self.credentials:
            logger.warning(f"Usage recorded for unknown credential: {token_id}")
            return

        credential = self.credentials[token_id]
        credential.last_used = datetime.now(timezone.utc).isoformat()
        credential.used_count += 1
        self.credentials[token_id] = credential

        self._log_audit(
            token_id=token_id,
            agent_name=credential.agent_name,
            operation="accessed",
            details=f"Credential used (total uses: {credential.used_count})",
            ip_address=ip_address,
        )

    def set_rotation_policy(
        self, agent_name: str, rotate_after_days: int, max_age_days: int
    ) -> None:
        """
        Set rotation policy for an agent.

        Args:
            agent_name: Name of agent
            rotate_after_days: Days before automatic rotation
            max_age_days: Maximum age before revocation
        """
        self.rotation_policies[agent_name] = {
            "rotate_after_days": rotate_after_days,
            "max_age_days": max_age_days,
        }

        logger.info(
            f"Set rotation policy for {agent_name}: "
            f"rotate after {rotate_after_days}d, max age {max_age_days}d"
        )

    def check_rotation_needed(self) -> list[str]:
        """
        Check which credentials need rotation.

        Returns:
            List of token IDs that need rotation
        """
        needs_rotation = []
        now = datetime.now(timezone.utc)

        for token_id, credential in self.credentials.items():
            agent_name = credential.agent_name

            if agent_name not in self.rotation_policies:
                continue

            policy = self.rotation_policies[agent_name]
            issued_at = datetime.fromisoformat(credential.issued_at)
            days_old = (now - issued_at).days

            if days_old >= policy["rotate_after_days"]:
                needs_rotation.append(token_id)

        return needs_rotation

    def cleanup_expired(self) -> int:
        """
        Clean up expired and revoked credentials older than 90 days.

        Returns:
            Number of credentials removed
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=90)
        removed = 0

        token_ids_to_remove = []
        for token_id, credential in self.credentials.items():
            if credential.status in [
                CredentialStatus.EXPIRED,
                CredentialStatus.REVOKED,
            ]:
                issued_at = datetime.fromisoformat(credential.issued_at)
                if issued_at < cutoff:
                    token_ids_to_remove.append(token_id)

        for token_id in token_ids_to_remove:
            del self.credentials[token_id]
            removed += 1

        logger.info(f"Cleaned up {removed} expired credentials")
        return removed

    def get_credential_info(self, token_id: str) -> dict[str, Any]:
        """
        Get information about a credential.

        Args:
            token_id: ID of credential

        Returns:
            Dictionary with credential information (token excluded)
        """
        if token_id not in self.credentials:
            return {}

        cred = self.credentials[token_id]
        return {
            "token_id": cred.token_id,
            "agent_name": cred.agent_name,
            "scope": cred.scope,
            "issued_at": cred.issued_at,
            "expires_at": cred.expires_at,
            "status": cred.status,
            "rotation_count": cred.rotation_count,
            "last_used": cred.last_used,
            "used_count": cred.used_count,
        }

    def list_credentials(
        self, agent_name: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List credentials with optional filtering.

        Args:
            agent_name: Filter by agent name
            status: Filter by status

        Returns:
            List of credential information dictionaries
        """
        result = []

        for cred in self.credentials.values():
            if agent_name and cred.agent_name != agent_name:
                continue
            if status and cred.status != status:
                continue

            result.append(self.get_credential_info(cred.token_id))

        return result

    def export_audit_log(self, start_time: str | None = None) -> list[dict[str, Any]]:
        """
        Export audit log entries.

        Args:
            start_time: ISO format timestamp to filter from

        Returns:
            List of audit log entries
        """
        logs: list[dict[str, Any]] = []
        if self.audit_log_path is None or not self.audit_log_path.exists():
            return logs

        start_dt = None
        if start_time:
            start_dt = datetime.fromisoformat(start_time)

        with open(self.audit_log_path) as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if start_dt:
                        log_time = datetime.fromisoformat(log_entry["timestamp"])
                        if log_time < start_dt:
                            continue
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue

        return logs

    def _generate_token_id(self) -> str:
        """Generate a unique token ID."""
        return f"cred_{secrets.token_hex(12)}"

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage without plaintext."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _log_audit(
        self,
        token_id: str,
        agent_name: str,
        operation: str,
        details: str,
        ip_address: str | None = None,
    ) -> None:
        """Write entry to audit log."""
        log_entry = CredentialAuditLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            token_id=token_id,
            agent_name=agent_name,
            operation=operation,
            details=details,
            ip_address=ip_address,
        )

        if self.audit_log_path is not None:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(asdict(log_entry)) + "\n")
