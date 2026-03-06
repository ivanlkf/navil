"""ML-powered detection features (requires navil[ml]).

Install with: pip install navil[ml]
"""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "IsolationForestDetector":
        from navil.ml.isolation_forest import IsolationForestDetector

        return IsolationForestDetector
    if name == "AgentClusterer":
        from navil.ml.clustering import AgentClusterer

        return AgentClusterer
    if name == "FeatureExtractor":
        from navil.ml.features import FeatureExtractor

        return FeatureExtractor
    if name == "ModelStore":
        from navil.ml.model_store import ModelStore

        return ModelStore
    raise AttributeError(f"module 'navil.ml' has no attribute {name}")
