
"""Structural evidence models for Atlas Synthesis.

Every Atlas engine should eventually emit StructuralEvidence records instead
of writing final prose directly.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


SYNTHESIS_EVIDENCE_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralEvidence:
    """One standardized evidence record produced by an Atlas engine."""

    engine: str
    feature: str
    category: str
    value: Any

    confidence: float = 0.5
    weight: float = 1.0

    explanation: str = ""
    source: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceBundle:
    """A collection of evidence records for one profile."""

    version: str
    profile_key: str
    evidence: tuple[StructuralEvidence, ...]


def evidence_to_dict(evidence: StructuralEvidence) -> dict[str, Any]:
    """Convert evidence record to JSON-safe dict."""
    data = asdict(evidence)
    data["tags"] = list(evidence.tags)
    return data


def evidence_from_dict(data: dict[str, Any]) -> StructuralEvidence:
    """Build evidence record from dict."""
    return StructuralEvidence(
        engine=str(data.get("engine", "unknown")),
        feature=str(data.get("feature", "unknown")),
        category=str(data.get("category", "unknown")),
        value=data.get("value"),
        confidence=safe_float(data.get("confidence"), 0.5),
        weight=safe_float(data.get("weight"), 1.0),
        explanation=str(data.get("explanation", "")),
        source=str(data.get("source", "")),
        tags=tuple(str(item) for item in data.get("tags", []) or []),
    )


def bundle_to_dict(bundle: EvidenceBundle) -> dict[str, Any]:
    """Convert evidence bundle to JSON-safe dict."""
    return {
        "version": bundle.version,
        "profile_key": bundle.profile_key,
        "evidence": [
            evidence_to_dict(item)
            for item in bundle.evidence
        ],
    }


def make_evidence(
    *,
    engine: str,
    feature: str,
    category: str,
    value: Any,
    confidence: float = 0.5,
    weight: float = 1.0,
    explanation: str = "",
    source: str = "",
    tags: list[str] | tuple[str, ...] | None = None,
) -> StructuralEvidence:
    """Create normalized evidence."""
    return StructuralEvidence(
        engine=engine,
        feature=normalize_feature(feature),
        category=normalize_feature(category),
        value=value,
        confidence=clamp(confidence),
        weight=max(0.0, safe_float(weight, 1.0)),
        explanation=explanation,
        source=source,
        tags=tuple(tags or ()),
    )


def normalize_feature(value: str) -> str:
    """Normalize feature/category labels."""
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def clamp(value: Any, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp numeric value to range."""
    numeric = safe_float(value, 0.5)
    return max(minimum, min(maximum, numeric))


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except Exception:
        return default
