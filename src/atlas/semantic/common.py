"""Shared semantic helpers."""

from __future__ import annotations

from typing import Any


def confidence(score: float, label: str | None = None) -> dict[str, Any]:
    """Build confidence object."""
    percent = round(score * 100, 2)
    return {
        "score": round(score, 4),
        "percent": percent,
        "label": label or label_from_score(score),
    }


def label_from_score(score: float) -> str:
    """Return confidence label."""
    if score >= 0.85:
        return "high"
    if score >= 0.65:
        return "moderate"
    if score >= 0.4:
        return "limited"
    return "low"


def evidence_item(source: str, claim: str, basis: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build semantic evidence record."""
    return {
        "source": source,
        "claim": claim,
        "basis": basis or {},
    }


def get_nested(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    """Safely read nested dict value."""
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def sentence_join(parts: list[str]) -> str:
    """Join readable paragraph parts."""
    return " ".join(part.strip() for part in parts if part and str(part).strip())


def humanize(value: str) -> str:
    """Humanize keys."""
    return str(value or "").replace("_", " ").replace("-", " ").title()
