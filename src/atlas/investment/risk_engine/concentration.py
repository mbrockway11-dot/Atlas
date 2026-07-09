
"""MTM position concentration risk."""

from __future__ import annotations

import pandas as pd


def concentration_risk(portfolio_state: dict, mtm_positions: pd.DataFrame | None = None) -> dict:
    if mtm_positions is not None and not mtm_positions.empty:
        df = mtm_positions.copy()
        weights = pd.to_numeric(df.get("portfolio_weight", 0.0), errors="coerce").fillna(0.0).abs()
        asset_count = int(len(df))
        max_weight = float(weights.max()) if len(weights) else 0.0
        source = "mtm_positions"
    else:
        state = portfolio_state.get("state", {}) or {}
        holdings = state.get("holdings", []) or []
        risky = [h for h in holdings if h.get("asset") not in {"CASH", "RESERVED_CASH"}]
        weights = [abs(float(h.get("paper_weight") or 0.0)) for h in risky]
        asset_count = len(risky)
        max_weight = max(weights) if weights else 0.0
        source = "portfolio_state"

    score = 0.0
    warnings = []

    if max_weight > 0.40:
        score += 0.45
        warnings.append("Largest MTM position above 40%.")
    elif max_weight > 0.30:
        score += 0.25
        warnings.append("Largest MTM position above 30%.")

    if asset_count < 2:
        score += 0.25
        warnings.append("Fewer than 2 risky MTM positions.")

    return {
        "risk_type": "concentration",
        "risk_score": round(min(score, 1.0), 6),
        "max_position_weight": round(float(max_weight), 6),
        "asset_count": asset_count,
        "source": source,
        "warnings": warnings,
    }
