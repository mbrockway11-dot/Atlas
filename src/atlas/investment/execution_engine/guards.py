
"""Execution safety guards."""

from __future__ import annotations

import pandas as pd


LIVE_TRADING_ENABLED = False


def apply_execution_guards(orders: pd.DataFrame, safety: dict, risk: dict, *, mode: str = "paper") -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame()

    out = orders.copy()

    safety_ok = bool(safety.get("approved"))
    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")

    out["safety_approved"] = safety_ok
    out["risk_label"] = risk_label
    out["live_trading_enabled"] = LIVE_TRADING_ENABLED

    if not safety_ok:
        out["execution_status"] = "BLOCKED_BY_SAFETY"
        out["guard_reason"] = safety.get("reason", "Safety Governor rejected execution.")
        return out

    if mode == "live" and not LIVE_TRADING_ENABLED:
        out["execution_status"] = "BLOCKED_LIVE_DISABLED"
        out["guard_reason"] = "Live trading is disabled in Execution Engine."
        return out

    if risk_label in {"critical_risk", "high_risk"}:
        out["execution_status"] = "BLOCKED_BY_RISK"
        out["guard_reason"] = f"Risk label is {risk_label}."
        return out

    out["execution_status"] = "APPROVED_FOR_EXECUTION"
    out["guard_reason"] = "Passed execution guards."

    return out
