"""Tests for Isolation Forest anomaly detection (requires scikit-learn)."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone

import pytest

sklearn = pytest.importorskip("sklearn")

from navil.anomaly_detector import ToolInvocation
from navil.ml.isolation_forest import IsolationForestDetector


def _make_invocations(n: int, tool: str = "logs", data: int = 100) -> list[ToolInvocation]:
    return [
        ToolInvocation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name="agent-a",
            tool_name=tool,
            action="read",
            duration_ms=50 + (i % 10),
            data_accessed_bytes=data,
            success=True,
        )
        for i in range(n)
    ]


class TestIsolationForestDetector:
    def test_train_insufficient_data(self) -> None:
        detector = IsolationForestDetector()
        invocations = _make_invocations(10)
        with pytest.raises(ValueError, match="Need >= 50"):
            detector.train(invocations)

    def test_train_success(self) -> None:
        detector = IsolationForestDetector()
        invocations = _make_invocations(60)
        stats = detector.train(invocations)
        assert stats["samples_trained"] == 60
        assert stats["features"] == 15
        assert detector.is_fitted is True

    def test_score_before_fit_returns_zero(self) -> None:
        detector = IsolationForestDetector()
        inv = _make_invocations(1)[0]
        score = detector.score(inv, [])
        assert score == 0.0

    def test_score_returns_0_to_1(self) -> None:
        detector = IsolationForestDetector()
        normal = _make_invocations(60)
        detector.train(normal)
        inv = _make_invocations(1)[0]
        score = detector.score(inv, normal)
        assert 0.0 <= score <= 1.0

    def test_save_and_load(self) -> None:
        detector = IsolationForestDetector()
        invocations = _make_invocations(60)
        detector.train(invocations)

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            path = f.name
        detector.save(path)

        detector2 = IsolationForestDetector()
        detector2.load(path)
        assert detector2.is_fitted is True

        import os

        os.unlink(path)
