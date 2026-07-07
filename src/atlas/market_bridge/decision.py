
"""Market Bridge decision engine."""

from __future__ import annotations

from typing import Any

from atlas.market_bridge.risk_governor import evaluate_market_risk


def build_market_decision(
    market_state: dict[str, Any],
    *,
    paper_only: bool = True,
    min_confidence: float = 0.70,
) -> dict[str, Any]:
    """Build paper-only market recommendation."""
    risk = evaluate_market_risk(
        market_state,
        paper_only=paper_only,
        min_confidence=min_confidence,
    )

    action = market_state.get("action", "UNKNOWN")
    confidence = float(market_state.get("confidence") or 0.0)

    if not risk.get("allowed_research_decision"):
        decision = "NO_TRADE"
    elif action in {"LONG", "SHORT", "EXIT"}:
        decision = action
    elif confidence >= min_confidence:
        decision = "WATCH"
    else:
        decision = "NO_TRADE"

    return {
        "success": True,
        "decision": decision,
        "asset": market_state.get("asset"),
        "direction": market_state.get("direction"),
        "confidence": confidence,
        "allowed_execution": False,
        "risk": risk,
        "reason": build_reason(decision, market_state, risk),
        "market_state": market_state,
    }


def build_reason(decision: str, market_state: dict[str, Any], risk: dict[str, Any]) -> str:
    if decision == "NO_TRADE":
        return risk.get("summary", "No trade conditions met.")

    return (
        f"Market Bridge produced {decision} paper-only research decision for "
        f"{market_state.get('asset')} with confidence {market_state.get('confidence')}. "
        "Live execution remains disabled."
    )
