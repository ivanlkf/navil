# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Clerk JWT authentication middleware for Navil Cloud.

When ``CLERK_SECRET_KEY`` **and** ``CLERK_ISSUER_URL`` are set the middleware
verifies incoming ``Authorization: Bearer <token>`` headers using Clerk's
JWKS endpoint and injects ``request.state.user_id`` / ``request.state.user_email``.

When the environment variables are *not* present the middleware is a
transparent no-op — every request passes through unauthenticated.  This
guarantees zero behavioural change for existing deployments and tests.
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
# FastAPI / Starlette middleware
# ---------------------------------------------------------------------------

# Paths that never require authentication (even when Clerk is configured).
_PUBLIC_PATHS = frozenset({"/api/billing/plan"})


def _is_public(path: str) -> bool:
    """Return True for paths that skip auth."""
    # All non-API paths (frontend assets, SPA routes) are always public.
    if not path.startswith("/api"):
        return True
    return path in _PUBLIC_PATHS


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """Validate Clerk JWTs and populate ``request.state.user_id``.

    When Clerk is not configured (no env vars) the middleware is inert.
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
