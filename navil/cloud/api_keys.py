# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""API key management for proxy-to-cloud authentication.

Customers generate API keys in the dashboard, then configure their proxy
with ``--cloud-key nvl_xxxx``.  The proxy sends telemetry to the cloud
API using this key for authentication.

Keys are prefixed with ``nvl_`` for easy identification (like ``sk_`` for
Stripe).  Only the SHA-256 hash is stored; the raw key is shown once at
creation and never again.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ApiKeyInfo:
    """Public API key information (never includes the raw key)."""

    id: int
    key_prefix: str
    name: str
    scopes: list[str]
    last_used_at: str | None
    expires_at: str | None
    revoked: bool
    created_at: str


def _hash_key(raw_key: str) -> str:
    """SHA-256 hash of a raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_raw_key() -> str:
    """Generate a new raw API key: nvl_ + 48 hex characters."""
    return "nvl_" + secrets.token_hex(24)


class ApiKeyManager:
    """Manage customer API keys for proxy authentication."""

    def create_key(
        self,
        user_id: str,
        name: str = "Default",
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[int, str]:
        """Create a new API key.

        Returns ``(key_id, raw_key)``.  The raw key is shown once and
        never stored — only its SHA-256 hash is persisted.
        """
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        raw_key = _generate_raw_key()
        key_hash = _hash_key(raw_key)
        key_prefix = raw_key[:12]  # "nvl_" + first 8 hex chars
        scopes = scopes or ["ingest"]

        expires_at = None
        if expires_in_days:
            expires_at = dt.datetime.utcnow() + dt.timedelta(days=expires_in_days)

        with get_session() as session:
            row = ApiKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                scopes=json.dumps(scopes),
                expires_at=expires_at,
            )
            session.add(row)
            session.flush()
            key_id = row.id

        return key_id, raw_key

    def verify_key(self, raw_key: str) -> tuple[str, list[str]] | None:
        """Verify an API key and return ``(user_id, scopes)`` or None.

        Also updates ``last_used_at`` timestamp.
        """
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        if not raw_key.startswith("nvl_"):
            return None

        key_hash = _hash_key(raw_key)

        try:
            with get_session() as session:
                row = (
                    session.query(ApiKey)
                    .filter(
                        ApiKey.key_hash == key_hash,
                        ApiKey.revoked.is_(False),
                    )
                    .first()
                )
                if row is None:
                    return None

                # Check expiry
                if row.expires_at and row.expires_at < dt.datetime.utcnow():
                    return None

                # Update last used
                row.last_used_at = dt.datetime.utcnow()

                scopes: list[str] = json.loads(row.scopes)
                return row.user_id, scopes
        except Exception:
            logger.exception("API key verification failed")
            return None

    def list_keys(self, user_id: str) -> list[ApiKeyInfo]:
        """List all API keys for a user (never returns raw keys)."""
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            rows = (
                session.query(ApiKey)
                .filter(ApiKey.user_id == user_id)
                .order_by(ApiKey.created_at.desc())
                .all()
            )
            return [
                ApiKeyInfo(
                    id=r.id,
                    key_prefix=r.key_prefix,
                    name=r.name,
                    scopes=json.loads(r.scopes),
                    last_used_at=r.last_used_at.isoformat() if r.last_used_at else None,
                    expires_at=r.expires_at.isoformat() if r.expires_at else None,
                    revoked=r.revoked,
                    created_at=r.created_at.isoformat() if r.created_at else "",
                )
                for r in rows
            ]

    def revoke_key(self, user_id: str, key_id: int) -> bool:
        """Revoke an API key.  Returns True if found and revoked."""
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            row = (
                session.query(ApiKey)
                .filter(ApiKey.id == key_id, ApiKey.user_id == user_id)
                .first()
            )
            if row is None:
                return False
            row.revoked = True
            return True

    def count_keys(self, user_id: str) -> int:
        """Count active (non-revoked) keys for a user."""
        from navil.cloud.database import get_session
        from navil.cloud.models import ApiKey

        with get_session() as session:
            return (
                session.query(ApiKey)
                .filter(
                    ApiKey.user_id == user_id,
                    ApiKey.revoked.is_(False),
                )
                .count()
            )
