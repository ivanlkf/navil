"""Model serialization and version management."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from navil._compat import require_ml

logger = logging.getLogger(__name__)


class ModelStore:
    """Manages trained ML model persistence with versioning."""

    def __init__(self, base_dir: str = ".navil/models") -> None:
        require_ml("Model storage")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, model: Any, name: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Save a model with metadata. Returns version ID."""
        import joblib

        version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        model_dir = self.base_dir / name / version
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / "model.joblib"
        joblib.dump(model, str(model_path))

        meta = {
            "name": name,
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        meta_path = model_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2))

        # Update latest pointer
        latest_path = self.base_dir / name / "latest.json"
        latest_path.write_text(json.dumps({"version": version}))

        logger.info(f"Model '{name}' saved as version {version}")
        return version

    def load(self, name: str, version: str | None = None) -> Any:
        """Load a model by name, optionally at specific version."""
        import joblib

        if version is None:
            latest_path = self.base_dir / name / "latest.json"
            if not latest_path.exists():
                raise FileNotFoundError(f"No model found: {name}")
            version = json.loads(latest_path.read_text())["version"]

        model_path = self.base_dir / name / version / "model.joblib"
        return joblib.load(str(model_path))

    def list_models(self) -> list[dict[str, str]]:
        """List all saved models and their latest versions."""
        models = []
        if not self.base_dir.exists():
            return models
        for model_dir in self.base_dir.iterdir():
            if model_dir.is_dir():
                latest_path = model_dir / "latest.json"
                if latest_path.exists():
                    info = json.loads(latest_path.read_text())
                    models.append(
                        {"name": model_dir.name, "version": info["version"]}
                    )
        return models
