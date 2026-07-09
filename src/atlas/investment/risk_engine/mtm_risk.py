
"""Direct MTM risk block."""

from __future__ import annotations

import pandas as pd


def mtm_position_risk(mtm_positions: pd.DataFrame) -> dict:
    if mtm_positions.empty:
        return {
            "risk_type": "mtm_position",
            "risk_score": 0.10,
            "warning_count": 1,
            "warnings": ["No MTM positions available."],
        }

    pnl_pct = pd.to_numeric(mtm_positions.get("unrealized_pnl_pct", 0.0), errors="coerce").fillna(0.0)
    weights = pd.to_numeric(mtm_positions.get("portfolio_weight", 0.0), errors="coerce").fillna(0.0)

    worst = float(pnl_pct.min()) if len(pnl_pct) else 0.0
    weighted_loss_pressure = float((pnl_pct.clip(upper=0).abs() * weights).sum())

    score = 0.0
    warnings = []

    if worst <= -0.10:
        score += 0.35
        warnings.append("At least one MTM position is below -10% unrealized.")
    elif worst < 0:
        score += 0.10
        warnings.append("At least one MTM position is negative.")

    if weighted_loss_pressure > 0.03:
        score += 0.25
        warnings.append("Weighted MTM loss pressure above 3%.")

    return {
        "risk_type": "mtm_position",
        "risk_score": round(min(score, 1.0), 6),
        "worst_unrealized_pnl_pct": round(worst, 6),
        "weighted_loss_pressure": round(weighted_loss_pressure, 6),
        "position_count": int(len(mtm_positions)),
        "warnings": warnings,
    }
