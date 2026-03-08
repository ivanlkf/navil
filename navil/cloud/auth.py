# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Authentication middleware for Navil Cloud.

Supports two authentication methods:

1. **Clerk JWT** — for human users accessing the dashboard.
   Requires ``CLERK_SECRET_KEY`` and ``CLERK_ISSUER_URL`` environment variables.

2. **API Key** — for proxy-to-cloud telemetry ingestion.
   Keys start with ``nvl_`` and are verified against the ``api_keys`` table.

Both methods set ``request.state.user_id`` so downstream handlers are
auth-agnostic.

When neither Clerk nor API keys are configured, the middleware is a
transparent no-op for backward compatibility with local development.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

CLERK_SECRET_KEY: str | None = os.environ.get("CLERK_SECRET_KEY")
CLERK_ISSUER_URL: str | None = os.environ.get("CLERK_ISSUER_URL")

# ---------------------------------------------------------------------------
# JWKS client (lazy singleton)
# ---------------------------------------------------------------------------

_jwks_client: Any | None = None


def _get_jwks_client() -> Any | None:
    """Return a cached ``PyJWKClient`` pointing at Clerk's JWKS endpoint."""
    global _jwks_client  # noqa: PLW0603
    if not CLERK_ISSUER_URL:
        return None
    if _jwks_client is None:
        import jwt  # PyJWT — already a project dependency

        jwks_url = f"{CLERK_ISSUER_URL.rstrip('/')}/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
        logger.info("Clerk JWKS client initialised: %s", jwks_url)
    return _jwks_client


def verify_clerk_token(token: str) -> dict[str, Any]:
    """Decode and verify a Clerk-issued JWT.

    Returns the decoded payload dict on success, raises on failure.
    """
    import jwt as pyjwt

    jwks = _get_jwks_client()
    if jwks is None:
        raise RuntimeError("Clerk JWKS client not configured")

    signing_key = jwks.get_signing_key_from_jwt(token)
    payload: dict[str, Any] = pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=CLERK_ISSUER_URL,
        options={"verify_aud": False},  # Clerk doesn't always set aud
    )
    return payload


# ---------------------------------------------------------------------------
# API Key verification
# ---------------------------------------------------------------------------

_api_key_manager: Any | None = None


def _get_api_key_manager() -> Any:
    """Return a cached ApiKeyManager singleton."""
    global _api_key_manager  # noqa: PLW0603
    if _api_key_manager is None:
        from navil.cloud.api_keys import ApiKeyManager

        _api_key_manager = ApiKeyManager()
    return _api_key_manager


def verify_api_key(token: str) -> tuple[str, list[str]] | None:
    """Verify an ``nvl_`` API key.  Returns ``(user_id, scopes)`` or None."""
    mgr = _get_api_key_manager()
    return mgr.verify_key(token)


# ---------------------------------------------------------------------------
# FastAPI / Starlette middleware
# ---------------------------------------------------------------------------

# Paths that never require authentication (even when Clerk is configured).
_PUBLIC_PATHS = frozenset({
    "/api/billing/plan",
    "/api/billing/webhook",
    "/api/webhooks/clerk",
    "/api/health",
})


def _is_public(path: str) -> bool:
    """Return True for paths that skip auth."""
    # All non-API paths (frontend assets, SPA routes) are always public.
    if not path.startswith("/api"):
        return True
    return path in _PUBLIC_PATHS


def _is_ingest_path(path: str) -> bool:
    """Return True for ingestion paths that accept API key auth."""
    return path.startswith("/api/ingest/")


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate requests via Clerk JWT or API key.

    Dispatch logic:

    - ``/api/ingest/*`` — verify ``Bearer nvl_...`` API key
    - ``/api/*`` other — verify Clerk JWT (existing behavior)
    - Non-API paths — always public (frontend SPA)

    Both paths set ``request.state.user_id`` so downstream is auth-agnostic.
    When Clerk is not configured, the middleware is inert (no-op).
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # --- No-op when Clerk is not configured ---
        if not CLERK_SECRET_KEY or not CLERK_ISSUER_URL:
            return await call_next(request)

        # --- Public paths skip auth ---
        if _is_public(request.url.path):
            return await call_next(request)

        # --- Extract Bearer token ---
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"detail": "Missing or invalid Authorization header"},
                status_code=401,
            )

        token = auth_header[7:]  # strip "Bearer "

        # --- API key auth for ingestion endpoints ---
        if _is_ingest_path(request.url.path) or token.startswith("nvl_"):
            result = verify_api_key(token)
            if result is None:
                return JSONResponse(
                    {"detail": "Invalid or expired API key"},
                    status_code=401,
                )
            user_id, scopes = result
            request.state.user_id = user_id
            request.state.user_email = ""
            request.state.api_key_scopes = scopes
            return await call_next(request)

        # --- Clerk JWT auth for dashboard endpoints ---
        try:
            payload = verify_clerk_token(token)
            request.state.user_id = payload.get("sub", "unknown")
            request.state.user_email = payload.get("email", "")
        except Exception as exc:
            logger.warning("Clerk JWT verification failed: %s", exc)
            return JSONResponse(
                {"detail": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
