# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Apache License, Version 2.0 (see LICENSE)
"""LLM-powered analysis features (requires navil[llm]).

Install with: pip install navil[llm]
"""

from __future__ import annotations

import json
import re
from typing import Any


def _repair_truncated_json(text: str) -> str:
    """Attempt to repair JSON truncated by max_tokens.

    Closes open brackets/braces and removes trailing incomplete values
    so that ``json.loads`` can parse the partial result.
    """
    # Remove trailing incomplete string values (e.g., `"reason": "some text...`)
    text = re.sub(r',\s*"[^"]*":\s*"[^"]*$', "", text)
    # Remove trailing key without value (e.g., `"reason":`)
    text = re.sub(r',\s*"[^"]*":\s*$', "", text)

    # Count open/close brackets and braces
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch == "}" and stack and stack[-1] == "{" or ch == "]" and stack and stack[-1] == "[":
            stack.pop()

    # Close any remaining open brackets/braces
    closers = {"[": "]", "{": "}"}
    for opener in reversed(stack):
        text += closers[opener]

    return text


def extract_json(text: str) -> str:
    """Extract and optionally repair JSON from an LLM response."""
    raw = _strip_fences(text)
    # Try parsing directly first
    try:
        json.loads(raw)
        return raw
    except (json.JSONDecodeError, ValueError):
        pass
    # Try repairing truncated JSON
    repaired = _repair_truncated_json(raw)
    try:
        json.loads(repaired)
        return repaired
    except (json.JSONDecodeError, ValueError):
        pass
    return raw


def _strip_fences(text: str) -> str:
    """Strip markdown code fences and locate JSON in free text."""
    # Closed ```json ... ``` fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Unclosed fence (truncated by max_tokens)
    m = re.search(r"```(?:json)?\s*\n?(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Top-level JSON object in free text
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return text


def __getattr__(name: str) -> Any:
    if name == "LLMClient":
        from navil.llm.client import LLMClient

        return LLMClient
    if name == "LLMAnalyzer":
        from navil.llm.analyzer import LLMAnalyzer

        return LLMAnalyzer
    if name == "PolicyGenerator":
        from navil.llm.policy_gen import PolicyGenerator

        return PolicyGenerator
    if name == "SelfHealingEngine":
        from navil.llm.self_healing import SelfHealingEngine

        return SelfHealingEngine
    raise AttributeError(f"module 'navil.llm' has no attribute {name}")
