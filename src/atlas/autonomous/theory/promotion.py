
"""Theory promotion."""

from __future__ import annotations

from typing import Any


def promote_theories(
    scored_candidates: list[dict[str, Any]],
    *,
    threshold: float = 0.58,
) -> list[dict[str, Any]]:
    """Promote sufficiently supported theories."""
    promoted = []

    for candidate in scored_candidates:
        score = float(candidate.get("theory_score") or 0.0)

        status = "promoted" if score >= threshold else "candidate"

        promoted.append(
            {
                **candidate,
                "status": status,
                "promotion_threshold": threshold,
                "promotion_reason": promotion_reason(candidate, threshold),
            }
        )

    return promoted


def promotion_reason(candidate: dict[str, Any], threshold: float) -> str:
    """Explain promotion status."""
    score = float(candidate.get("theory_score") or 0.0)

    if score >= threshold:
        return (
            f"Promoted because theory score {score:.3f} met or exceeded threshold {threshold:.3f}."
        )

    return (
        f"Not promoted because theory score {score:.3f} is below threshold {threshold:.3f}."
    )
