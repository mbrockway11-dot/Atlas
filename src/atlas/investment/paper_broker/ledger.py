
"""Paper Broker v3 ledger and position accounting."""

from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd


INITIAL_EQUITY = 100000.0


def append_rows(existing: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    new = pd.DataFrame(rows)

    if existing is None or existing.empty:
        return new

    if new.empty:
        return existing

    return pd.concat([existing, new], ignore_index=True)


def build_trade_ledger_rows(fills: list[dict]) -> list[dict]:
    rows = []

    for fill in fills:
        rows.append({
            "timestamp": fill.get("filled_at") or datetime.now(UTC).isoformat(),
            "stable_order_key": fill.get("stable_order_key"),
            "asset": fill.get("asset"),
            "side": fill.get("side"),
            "action": fill.get("action"),
            "filled_weight": fill.get("filled_weight"),
            "notional_value": fill.get("notional_value"),
            "fee_drag": fill.get("fee_drag"),
            "slippage_drag": fill.get("slippage_drag"),
            "total_cost_drag": fill.get("total_cost_drag"),
            "source": "paper_broker_v3",
        })

    return rows


def build_cash_ledger_rows(fills: list[dict]) -> list[dict]:
    rows = []

    for fill in fills:
        action = str(fill.get("action") or "").upper()
        notional = float(fill.get("notional_value") or 0.0)

        cash_delta = -notional if action == "BUY" else notional if action == "SELL" else 0.0

        rows.append({
            "timestamp": fill.get("filled_at") or datetime.now(UTC).isoformat(),
            "stable_order_key": fill.get("stable_order_key"),
            "asset": "CASH",
            "cash_delta": round(cash_delta, 2),
            "reason": f"{action} {fill.get('asset')}",
            "source": "paper_broker_v3",
        })

    return rows


def rebuild_positions(all_fills: pd.DataFrame) -> pd.DataFrame:
    if all_fills is None or all_fills.empty:
        return pd.DataFrame(columns=[
            "asset", "side", "net_weight", "notional_value", "status", "source"
        ])

    df = all_fills.copy()
    df["filled_weight"] = pd.to_numeric(df.get("filled_weight", 0.0), errors="coerce").fillna(0.0)

    if "action" not in df.columns:
        df["action"] = "BUY"

    df["signed_weight"] = df.apply(
        lambda r: float(r["filled_weight"]) if str(r.get("action")).upper() == "BUY" else -float(r["filled_weight"]),
        axis=1,
    )

    grouped = df.groupby(["asset", "side"], as_index=False)["signed_weight"].sum()
    grouped["net_weight"] = grouped["signed_weight"].round(6)
    grouped["notional_value"] = (grouped["net_weight"] * INITIAL_EQUITY).round(2)
    grouped["status"] = grouped["net_weight"].apply(lambda x: "OPEN" if abs(float(x)) > 0.000001 else "CLOSED")
    grouped["source"] = "paper_broker_v3"

    return grouped[["asset", "side", "net_weight", "notional_value", "status", "source"]]


def current_cash(cash_ledger: pd.DataFrame, positions: pd.DataFrame) -> float:
    if cash_ledger is not None and not cash_ledger.empty and "cash_delta" in cash_ledger.columns:
        cash_delta = pd.to_numeric(cash_ledger["cash_delta"], errors="coerce").fillna(0.0).sum()
        return round(INITIAL_EQUITY + float(cash_delta), 2)

    risky_value = 0.0
    if positions is not None and not positions.empty and "notional_value" in positions.columns:
        risky_value = pd.to_numeric(positions["notional_value"], errors="coerce").fillna(0.0).sum()

    return round(INITIAL_EQUITY - float(risky_value), 2)
