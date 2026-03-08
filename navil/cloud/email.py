# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Transactional email service for Navil Cloud using Resend.

Sends welcome emails, alert digests, credential expiry warnings,
and subscription change notifications.

Set ``RESEND_API_KEY`` and optionally ``EMAIL_FROM`` in the environment.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

RESEND_API_KEY: str | None = os.environ.get("RESEND_API_KEY")
EMAIL_FROM: str = os.environ.get("EMAIL_FROM", "Navil <noreply@navil.ai>")


def email_configured() -> bool:
    """Return True when Resend credentials are present."""
    return bool(RESEND_API_KEY)


class EmailService:
    """Transactional email service backed by Resend."""

    def __init__(self) -> None:
        if RESEND_API_KEY:
            try:
                import resend

                resend.api_key = RESEND_API_KEY
                self._resend = resend
                logger.info("Resend email service configured")
            except ImportError:
                logger.warning("resend package not installed — emails disabled")
                self._resend = None
        else:
            self._resend = None

    def _send(
        self,
        to: str,
        subject: str,
        html: str,
        tags: list[dict[str, str]] | None = None,
    ) -> dict[str, Any] | None:
        """Send an email via Resend. Returns response or None if disabled."""
        if self._resend is None:
            logger.debug("Email skipped (not configured): to=%s subject=%s", to, subject)
            return None
        try:
            params: dict[str, Any] = {
                "from_": EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
            }
            if tags:
                params["tags"] = tags

            result = self._resend.Emails.send(params)
            logger.info("Email sent: to=%s subject=%s", to, subject)
            return result
        except Exception:
            logger.exception("Failed to send email: to=%s subject=%s", to, subject)
            return None

    # ------------------------------------------------------------------
    # Email templates
    # ------------------------------------------------------------------

    def send_welcome(self, to: str, name: str = "") -> dict[str, Any] | None:
        """Send welcome email to a newly registered user."""
        display_name = name or "there"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="color: #818cf8; font-size: 28px; margin: 0;">Navil</h1>
                <p style="color: #6b7280; font-size: 14px; margin-top: 4px;">MCP Security Platform</p>
            </div>
            <h2 style="color: #f3f4f6; font-size: 22px;">Welcome, {display_name}!</h2>
            <p style="color: #9ca3af; font-size: 15px; line-height: 1.6;">
                Your Navil account is ready. Here's how to get started:
            </p>
            <ol style="color: #d1d5db; font-size: 14px; line-height: 2; padding-left: 20px;">
                <li>Create an API key in your <a href="https://navil.ai/dashboard/api-keys" style="color: #818cf8;">dashboard</a></li>
                <li>Install the proxy: <code style="background: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 13px;">pip install navil</code></li>
                <li>Start monitoring: <code style="background: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 13px;">navil proxy start --target &lt;MCP_SERVER&gt; --cloud-key &lt;KEY&gt;</code></li>
            </ol>
            <div style="text-align: center; margin: 32px 0;">
                <a href="https://navil.ai/onboarding" style="display: inline-block; background: #6366f1; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px;">
                    Start Setup
                </a>
            </div>
            <hr style="border: none; border-top: 1px solid #374151; margin: 32px 0;" />
            <p style="color: #6b7280; font-size: 12px; text-align: center;">
                Navil by Pantheon Lab &middot; <a href="https://navil.ai" style="color: #818cf8;">navil.ai</a>
            </p>
        </div>
        """
        return self._send(
            to=to,
            subject="Welcome to Navil - Secure your MCP servers",
            html=html,
            tags=[{"name": "category", "value": "welcome"}],
        )

    def send_alert_digest(
        self,
        to: str,
        alerts: list[dict[str, Any]],
        period: str = "hourly",
    ) -> dict[str, Any] | None:
        """Send an alert digest email."""
        if not alerts:
            return None

        critical = [a for a in alerts if a.get("severity") == "CRITICAL"]
        high = [a for a in alerts if a.get("severity") == "HIGH"]
        other = [a for a in alerts if a.get("severity") not in ("CRITICAL", "HIGH")]

        alert_rows = ""
        for a in (critical + high + other)[:20]:
            sev = a.get("severity", "LOW")
            color = {
                "CRITICAL": "#ef4444",
                "HIGH": "#f97316",
                "MEDIUM": "#eab308",
                "LOW": "#3b82f6",
            }.get(sev, "#6b7280")
            alert_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #374151;">
                    <span style="display: inline-block; background: {color}20; color: {color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{sev}</span>
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #374151; color: #d1d5db; font-size: 13px;">{a.get('agent', 'unknown')}</td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #374151; color: #9ca3af; font-size: 13px;">{a.get('anomaly_type', a.get('description', ''))[:60]}</td>
            </tr>
            """

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #818cf8; font-size: 24px; margin: 0;">Navil Alert Digest</h1>
                <p style="color: #6b7280; font-size: 13px; margin-top: 4px;">{period.capitalize()} summary &middot; {len(alerts)} alert(s)</p>
            </div>
            <div style="background: #1f2937; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
                <div style="display: flex; padding: 12px 16px; gap: 24px;">
                    <div><span style="color: #ef4444; font-size: 20px; font-weight: 700;">{len(critical)}</span><br/><span style="color: #6b7280; font-size: 11px;">Critical</span></div>
                    <div><span style="color: #f97316; font-size: 20px; font-weight: 700;">{len(high)}</span><br/><span style="color: #6b7280; font-size: 11px;">High</span></div>
                    <div><span style="color: #9ca3af; font-size: 20px; font-weight: 700;">{len(other)}</span><br/><span style="color: #6b7280; font-size: 11px;">Other</span></div>
                </div>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #111827;">
                        <th style="padding: 8px 12px; text-align: left; color: #6b7280; font-size: 11px; font-weight: 600;">Severity</th>
                        <th style="padding: 8px 12px; text-align: left; color: #6b7280; font-size: 11px; font-weight: 600;">Agent</th>
                        <th style="padding: 8px 12px; text-align: left; color: #6b7280; font-size: 11px; font-weight: 600;">Type</th>
                    </tr>
                </thead>
                <tbody>{alert_rows}</tbody>
            </table>
            <div style="text-align: center; margin: 24px 0;">
                <a href="https://navil.ai/dashboard/alerts" style="display: inline-block; background: #6366f1; color: white; padding: 10px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px;">
                    View All Alerts
                </a>
            </div>
            <hr style="border: none; border-top: 1px solid #374151; margin: 24px 0;" />
            <p style="color: #6b7280; font-size: 11px; text-align: center;">
                <a href="https://navil.ai/dashboard/settings" style="color: #818cf8;">Manage notification preferences</a>
            </p>
        </div>
        """
        return self._send(
            to=to,
            subject=f"Navil: {len(critical)} critical, {len(high)} high alert(s)",
            html=html,
            tags=[{"name": "category", "value": "alert_digest"}],
        )

    def send_credential_expiry(
        self,
        to: str,
        credential_name: str,
        expires_in: str,
    ) -> dict[str, Any] | None:
        """Send a warning that a credential is about to expire."""
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #818cf8; font-size: 24px; margin: 0;">Navil</h1>
            </div>
            <div style="background: #422006; border: 1px solid #92400e; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <p style="color: #fbbf24; font-size: 14px; font-weight: 600; margin: 0 0 8px;">
                    Credential Expiring Soon
                </p>
                <p style="color: #fde68a; font-size: 13px; margin: 0;">
                    Your API key <strong>"{credential_name}"</strong> will expire in {expires_in}.
                    Rotate it to avoid service interruption.
                </p>
            </div>
            <div style="text-align: center; margin: 24px 0;">
                <a href="https://navil.ai/dashboard/api-keys" style="display: inline-block; background: #6366f1; color: white; padding: 10px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px;">
                    Manage API Keys
                </a>
            </div>
        </div>
        """
        return self._send(
            to=to,
            subject=f"Navil: API key \"{credential_name}\" expires in {expires_in}",
            html=html,
            tags=[{"name": "category", "value": "credential_expiry"}],
        )

    def send_subscription_change(
        self,
        to: str,
        old_plan: str,
        new_plan: str,
    ) -> dict[str, Any] | None:
        """Send a notification about plan changes."""
        action = "upgraded" if new_plan != "free" else "downgraded"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #818cf8; font-size: 24px; margin: 0;">Navil</h1>
            </div>
            <h2 style="color: #f3f4f6; font-size: 20px;">Plan {action.capitalize()}</h2>
            <p style="color: #9ca3af; font-size: 14px; line-height: 1.6;">
                Your plan has been {action} from <strong style="color: #d1d5db;">{old_plan.capitalize()}</strong>
                to <strong style="color: #818cf8;">{new_plan.capitalize()}</strong>.
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <a href="https://navil.ai/dashboard/settings" style="display: inline-block; background: #6366f1; color: white; padding: 10px 28px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px;">
                    View Dashboard
                </a>
            </div>
        </div>
        """
        return self._send(
            to=to,
            subject=f"Navil: Plan {action} to {new_plan.capitalize()}",
            html=html,
            tags=[{"name": "category", "value": "subscription_change"}],
        )


# Singleton
_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Return the singleton EmailService instance."""
    global _service  # noqa: PLW0603
    if _service is None:
        _service = EmailService()
    return _service
