
"""Execution gating from registry signals."""

from __future__ import annotations

import pandas as pd


def apply_execution_gates(plan: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    """Apply structural execution gates from V32 and other execution engines."""
    if plan.empty:
        return plan

    out = plan.copy()
    out["execution_gate"] = "OPEN"
    out["gate_reason"] = "No blocking execution signal."

    if registry.empty:
        return out

    reg = registry.copy()
    reg["source"] = reg["source"].fillna("").astype(str)
    reg["strategy_family"] = reg["strategy_family"].fillna("").astype(str)
    reg["action"] = reg["action"].fillna("").astype(str).str.upper()
    reg["direction"] = reg["direction"].fillna("").astype(str).str.upper()

    execution_rows = reg[reg["strategy_family"] == "intraday_execution"]

    for idx, row in out.iterrows():
        asset = row.get("asset")

        if asset == "CASH":
            out.at[idx, "execution_gate"] = "OPEN"
            out.at[idx, "gate_reason"] = "Cash row."
            continue

        matching = execution_rows[execution_rows["asset"] == asset]

        if matching.empty:
            out.at[idx, "execution_gate"] = "OPEN"
            out.at[idx, "gate_reason"] = "No execution adapter signal for asset."
            continue

        active = matching[~matching["action"].isin(["NO_ACTION", "WAIT"])]

        if active.empty:
            out.at[idx, "execution_gate"] = "WAIT"
            out.at[idx, "gate_reason"] = "Execution engines are idle; wait for structure confirmation."
        else:
            out.at[idx, "execution_gate"] = "CONFIRMED"
            out.at[idx, "gate_reason"] = "Execution adapter confirms active structure."

    return out
