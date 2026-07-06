
"""Inference comparison logic."""

from __future__ import annotations

from typing import Any

from atlas.comparison_v3.extractors import extract_inferences, extract_tensions, pretty_label


def compare_inferences(left_payload: dict[str, Any], right_payload: dict[str, Any]) -> dict[str, Any]:
    """Compare inference and tension patterns."""
    left = set(extract_inferences(left_payload))
    right = set(extract_inferences(right_payload))

    left_tensions = set(extract_tensions(left_payload))
    right_tensions = set(extract_tensions(right_payload))

    shared = sorted(left & right)

    return {
        "shared_inferences": shared,
        "left_unique_inferences": sorted(left - right),
        "right_unique_inferences": sorted(right - left),
        "shared_tensions": sorted(left_tensions & right_tensions),
        "left_unique_tensions": sorted(left_tensions - right_tensions),
        "right_unique_tensions": sorted(right_tensions - left_tensions),
        "inference_similarity": jaccard(left, right),
        "tension_similarity": jaccard(left_tensions, right_tensions),
        "summary": build_inference_summary(shared, left, right),
    }


def jaccard(left: set[str], right: set[str]) -> float:
    """Compute Jaccard similarity."""
    if not left and not right:
        return 0.0

    return round(len(left & right) / max(1, len(left | right)), 6)


def build_inference_summary(shared: list[str], left: set[str], right: set[str]) -> str:
    """Build inference summary."""
    if shared:
        text = ", ".join(pretty_label(item) for item in shared[:5])
        return f"The profiles share inference rules around: {text}."

    if left or right:
        return "The profiles appear to reach their structural conclusions through different inference paths."

    return "Inference comparison did not find enough structured data."
