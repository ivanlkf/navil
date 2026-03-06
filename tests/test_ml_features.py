"""Tests for ML feature extraction (requires scikit-learn)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

sklearn = pytest.importorskip("sklearn")

from navil.anomaly_detector import ToolInvocation
from navil.ml.features import FeatureExtractor


def _make_invocation(
    agent: str = "agent-a",
    tool: str = "logs",
    action: str = "read",
    duration: int = 50,
    data: int = 100,
) -> ToolInvocation:
    return ToolInvocation(
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_name=agent,
        tool_name=tool,
        action=action,
        duration_ms=duration,
        data_accessed_bytes=data,
        success=True,
    )


class TestFeatureExtractor:
    def test_feature_count(self) -> None:
        fe = FeatureExtractor()
        inv = _make_invocation()
        features = fe.extract_single(inv, [])
        assert len(features) == 15

    def test_feature_names_match_count(self) -> None:
        assert len(FeatureExtractor.FEATURE_NAMES) == 15

    def test_batch_shape(self) -> None:
        fe = FeatureExtractor()
        invocations = [_make_invocation() for _ in range(10)]
        X = fe.extract_batch(invocations)
        assert X.shape == (10, 15)

    def test_tool_encoding_consistency(self) -> None:
        fe = FeatureExtractor()
        inv1 = _make_invocation(tool="logs")
        inv2 = _make_invocation(tool="admin")
        inv3 = _make_invocation(tool="logs")
        f1 = fe.extract_single(inv1, [])
        f2 = fe.extract_single(inv2, [])
        f3 = fe.extract_single(inv3, [])
        # Same tool should get same index
        assert f1[6] == f3[6]
        assert f1[6] != f2[6]

    def test_action_encoding_consistency(self) -> None:
        fe = FeatureExtractor()
        inv1 = _make_invocation(action="read")
        inv2 = _make_invocation(action="write")
        f1 = fe.extract_single(inv1, [])
        f2 = fe.extract_single(inv2, [])
        assert f1[7] != f2[7]

    def test_duration_feature(self) -> None:
        fe = FeatureExtractor()
        inv = _make_invocation(duration=999)
        features = fe.extract_single(inv, [])
        assert features[0] == 999.0

    def test_success_flag(self) -> None:
        fe = FeatureExtractor()
        inv = _make_invocation()
        inv.success = False
        features = fe.extract_single(inv, [])
        assert features[2] == 0.0

    def test_with_history(self) -> None:
        fe = FeatureExtractor()
        history = [_make_invocation() for _ in range(5)]
        inv = _make_invocation()
        features = fe.extract_single(inv, history)
        # invocations_last_30min should count history
        assert features[9] >= 0
