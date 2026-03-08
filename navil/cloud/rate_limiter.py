# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Redis-backed sliding-window rate limiter for Navil Cloud.

When Redis is not available (``REDIS_URL`` not set), falls back to an
in-memory sliding window — fine for single-process development.

Plan-based limits
-----------------

+---------+------------+-------------+-------------+
| Plan    | Events/min | Alerts/min  | Events/hour |
+---------+------------+-------------+-------------+
| free    |        100 |          10 |       1,000 |
| lite    |      1,000 |         100 |      50,000 |
| elite   |     10,000 |       1,000 |     500,000 |
+---------+------------+-------------+-------------+
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

REDIS_URL: str | None = os.environ.get("REDIS_URL")

# Plan → (resource → (limit, window_seconds))
PLAN_LIMITS: dict[str, dict[str, tuple[int, int]]] = {
    "free": {
        "events_min": (100, 60),
        "alerts_min": (10, 60),
        "events_hour": (1_000, 3600),
    },
    "lite": {
        "events_min": (1_000, 60),
        "alerts_min": (100, 60),
        "events_hour": (50_000, 3600),
    },
    "elite": {
        "events_min": (10_000, 60),
        "alerts_min": (1_000, 60),
        "events_hour": (500_000, 3600),
    },
}


# ---------------------------------------------------------------------------
# In-memory fallback
# ---------------------------------------------------------------------------

class _InMemoryWindow:
    """Thread-unsafe sliding window — sufficient for single-process dev."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _key(self, user_id: str, resource: str) -> str:
        return f"{user_id}:{resource}"

    def check_and_increment(
        self, user_id: str, resource: str, limit: int, window: int, count: int = 1,
    ) -> tuple[bool, int]:
        """Return ``(allowed, remaining)``."""
        k = self._key(user_id, resource)
        now = time.time()
        cutoff = now - window
        # Prune old entries
        self._buckets[k] = [t for t in self._buckets[k] if t > cutoff]
        current = len(self._buckets[k])
        if current + count > limit:
            return False, max(0, limit - current)
        self._buckets[k].extend([now] * count)
        return True, max(0, limit - current - count)


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

_redis_client: Any | None = None


def _get_redis() -> Any | None:
    """Return a cached Redis client, or None if unavailable."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL:
        return None
    try:
        import redis as redis_pkg

        _redis_client = redis_pkg.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis rate-limiter connected: %s", REDIS_URL.split("@")[-1])
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable, falling back to in-memory rate limiter: %s", exc)
        return None


class _RedisWindow:
    """Sliding-window rate limiter using Redis sorted sets."""

    def __init__(self, client: Any) -> None:
        self._r = client

    def check_and_increment(
        self, user_id: str, resource: str, limit: int, window: int, count: int = 1,
    ) -> tuple[bool, int]:
        key = f"rl:{user_id}:{resource}"
        now = time.time()
        cutoff = now - window
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        results = pipe.execute()
        current = results[1]
        if current + count > limit:
            return False, max(0, limit - current)
        pipe2 = self._r.pipeline()
        for i in range(count):
            pipe2.zadd(key, {f"{now}:{i}": now})
        pipe2.expire(key, window + 10)
        pipe2.execute()
        return True, max(0, limit - current - count)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_backend: _InMemoryWindow | _RedisWindow | None = None


def _get_backend() -> _InMemoryWindow | _RedisWindow:
    global _backend  # noqa: PLW0603
    if _backend is not None:
        return _backend
    r = _get_redis()
    _backend = _RedisWindow(r) if r is not None else _InMemoryWindow()
    return _backend


def check_rate_limit(
    user_id: str,
    resource: str,
    plan: str = "free",
    count: int = 1,
) -> tuple[bool, int, int]:
    """Check if the action is within rate limits.

    Returns ``(allowed, remaining, retry_after_seconds)``.
    """
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    if resource not in limits:
        return True, 999_999, 0

    limit, window = limits[resource]
    backend = _get_backend()
    allowed, remaining = backend.check_and_increment(
        user_id, resource, limit, window, count=count,
    )
    retry_after = window if not allowed else 0
    return allowed, remaining, retry_after
