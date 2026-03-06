"""Tests for the MCP Security Proxy (all mocked, no network)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from navil.anomaly_detector import BehavioralAnomalyDetector
from navil.credential_manager import CredentialManager
from navil.policy_engine import PolicyEngine
from navil.proxy import MCPSecurityProxy


@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
def detector() -> BehavioralAnomalyDetector:
    return BehavioralAnomalyDetector()


@pytest.fixture
def cred_manager() -> CredentialManager:
    return CredentialManager()


@pytest.fixture
def proxy(
    policy_engine: PolicyEngine,
    detector: BehavioralAnomalyDetector,
    cred_manager: CredentialManager,
) -> MCPSecurityProxy:
    return MCPSecurityProxy(
        target_url="http://localhost:3000",
        policy_engine=policy_engine,
        anomaly_detector=detector,
        credential_manager=cred_manager,
        require_auth=False,  # Disable auth for easier testing
    )


def _mock_forward(response_data: dict) -> AsyncMock:
    """Create an AsyncMock for proxy._forward that returns given response."""
    response_bytes = len(json.dumps(response_data).encode())
    return AsyncMock(return_value=(response_data, response_bytes))


class TestParseJsonRPC:
    """JSON-RPC 2.0 parsing tests."""

    def test_parse_valid_tools_call(self) -> None:
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "read_file", "arguments": {"path": "/tmp/test"}},
                "id": 1,
            }
        ).encode()

        parsed = MCPSecurityProxy.parse_jsonrpc(body)
        assert parsed["method"] == "tools/call"
        assert parsed["params"]["name"] == "read_file"
        assert parsed["id"] == 1

    def test_parse_tools_list(self) -> None:
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2,
            }
        ).encode()

        parsed = MCPSecurityProxy.parse_jsonrpc(body)
        assert parsed["method"] == "tools/list"
        assert parsed["id"] == 2

    def test_parse_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            MCPSecurityProxy.parse_jsonrpc(b"not json")

    def test_parse_non_object(self) -> None:
        with pytest.raises(ValueError, match="must be an object"):
            MCPSecurityProxy.parse_jsonrpc(b"[1,2,3]")


class TestExtractToolInfo:
    def test_extract(self) -> None:
        parsed = {
            "method": "tools/call",
            "params": {"name": "write_file", "arguments": {"content": "hello"}},
            "id": 1,
        }
        tool_name, action, arguments = MCPSecurityProxy.extract_tool_info(parsed)
        assert tool_name == "write_file"
        assert arguments == {"content": "hello"}


class TestIdentity:
    def test_x_agent_name_header(self, proxy: MCPSecurityProxy) -> None:
        name = proxy.extract_agent_name({"x-agent-name": "test-agent"})
        assert name == "test-agent"

    def test_no_identity(self, proxy: MCPSecurityProxy) -> None:
        name = proxy.extract_agent_name({})
        assert name is None

    def test_jwt_bearer_with_valid_credential(self, proxy: MCPSecurityProxy) -> None:
        """JWT auth should work when credential manager validates."""
        cred = proxy.credential_manager.issue_credential(
            agent_name="jwt-agent", scope="*", ttl_seconds=3600
        )
        token = cred["token"]
        name = proxy.extract_agent_name({"authorization": f"Bearer {token}"})
        assert name == "jwt-agent"


class TestHandleJsonRPC:
    @pytest.mark.asyncio
    async def test_auth_required_blocks_unauthenticated(
        self,
        detector: BehavioralAnomalyDetector,
        cred_manager: CredentialManager,
    ) -> None:
        """When require_auth=True, missing identity returns error -32003."""
        proxy = MCPSecurityProxy(
            target_url="http://localhost:3000",
            policy_engine=PolicyEngine(),
            anomaly_detector=detector,
            credential_manager=cred_manager,
            require_auth=True,
        )

        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "read"},
                "id": 1,
            }
        ).encode()

        result = await proxy.handle_jsonrpc(body, {})
        assert result["error"]["code"] == -32003
        assert proxy.stats["blocked"] == 1

    @pytest.mark.asyncio
    async def test_invalid_json_returns_parse_error(self, proxy: MCPSecurityProxy) -> None:
        result = await proxy.handle_jsonrpc(b"not json", {})
        assert result["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_tools_call_forwarded(self, proxy: MCPSecurityProxy) -> None:
        """Successful tools/call should forward and record invocation."""
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "read_file", "arguments": {"path": "/tmp"}},
                "id": 1,
            }
        ).encode()

        upstream_response = {
            "jsonrpc": "2.0",
            "result": {"content": "file data"},
            "id": 1,
        }

        proxy._forward = _mock_forward(upstream_response)

        result = await proxy.handle_jsonrpc(body, {"x-agent-name": "test-agent"})

        assert "result" in result
        assert proxy.stats["forwarded"] == 1
        assert len(proxy.detector.invocations) == 1
        assert proxy.detector.invocations[0].agent_name == "test-agent"
        assert proxy.detector.invocations[0].tool_name == "read_file"

    @pytest.mark.asyncio
    async def test_tools_list_registers_tools(self, proxy: MCPSecurityProxy) -> None:
        """tools/list should register tool names for supply chain detection."""
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1,
            }
        ).encode()

        upstream_response = {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "read_file", "description": "Read a file"},
                    {"name": "write_file", "description": "Write a file"},
                ]
            },
            "id": 1,
        }

        proxy._forward = _mock_forward(upstream_response)

        result = await proxy.handle_jsonrpc(body, {"x-agent-name": "test-agent"})

        assert "result" in result
        assert "http://localhost:3000" in proxy.detector.registered_tools
        assert proxy.detector.registered_tools["http://localhost:3000"] == {
            "read_file",
            "write_file",
        }


class TestTrafficLog:
    def test_ring_buffer_max_size(self, proxy: MCPSecurityProxy) -> None:
        """Traffic log should be capped at MAX_TRAFFIC_LOG entries."""
        for i in range(proxy.MAX_TRAFFIC_LOG + 100):
            proxy._log_traffic(f"agent-{i}", "tools/call", "tool", "ALLOWED", 10, 100)

        assert len(proxy.traffic_log) == proxy.MAX_TRAFFIC_LOG

    def test_get_traffic_filter(self, proxy: MCPSecurityProxy) -> None:
        proxy._log_traffic("agent-a", "tools/call", "read", "ALLOWED", 10, 100)
        proxy._log_traffic("agent-b", "tools/call", "write", "DENIED", 5, 0)
        proxy._log_traffic("agent-a", "tools/list", "", "ALLOWED", 3, 50)

        # Filter by agent
        result = proxy.get_traffic(agent="agent-a")
        assert len(result) == 2

        # Filter blocked only
        result = proxy.get_traffic(blocked_only=True)
        assert len(result) == 1
        assert result[0]["decision"] == "DENIED"


class TestGetStatus:
    def test_status_structure(self, proxy: MCPSecurityProxy) -> None:
        status = proxy.get_status()
        assert status["running"] is True
        assert status["target_url"] == "http://localhost:3000"
        assert "total_requests" in status["stats"]
        assert "uptime_seconds" in status


class TestJsonRPCError:
    def test_error_format(self) -> None:
        err = MCPSecurityProxy._jsonrpc_error(-32001, "Blocked", 42)
        assert err["jsonrpc"] == "2.0"
        assert err["error"]["code"] == -32001
        assert err["error"]["message"] == "Blocked"
        assert err["id"] == 42
