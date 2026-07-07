
"""Scientific Confidence Engine report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.confidence.extractors import extract_confidence_inputs
from atlas.autonomous.confidence.scoring import score_scientific_confidence


CONFIDENCE_ENGINE_VERSION = "1.0.0"


def build_scientific_confidence_report(
    autonomous_report: dict[str, Any],
) -> dict[str, Any]:
    """Build scientific confidence report."""
    inputs = extract_confidence_inputs(autonomous_report)
    score = score_scientific_confidence(**inputs)

    return {
        "success": True,
        "version": CONFIDENCE_ENGINE_VERSION,
        "inputs": inputs,
        **score,
        "summary": build_summary(score),
    }


def build_summary(score: dict[str, Any]) -> str:
    """Build confidence summary."""
    return (
        f"Scientific Confidence Engine assigned "
        f"{score.get('scientific_confidence')} "
        f"({score.get('confidence_label')})."
    )
