
"""Performance v2 PnL."""

from __future__ import annotations

INITIAL_EQUITY = 100000.0


def calculate_pnl_from_state(state_report: dict, initial_equity: float = INITIAL_EQUITY) -> dict:
    state = state_report.get("state", {}) or {}
    equity = state.get("equity", {}) or {}

    current = float(equity.get("current_equity") or initial_equity)
    pnl = current - initial_equity
    pnl_pct = pnl / initial_equity if initial_equity else 0.0

    return {
        "initial_equity": round(float(initial_equity), 2),
        "current_equity": round(float(current), 2),
        "pnl": round(float(pnl), 2),
        "pnl_pct": round(float(pnl_pct), 6),
        "source": "portfolio_state_v2",
    }
