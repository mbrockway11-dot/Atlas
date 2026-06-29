"""Atlas differential research helpers."""

from typing import Any


def ranked_differences(distance_by_key: dict[str, float]) -> list[dict[str, float]]:
    """Rank differences from largest to smallest."""
    return [
        {
            "key": key,
            "difference": value,
        }
        for key, value in sorted(
            distance_by_key.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def summarize_profile_difference(comparison: dict[str, Any]) -> dict[str, Any]:
    """Summarize largest structural differences from comparison output."""
    subtype_ranked = ranked_differences(
        comparison["subtype"]["distance_by_key"]
    )
    planetary_ranked = ranked_differences(
        comparison["planetary"]["distance_by_key"]
    )
    essence_ranked = ranked_differences(
        comparison["essence_function"]["distance_by_key"]
    )

    return {
        "profile_a": comparison["profile_a"],
        "profile_b": comparison["profile_b"],
        "overall_similarity": comparison["overall_similarity"],
        "largest_subtype_difference": subtype_ranked[0] if subtype_ranked else None,
        "largest_planetary_difference": planetary_ranked[0] if planetary_ranked else None,
        "largest_essence_difference": essence_ranked[0] if essence_ranked else None,
        "subtype_differences": subtype_ranked,
        "planetary_differences": planetary_ranked,
        "essence_differences": essence_ranked,
    }