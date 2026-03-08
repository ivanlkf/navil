"""MCP Security Proxy — real-time JSON-RPC 2.0 reverse proxy.

Sits between AI agents and MCP servers, intercepting every tool call
for policy enforcement and anomaly detection.

Usage (standalone):
    navil proxy start --target http://localhost:3000 --port 9090

Architecture:
    Agent → POST /mcp → Navil Proxy → httpx → MCP Server
                            ↓
                    Pre-execution:  policy check, rate limit, auth
                    Post-execution: record invocation, anomaly detection
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

try:
    from starlette.requests import Request as _StarletteRequest
except ModuleNotFoundError:  # starlette is optional (proxy extras)
    _StarletteRequest = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class MCPSecurityProxy:
    """Real-time MCP security proxy.

    Intercepts JSON-RPC 2.0 messages (tools/call, tools/list) and applies
    security checks before forwarding to the upstream MCP server.
    """

    MAX_TRAFFIC_LOG = 1000

    def __init__(
        self,
        target_url: str,
        policy_engine: Any,
        anomaly_detector: Any,
        credential_manager: Any,
        require_auth: bool = True,
        cloud_client: Any | None = None,
    ) -> None:
        self.target_url = target_url.rstrip("/")
        self.policy_engine = policy_engine
        self.detector = anomaly_detector
        self.credential_manager = credential_manager
        self.require_auth = require_auth
        self.cloud_client = cloud_client  # NavilCloudClient for telemetry

        self.traffic_log: deque[dict[str, Any]] = deque(maxlen=self.MAX_TRAFFIC_LOG)
        self.stats = {
            "total_requests": 0,
            "blocked": 0,
            "alerts_generated": 0,
            "forwarded": 0,
        }
        self.start_time = time.time()

    # ── JSON-RPC Parsing ──────────────────────────────────────

    @staticmethod
    def parse_jsonrpc(body: bytes) -> dict[str, Any]:
        """Parse a JSON-RPC 2.0 request envelope.

        Returns dict with keys: method, params, id, raw.
        Raises ValueError on invalid JSON-RPC.
        """
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("JSON-RPC request must be an object")

        return {
            "method": data.get("method", ""),
            "params": data.get("params", {}),
            "id": data.get("id"),
            "raw": data,
        }

    @staticmethod
    def extract_tool_info(parsed: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        """Extract tool name, action, and arguments from a tools/call request.

        Returns (tool_name, action, arguments).
        """
        params = parsed.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        # MCP doesn't have a formal "action" field — derive from method
        action = parsed.get("method", "tools/call")
        return tool_name, action, arguments

    # ── Identity ──────────────────────────────────────────────

    def extract_agent_name(self, headers: dict[str, str]) -> str | None:
        """Extract agent identity from request headers.

        Checks Authorization header (Bearer JWT) first, then falls back
        to X-Agent-Name header.
        """
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            # Try JWT verification first
            try:
                payload = self.credential_manager.verify_credential(token)
                if payload and "agent_name" in payload:
                    return payload["agent_name"]
            except Exception:
                pass
            # Fallback: match token against stored credentials
            if hasattr(self.credential_manager, "credentials"):
                for cred in self.credential_manager.credentials.values():
                    status = cred.status
                    status_str = status.value if hasattr(status, "value") else str(status)
                    if cred.token == token and status_str == "ACTIVE":
                        return cred.agent_name

        return headers.get("x-agent-name")

    # ── Core Request Handler ──────────────────────────────────

    async def handle_jsonrpc(
        self, body: bytes, headers: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Handle an incoming JSON-RPC request.

        Returns (json_rpc_response, upstream_headers) tuple.
        """
        self.stats["total_requests"] += 1
        start = time.time()

        # Parse JSON-RPC
        try:
            parsed = self.parse_jsonrpc(body)
        except ValueError as e:
            return self._jsonrpc_error(-32700, f"Parse error: {e}", None), {}

        req_id = parsed["id"]
        method = parsed["method"]

        # Extract identity
        agent_name = self.extract_agent_name(headers)
        if self.require_auth and not agent_name:
            self.stats["blocked"] += 1
            self._log_traffic(agent_name, method, "", "AUTH_REQUIRED", 0, 0)
            return self._jsonrpc_error(-32003, "Authentication required", req_id), {}

        agent_name = agent_name or "anonymous"

        # Pre-execution checks (only for tools/call)
        if method == "tools/call":
            tool_name, action, arguments = self.extract_tool_info(parsed)

            # Policy check
            if hasattr(self.policy_engine, "check_tool_call"):
                decision = self.policy_engine.check_tool_call(agent_name, tool_name, action)
                if hasattr(decision, "decision"):
                    decision_val = decision.decision.value
                else:
                    decision_val = str(decision)

                if decision_val == "DENY":
                    self.stats["blocked"] += 1
                    duration_ms = int((time.time() - start) * 1000)
                    self._log_traffic(agent_name, method, tool_name, "DENIED", duration_ms, 0)
                    return self._jsonrpc_error(
                        -32001,
                        f"Blocked by policy: {tool_name}",
                        req_id,
                    ), {}

            # Forward to upstream
            response_data, response_bytes, upstream_hdrs = await self._forward(body, headers)
            duration_ms = int((time.time() - start) * 1000)

            # Post-execution: record invocation
            args_json = json.dumps(arguments, sort_keys=True)
            args_hash = hashlib.sha256(args_json.encode()).hexdigest()

            alert_count_before = len(self.detector.alerts)
            self.detector.record_invocation(
                agent_name=agent_name,
                tool_name=tool_name,
                action=action,
                duration_ms=duration_ms,
                data_accessed_bytes=response_bytes,
                success="error" not in response_data,
                target_server=self.target_url,
                arguments_hash=args_hash,
                arguments_size_bytes=len(args_json.encode()),
                response_size_bytes=response_bytes,
                is_list_tools=False,
            )
            alert_count_after = len(self.detector.alerts)
            new_alerts = alert_count_after - alert_count_before
            if new_alerts > 0:
                self.stats["alerts_generated"] += new_alerts

            # Cloud telemetry: ship event + any new alerts
            if self.cloud_client:
                import asyncio

                try:
                    asyncio.ensure_future(
                        self.cloud_client.record_event(
                            agent_name=agent_name,
                            tool_name=tool_name,
                            action=action,
                            duration_ms=duration_ms,
                            data_accessed_bytes=response_bytes,
                            success="error" not in response_data,
                        )
                    )
                    # Ship new alerts
                    for a in self.detector.alerts[-new_alerts:] if new_alerts > 0 else []:
                        a_dict = a if isinstance(a, dict) else a.__dict__
                        asyncio.ensure_future(
                            self.cloud_client.report_alert(
                                agent_name=a_dict.get("agent_name", agent_name),
                                anomaly_type=a_dict.get("anomaly_type", "UNKNOWN"),
                                severity=a_dict.get("severity", "MEDIUM"),
                                description=a_dict.get("description", ""),
                                evidence=a_dict.get("evidence", []),
                            )
                        )
                except Exception:
                    pass  # telemetry is best-effort

            self.stats["forwarded"] += 1
            self._log_traffic(agent_name, method, tool_name, "ALLOWED", duration_ms, response_bytes)
            return response_data, upstream_hdrs

        elif method == "tools/list":
            # Forward tools/list and track registered tools
            response_data, response_bytes, upstream_hdrs = await self._forward(body, headers)
            duration_ms = int((time.time() - start) * 1000)

            # Record as invocation for reconnaissance detection
            alert_count_before = len(self.detector.alerts)
            self.detector.record_invocation(
                agent_name=agent_name,
                tool_name="__tools_list__",
                action="tools/list",
                duration_ms=duration_ms,
                data_accessed_bytes=response_bytes,
                success="error" not in response_data,
                target_server=self.target_url,
                is_list_tools=True,
            )
            alert_count_after = len(self.detector.alerts)
            if alert_count_after > alert_count_before:
                self.stats["alerts_generated"] += alert_count_after - alert_count_before

            # Extract tool names from response for supply chain tracking
            try:
                result = response_data.get("result", {})
                tools = result.get("tools", []) if isinstance(result, dict) else []
                tool_names = [t.get("name", "") for t in tools if isinstance(t, dict)]
                if tool_names:
                    self.detector.register_server_tools(self.target_url, tool_names)
            except Exception:
                pass

            self.stats["forwarded"] += 1
            self._log_traffic(agent_name, method, "", "ALLOWED", duration_ms, response_bytes)
            return response_data, upstream_hdrs

        else:
            # Forward all other methods transparently
            response_data, response_bytes, upstream_hdrs = await self._forward(body, headers)
            duration_ms = int((time.time() - start) * 1000)
            self.stats["forwarded"] += 1
            self._log_traffic(agent_name, method, "", "FORWARDED", duration_ms, response_bytes)
            return response_data, upstream_hdrs

    # ── Upstream Forwarding ───────────────────────────────────

    async def _forward(
        self, body: bytes, headers: dict[str, str]
    ) -> tuple[dict[str, Any], int, dict[str, str]]:
        """Forward request to upstream MCP server via httpx.

        Returns (response_json, response_size_bytes, upstream_headers).
        """
        import httpx

        # Strip hop-by-hop headers
        forward_headers = {
            k: v
            for k, v in headers.items()
            if k.lower() not in ("host", "connection", "transfer-encoding")
        }
        forward_headers["content-type"] = "application/json"
        forward_headers["accept"] = "application/json, text/event-stream"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.target_url,
                content=body,
                headers=forward_headers,
            )

        response_bytes = len(resp.content)
        content_type = resp.headers.get("content-type", "")

        if "text/event-stream" in content_type:
            # Parse SSE: extract JSON from "data: {...}" lines
            response_data = self._parse_sse_response(resp.text)
        else:
            try:
                response_data = resp.json()
            except Exception:
                response_data = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": "Upstream returned non-JSON"},
                    "id": None,
                }

        # Collect headers to forward back (e.g. mcp-session-id)
        upstream_headers = {
            k: v for k, v in resp.headers.items() if k.lower() in ("mcp-session-id",)
        }

        return response_data, response_bytes, upstream_headers

    @staticmethod
    def _parse_sse_response(text: str) -> dict[str, Any]:
        """Extract JSON-RPC response from SSE stream (text/event-stream)."""
        for line in text.splitlines():
            if line.startswith("data: "):
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "No valid JSON in SSE response"},
            "id": None,
        }

    # ── Traffic Logging ───────────────────────────────────────

    def _log_traffic(
        self,
        agent: str | None,
        method: str,
        tool: str,
        decision: str,
        duration_ms: int,
        data_bytes: int,
    ) -> None:
        """Append entry to the traffic ring buffer."""
        self.traffic_log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent or "unknown",
                "method": method,
                "tool": tool,
                "decision": decision,
                "duration_ms": duration_ms,
                "data_bytes": data_bytes,
            }
        )

    def get_traffic(
        self,
        limit: int = 100,
        agent: str | None = None,
        blocked_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get recent traffic log entries."""
        entries = list(self.traffic_log)

        if agent:
            entries = [e for e in entries if e["agent"] == agent]
        if blocked_only:
            entries = [e for e in entries if e["decision"] in ("DENIED", "AUTH_REQUIRED")]

        return list(reversed(entries[-limit:]))

    def get_status(self) -> dict[str, Any]:
        """Get proxy status summary."""
        return {
            "running": True,
            "target_url": self.target_url,
            "stats": dict(self.stats),
            "uptime_seconds": int(time.time() - self.start_time),
            "traffic_log_size": len(self.traffic_log),
        }

    # ── JSON-RPC Helpers ──────────────────────────────────────

    @staticmethod
    def _jsonrpc_error(code: int, message: str, req_id: Any) -> dict[str, Any]:
        """Build a JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id,
        }


def create_proxy_app(proxy: MCPSecurityProxy) -> Any:
    """Create a FastAPI app wrapping the proxy.

    The proxy runs on its own port (separate from the dashboard)
    so agents connect to it directly.
    """
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="Navil MCP Security Proxy",
        description="Real-time MCP security proxy with policy enforcement and anomaly detection",
        version="0.1.0",
    )

    @app.post("/mcp")
    async def handle_mcp(request: Request) -> JSONResponse:
        body = await request.body()
        headers = dict(request.headers)
        result, upstream_headers = await proxy.handle_jsonrpc(body, headers)
        return JSONResponse(content=result, headers=upstream_headers)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return proxy.get_status()

    @app.get("/traffic")
    async def traffic(
        limit: int = 100,
        agent: str | None = None,
        blocked_only: bool = False,
    ) -> list[dict[str, Any]]:
        return proxy.get_traffic(limit=limit, agent=agent, blocked_only=blocked_only)

    return app
