
"""Shared helpers for synthesis adapters."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.evidence import StructuralEvidence, make_evidence
from atlas.synthesis.ontology import category_for_feature


def make_record(
    engine: str,
    feature: str,
    value: Any,
    confidence: float,
) -> StructuralEvidence:
    """Create an ontology-backed evidence record."""
    return make_evidence(
        engine=engine,
        feature=feature,
        category=category_for_feature(feature),
        value=value,
        confidence=confidence,
        weight=1.0,
        explanation=f"{engine} supports {feature}.",
        source=engine,
        tags=[engine.split(".")[0], feature],
    )


def safe_dict(value: Any) -> dict[str, Any]:
    """Return dict or empty dict."""
    return value if isinstance(value, dict) else {}


def safe_float(value: Any, default: float = 0.0) -> float:
    """Return float or default."""
    try:
        return float(value)
    except Exception:
        return default
