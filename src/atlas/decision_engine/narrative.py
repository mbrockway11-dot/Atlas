
"""Narrative explanation for decision comparisons."""

from __future__ import annotations

from typing import Any


def build_decision_narrative(report: dict[str, Any]) -> dict[str, Any]:
    """Build human-readable decision narrative."""
    comparison = report.get("comparison", {})
    winner = comparison.get("winner") or {}
    ranking = comparison.get("ranking", [])

    if not winner:
        return {
            "headline": "Decision path unresolved.",
            "recommendation": "Atlas could not compare the available options.",
            "watch_for": [],
        }

    label = winner.get("label", "the leading option")
    score = winner.get("overall_score", 0.0)

    return {
        "headline": f"Structurally strongest path: {label}",
        "recommendation": (
            f"Atlas currently reads {label} as the strongest structural fit with an alignment score of {score:.2f}. "
            "Read this as a decision-support signal, not a command. The best choice is the one whose tradeoffs you consciously accept."
        ),
        "why": build_why(ranking),
        "watch_for": build_watch_for(ranking),
    }


def build_why(ranking: list[dict[str, Any]]) -> list[str]:
    """Build why bullets."""
    if not ranking:
        return []

    top = ranking[0]

    return [
        f"Structural alignment: {top.get('alignment')}",
        f"Growth alignment: {top.get('growth')}",
        f"Recovery alignment: {top.get('recovery')}",
        f"Stress load: {top.get('stress')}",
    ]


def build_watch_for(ranking: list[dict[str, Any]]) -> list[str]:
    """Build watch-for bullets."""
    if not ranking:
        return []

    top = ranking[0]
    stress = float(top.get("stress") or 0.0)

    bullets = []

    if stress >= 0.45:
        bullets.append("The leading option may carry meaningful stress load. Build recovery time into the path.")

    if float(top.get("growth") or 0.0) < 0.65:
        bullets.append("Growth alignment is not dominant. Make sure the path does not only preserve comfort.")

    if float(top.get("recovery") or 0.0) < 0.70:
        bullets.append("Recovery quality is moderate. Define how the system returns to stability before committing.")

    if not bullets:
        bullets.append("The leading path is structurally coherent, but still needs real-world constraints checked.")

    return bullets
