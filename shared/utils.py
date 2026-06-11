"""
Shared utilities used across all agents.
"""
import re
import json
from typing import Any


def clean_gemini_json(raw: str) -> dict:
    """Strip markdown code fences and parse Gemini JSON response."""
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_chars: int = 6000) -> str:
    """Truncate text to avoid exceeding Gemini token limits."""
    return text[:max_chars] if len(text) > max_chars else text
