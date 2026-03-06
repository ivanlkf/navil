"""Optional dependency availability checks with graceful degradation."""

from __future__ import annotations

import importlib


def require_ml(feature_name: str = "ML features") -> None:
    """Raise ImportError with install instructions if scikit-learn is unavailable."""
    try:
        importlib.import_module("sklearn")
    except ImportError:
        raise ImportError(
            f"{feature_name} requires scikit-learn. Install with: pip install navil[ml]"
        ) from None


def require_llm(feature_name: str = "LLM features") -> None:
    """Raise ImportError with install instructions if no LLM SDK is available."""
    has_anthropic = False
    has_openai = False
    has_gemini = False
    try:
        importlib.import_module("anthropic")
        has_anthropic = True
    except ImportError:
        pass
    try:
        importlib.import_module("openai")
        has_openai = True
    except ImportError:
        pass
    try:
        importlib.import_module("google.generativeai")
        has_gemini = True
    except ImportError:
        pass

    if not has_anthropic and not has_openai and not has_gemini:
        raise ImportError(
            f"{feature_name} requires anthropic, openai, or google-generativeai SDK. "
            "Install with: pip install navil[llm]"
        ) from None


def has_ml() -> bool:
    """Check if ML dependencies are available."""
    try:
        require_ml()
        return True
    except ImportError:
        return False


def has_llm() -> bool:
    """Check if LLM dependencies are available."""
    try:
        require_llm()
        return True
    except ImportError:
        return False
