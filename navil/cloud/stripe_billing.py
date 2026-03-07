# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Stripe-backed billing for Navil Cloud.

Activated when ``STRIPE_SECRET_KEY`` is set.  Falls back to the in-memory
``BillingManager`` when not configured.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_LITE_PRICE_ID = os.environ.get("STRIPE_LITE_PRICE_ID")
STRIPE_ELITE_PRICE_ID = os.environ.get("STRIPE_ELITE_PRICE_ID")

CACHE_TTL = 60  # seconds


def stripe_configured() -> bool:
    """Return True when Stripe credentials are present in the environment."""
    return bool(STRIPE_SECRET_KEY)


@dataclass
class CachedStatus:
    plan: str
    customer_id: str
    fetched_at: float


class StripeBillingManager:
    """Billing manager backed by Stripe Subscriptions.

    Uses Stripe as the single source of truth — no database required.
    Subscription status is cached for ``CACHE_TTL`` seconds.
    """

    def __init__(self) -> None:
        import stripe

        stripe.api_key = STRIPE_SECRET_KEY
        self._cache: dict[str, CachedStatus] = {}

    # -- Customer management ------------------------------------------------

    def _get_or_create_customer(self, user_id: str, email: str = "") -> str:
        """Find existing Stripe customer by ``navil_user_id`` metadata, or create one."""
        import stripe

        results = stripe.Customer.search(
            query=f'metadata["navil_user_id"]:"{user_id}"',
        )
        if results.data:
            return results.data[0].id

        customer = stripe.Customer.create(
            email=email or None,
            metadata={"navil_user_id": user_id},
        )
        return customer.id

    # -- Subscription status ------------------------------------------------

    def get_subscription_status(self, user_id: str) -> CachedStatus:
        """Return current plan for *user_id*, with short-lived caching."""
        cached = self._cache.get(user_id)
        if cached and (time.time() - cached.fetched_at) < CACHE_TTL:
            return cached

        import stripe

        customer_id = self._get_or_create_customer(user_id)
        subs = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1,
        )
        if subs.data:
            price_id = subs.data[0].get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
            plan = "elite" if price_id == STRIPE_ELITE_PRICE_ID else "lite"
        else:
            plan = "free"
        status = CachedStatus(
            plan=plan,
            customer_id=customer_id,
            fetched_at=time.time(),
        )
        self._cache[user_id] = status
        return status

    # -- Checkout / Portal --------------------------------------------------

    def create_checkout_session(
        self,
        user_id: str,
        success_url: str,
        cancel_url: str,
        email: str = "",
        plan: str = "lite",
    ) -> str:
        """Create a Stripe Checkout Session for the given plan.  Returns session URL."""
        import stripe

        price_id = STRIPE_ELITE_PRICE_ID if plan == "elite" else STRIPE_LITE_PRICE_ID
        customer_id = self._get_or_create_customer(user_id, email)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"navil_user_id": user_id},
        )
        return session.url or ""

    def create_portal_session(self, user_id: str, return_url: str) -> str:
        """Create a Stripe Customer Portal session.  Returns portal URL."""
        import stripe

        status = self.get_subscription_status(user_id)
        session = stripe.billing_portal.Session.create(
            customer=status.customer_id,
            return_url=return_url,
        )
        return session.url

    # -- Webhooks -----------------------------------------------------------

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        """Verify and process a Stripe webhook event.  Invalidates cache."""
        import stripe

        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET,
        )

        if event.type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "checkout.session.completed",
        ):
            obj = event.data.object
            customer_id = obj.get("customer") or obj.get("id")
            # Invalidate cache entries for this customer
            to_remove = [uid for uid, cs in self._cache.items() if cs.customer_id == customer_id]
            for uid in to_remove:
                del self._cache[uid]
            logger.info(
                "Stripe webhook %s: cache invalidated for customer %s",
                event.type,
                customer_id,
            )

        return {"status": "ok", "type": event.type}

    # -- Plan checks (matches BillingManager interface) ---------------------

    def can_use_llm(self, user_id: str, has_byok: bool) -> bool:
        """Check whether *user_id* may invoke LLM features."""
        if has_byok:
            return True
        status = self.get_subscription_status(user_id)
        return status.plan in ("lite", "elite")

    def increment_llm_calls(self, user_id: str) -> int:
        """No-op counter for Stripe mode (metering done via Stripe)."""
        return 0
