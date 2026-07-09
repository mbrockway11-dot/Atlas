
"""Map strategies to decision families."""

from __future__ import annotations


def strategy_family_from_id(strategy_id: str | None) -> str:
    sid = str(strategy_id or "").lower()

    if "breadth" in sid:
        return "breadth"
    if "momentum" in sid:
        return "momentum"
    if "leader" in sid or "leadership" in sid:
        return "leadership"
    if "topology" in sid:
        return "topology"
    if "portfolio" in sid:
        return "portfolio_allocation"
    if "cross_sectional" in sid or "ranker" in sid:
        return "cross_sectional_ranking"
    if "engine_a" in sid or "engine_b" in sid or "v32" in sid:
        return "intraday_execution"

    return "unknown"
