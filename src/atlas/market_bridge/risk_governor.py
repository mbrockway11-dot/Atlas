
"""Paper-only Market Bridge risk governor."""

from __future__ import annotations

from typing import Any


def evaluate_market_risk(
    market_state: dict[str, Any],
    *,
    paper_only: bool = True,
    min_confidence: float = 0.70,
    max_position_size: float = 0.10,
) -> dict[str, Any]:
    """Evaluate paper-only research risk."""
    reasons = []

    if paper_only:
        reasons.append("Paper-only mode is enforced.")

    if not market_state.get("entry_ready"):
        reasons.append("Entry is not ready.")

    if float(market_state.get("confidence") or 0.0) < min_confidence:
        reasons.append("Confidence is below minimum threshold.")

    if market_state.get("asset") in {"", "UNKNOWN"}:
        reasons.append("No valid asset detected.")

    blockers = {
        "Entry is not ready.",
        "Confidence is below minimum threshold.",
        "No valid asset detected.",
    }

    allowed_research_decision = not any(reason in blockers for reason in reasons)

    return {
        "success": True,
        "risk_mode": "paper_only" if paper_only else "research_only",
        "allowed_execution": False,
        "allowed_research_decision": allowed_research_decision,
        "max_position_size": max_position_size,
        "reasons": reasons,
        "summary": build_summary(allowed_research_decision, reasons),
    }


def build_summary(allowed: bool, reasons: list[str]) -> str:
    if allowed:
        return "Risk Governor allows paper-only research decision. Live execution remains disabled."
    return "Risk Governor blocked action: " + "; ".join(reasons)
