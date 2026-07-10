
"""Portfolio State v4 builder."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_portfolio_state(inputs: dict) -> dict:
    mtm_report = inputs.get("mtm_report", {}) or {}
    mtm_positions = inputs.get("mtm_positions")

    equity_snapshot = mtm_report.get("equity_snapshot", {}) or {}

    equity = float(equity_snapshot.get("equity") or INITIAL_EQUITY)
    cash = float(equity_snapshot.get("cash") or 0.0)
    market_value = float(equity_snapshot.get("market_value") or 0.0)
    pnl = float(equity_snapshot.get("pnl") or 0.0)
    pnl_pct = float(equity_snapshot.get("pnl_pct") or 0.0)
    drawdown = float(equity_snapshot.get("drawdown") or 0.0)
    rolling_high = float(equity_snapshot.get("rolling_high") or equity)

    holdings = build_holdings(mtm_positions, cash, equity)

    risky_weight = market_value / equity if equity else 0.0
    cash_weight = cash / equity if equity else 0.0

    return {
        "version": "portfolio_state_v4",
        "source": "mark_to_market_v4_broker_state",
        "equity": {
            "current_equity": round(equity, 2),
            "initial_equity": INITIAL_EQUITY,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 6),
            "drawdown": round(drawdown, 6),
            "cash": round(cash, 2),
            "market_value": round(market_value, 2),
            "rolling_high": round(rolling_high, 2),
        },
        "exposure": {
            "risky_weight": round(risky_weight, 6),
            "cash_weight": round(cash_weight, 6),
            "reserved_cash_weight": 0.0,
            "gross_exposure": round(risky_weight, 6),
            "net_exposure": round(risky_weight, 6),
        },
        "holdings": holdings,
        "counts": {
            "holding_count": len(holdings),
            "risky_position_count": len([h for h in holdings if h.get("asset") != "CASH"]),
            "pending_order_count": 0,
            "ledger_row_count": int(len(inputs.get("broker_fills"))) if inputs.get("broker_fills") is not None else 0,
        },
        "direction": "LONG" if risky_weight > 0 else "CASH",
    }


def build_holdings(mtm_positions: pd.DataFrame, cash: float, equity: float) -> list[dict]:
    holdings = []

    if mtm_positions is not None and not mtm_positions.empty:
        for _, row in mtm_positions.iterrows():
            holdings.append({
                "asset": row.get("asset"),
                "side": row.get("side", "LONG"),
                "weight": round(float(row.get("portfolio_weight") or 0.0), 6),
                "value": round(float(row.get("market_value") or 0.0), 2),
                "quantity": row.get("quantity"),
                "current_price": row.get("current_price"),
                "avg_entry_price": row.get("avg_entry_price"),
                "unrealized_pnl": row.get("unrealized_pnl"),
                "unrealized_pnl_pct": row.get("unrealized_pnl_pct"),
                "source": "mark_to_market_v4",
            })

    holdings.append({
        "asset": "CASH",
        "side": "CASH",
        "weight": round(cash / equity, 6) if equity else 0.0,
        "value": round(cash, 2),
        "source": "broker_cash_ledger",
    })

    return holdings
