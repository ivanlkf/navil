"""Isolation Forest anomaly detection wrapper."""

from __future__ import annotations

import logging
from typing import Any

from navil._compat import require_ml
from navil.anomaly_detector import ToolInvocation
from navil.ml.features import FeatureExtractor

logger = logging.getLogger(__name__)


class IsolationForestDetector:
    """Unsupervised anomaly detection using Isolation Forest.

    Wraps scikit-learn's IsolationForest with a ToolInvocation-aware
    feature extraction pipeline and 0-1 anomaly scoring.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        require_ml("Isolation Forest")
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self.scaler = StandardScaler()
        self.feature_extractor = FeatureExtractor()
        self.is_fitted = False

    def train(self, invocations: list[ToolInvocation]) -> dict[str, Any]:
        """Train the model on historical invocations.

        Args:
            invocations: List of at least 50 ToolInvocation records.

        Returns:
            Training statistics dict.

        Raises:
            ValueError: If fewer than 50 invocations provided.
        """
        import numpy as np

        if len(invocations) < 50:
            raise ValueError(f"Need >= 50 invocations for training, got {len(invocations)}")

        X = self.feature_extractor.extract_batch(invocations)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True

        scores = self.model.decision_function(X_scaled)
        return {
            "samples_trained": len(invocations),
            "features": len(FeatureExtractor.FEATURE_NAMES),
            "anomaly_score_mean": float(np.mean(scores)),
            "anomaly_score_std": float(np.std(scores)),
        }

    def score(self, invocation: ToolInvocation, history: list[ToolInvocation]) -> float:
        """Score a single invocation. Returns 0.0 (normal) to 1.0 (anomalous)."""
        import numpy as np

        if not self.is_fitted:
            return 0.0

        features = self.feature_extractor.extract_single(invocation, history)
        X = np.array([features])
        X_scaled = self.scaler.transform(X)

        raw_score = self.model.decision_function(X_scaled)[0]
        confidence = max(0.0, min(1.0, 0.5 - raw_score))
        return confidence

    def save(self, path: str) -> None:
        """Save model to disk."""
        import joblib

        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "feature_extractor": self.feature_extractor,
            },
            path,
        )

    def load(self, path: str) -> None:
        """Load model from disk."""
        import joblib

        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_extractor = data["feature_extractor"]
        self.is_fitted = True
