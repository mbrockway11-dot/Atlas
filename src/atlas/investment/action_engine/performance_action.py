
"""Performance-based action votes."""

from __future__ import annotations


def performance_vote(position: dict, performance: dict) -> dict:
    pnl = performance.get("pnl", {}) or {}
    pnl_pct = float(pnl.get("pnl_pct") or 0.0)

    if pnl_pct <= -0.05:
        return vote("REDUCE", 0.80, "Paper PnL drawdown exceeds -5%.")

    if pnl_pct >= 0.05:
        return vote("HOLD", 0.65, "Paper PnL is positive; no exit pressure.")

    return vote("HOLD", 0.60, "Paper PnL is within normal range.")


def vote(action: str, confidence: float, reason: str) -> dict:
    return {
        "source": "performance",
        "action": action,
        "confidence": confidence,
        "reason": reason,
    }
