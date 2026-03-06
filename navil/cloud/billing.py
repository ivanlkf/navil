# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""In-memory billing and plan management for Navil Cloud."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Plan = Literal["free", "pro"]


@dataclass
class UserBilling:
    """Billing state for a single user."""

    plan: Plan = "free"
    llm_call_count: int = 0


class BillingManager:
    """In-memory user billing tracker.

    Tracks plan tier and LLM usage per user.  All data is ephemeral
    and resets when the server restarts.
    """

    def __init__(self) -> None:
        self._users: dict[str, UserBilling] = {}

    def get_billing(self, user_id: str) -> UserBilling:
        """Return billing info for *user_id*, creating a default if absent."""
        if user_id not in self._users:
            self._users[user_id] = UserBilling()
        return self._users[user_id]

    def set_plan(self, user_id: str, plan: Plan) -> None:
        """Change the plan for *user_id*."""
        self.get_billing(user_id).plan = plan

    def increment_llm_calls(self, user_id: str) -> int:
        """Record one LLM API call and return the new total."""
        billing = self.get_billing(user_id)
        billing.llm_call_count += 1
        return billing.llm_call_count

    def can_use_llm(self, user_id: str, has_byok: bool) -> bool:
        """Check whether *user_id* may invoke LLM features.

        Rules:
        - BYOK users can always use LLM (they pay their own provider).
        - Pro-plan users can always use LLM.
        - Free-plan users without BYOK are blocked.
        """
        if has_byok:
            return True
        return self.get_billing(user_id).plan == "pro"
