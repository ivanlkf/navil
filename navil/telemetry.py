# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Apache License 2.0 (see LICENSE)
"""Navil Cloud telemetry client.

Lightweight async HTTP client for shipping proxy telemetry to navil.ai.
Used by the proxy when ``--cloud-key`` is provided.

Usage::

    client = NavilCloudClient(api_key="nvl_xxxx", cloud_url="https://navil.ai")

    # Record events (buffered, flushed every 10s or 100 events)
    await client.record_event({...})

    # Report critical alerts (sent immediately)
    await client.report_alert({...})

    # Heartbeat (called automatically every 60s)
    await client.heartbeat({...})
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class NavilCloudClient:
    """Ships proxy telemetry to the Navil Cloud API."""

    def __init__(
        self,
        api_key: str,
        cloud_url: str = "https://navil.ai",
        flush_interval: float = 10.0,
        batch_size: int = 100,
    ) -> None:
        self.api_key = api_key
        self.cloud_url = cloud_url.rstrip("/")
        self.flush_interval = flush_interval
        self.batch_size = batch_size

        self._event_buffer: list[dict[str, Any]] = []
        self._alert_buffer: list[dict[str, Any]] = []
        self._last_flush = time.monotonic()
        self._client: Any = None
        self._flush_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._running = False
        self._proxy_start_time = time.monotonic()

    def _get_client(self) -> Any:
        """Lazy-create an httpx.AsyncClient."""
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self.cloud_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
        return self._client

    async def start(self, proxy_status_fn: Any = None) -> None:
        """Start background flush and heartbeat tasks."""
        self._running = True
        self._proxy_status_fn = proxy_status_fn
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Cloud telemetry started → %s", self.cloud_url)

    async def stop(self) -> None:
        """Stop background tasks and flush remaining data."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        # Final flush
        await self._flush_events()
        await self._flush_alerts()
        if self._client:
            await self._client.aclose()

    async def record_event(
        self,
        agent_name: str,
        tool_name: str,
        action: str,
        duration_ms: int,
        data_accessed_bytes: int = 0,
        success: bool = True,
    ) -> None:
        """Buffer an event for batch upload."""
        self._event_buffer.append({
            "agent_name": agent_name,
            "tool_name": tool_name,
            "action": action,
            "duration_ms": duration_ms,
            "data_accessed_bytes": data_accessed_bytes,
            "success": success,
        })

        # Flush if buffer full
        if len(self._event_buffer) >= self.batch_size:
            await self._flush_events()

    async def report_alert(
        self,
        agent_name: str,
        anomaly_type: str,
        severity: str,
        description: str = "",
        evidence: list[str] | None = None,
    ) -> None:
        """Report an alert.  CRITICAL/HIGH alerts are sent immediately."""
        alert = {
            "agent_name": agent_name,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "description": description,
            "evidence": evidence or [],
        }

        if severity in ("CRITICAL", "HIGH"):
            # Send immediately
            await self._send_alerts([alert])
        else:
            self._alert_buffer.append(alert)
            if len(self._alert_buffer) >= 50:
                await self._flush_alerts()

    async def heartbeat(self, status: dict[str, Any] | None = None) -> None:
        """Send a heartbeat to the cloud."""
        from navil import __version__

        payload = {
            "proxy_version": __version__,
            "target_url": status.get("target_url", "") if status else "",
            "uptime_seconds": int(time.monotonic() - self._proxy_start_time),
            "stats": status.get("stats", {}) if status else {},
        }
        try:
            client = self._get_client()
            await client.post("/api/ingest/heartbeat", json=payload)
        except Exception:
            logger.debug("Heartbeat failed (cloud may be unreachable)")

    # ── Internal ────────────────────────────────────

    async def _flush_events(self) -> None:
        """Send buffered events to the cloud."""
        if not self._event_buffer:
            return
        batch = self._event_buffer[:]
        self._event_buffer.clear()
        try:
            client = self._get_client()
            resp = await client.post("/api/ingest/events", json={"events": batch})
            if resp.status_code != 200:
                logger.warning("Event ingestion failed: %s %s", resp.status_code, resp.text[:200])
        except Exception:
            logger.debug("Event flush failed (cloud may be unreachable)")

    async def _flush_alerts(self) -> None:
        """Send buffered alerts to the cloud."""
        if not self._alert_buffer:
            return
        batch = self._alert_buffer[:]
        self._alert_buffer.clear()
        await self._send_alerts(batch)

    async def _send_alerts(self, alerts: list[dict[str, Any]]) -> None:
        """Send a batch of alerts."""
        try:
            client = self._get_client()
            resp = await client.post("/api/ingest/alerts", json={"alerts": alerts})
            if resp.status_code != 200:
                logger.warning("Alert ingestion failed: %s %s", resp.status_code, resp.text[:200])
        except Exception:
            logger.debug("Alert flush failed (cloud may be unreachable)")

    async def _flush_loop(self) -> None:
        """Periodically flush buffered events and alerts."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_events()
                await self._flush_alerts()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.debug("Flush loop error")

    async def _heartbeat_loop(self) -> None:
        """Send heartbeats every 60 seconds."""
        while self._running:
            try:
                await asyncio.sleep(60)
                status = None
                if hasattr(self, "_proxy_status_fn") and self._proxy_status_fn:
                    status = self._proxy_status_fn()
                await self.heartbeat(status)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.debug("Heartbeat loop error")
