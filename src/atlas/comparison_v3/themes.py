
"""Theme comparison logic."""

from __future__ import annotations

from typing import Any

from atlas.comparison_v3.extractors import extract_themes, pretty_label


def compare_themes(left_payload: dict[str, Any], right_payload: dict[str, Any]) -> dict[str, Any]:
    """Compare profile themes."""
    left = set(extract_themes(left_payload))
    right = set(extract_themes(right_payload))

    shared = sorted(left & right)
    left_unique = sorted(left - right)
    right_unique = sorted(right - left)

    return {
        "shared": shared,
        "left_unique": left_unique,
        "right_unique": right_unique,
        "shared_count": len(shared),
        "left_unique_count": len(left_unique),
        "right_unique_count": len(right_unique),
        "similarity": jaccard(left, right),
        "summary": build_theme_summary(shared, left_unique, right_unique),
    }


def jaccard(left: set[str], right: set[str]) -> float:
    """Compute Jaccard similarity."""
    if not left and not right:
        return 0.0

    return round(len(left & right) / max(1, len(left | right)), 6)


def build_theme_summary(shared: list[str], left_unique: list[str], right_unique: list[str]) -> str:
    """Build theme summary."""
    if shared:
        shared_text = ", ".join(pretty_label(item) for item in shared[:5])
        return f"Shared architecture appears around: {shared_text}."

    if left_unique or right_unique:
        return "The two profiles show more differentiated theme architecture than shared architecture."

    return "Theme comparison did not find enough structured data."
