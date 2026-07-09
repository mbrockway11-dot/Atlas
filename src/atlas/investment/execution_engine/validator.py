
"""Execution Engine v3 validation."""

from __future__ import annotations

import pandas as pd


def validate_intents(intents: pd.DataFrame, safety: dict, risk: dict) -> list[dict]:
    rows = []

    safety_approved = bool(safety.get("approved"))
    safety_status = safety.get("status") or safety.get("safety_status")
    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")

    if intents.empty:
        return rows

    for _, row in intents.iterrows():
        asset = row.get("asset")
        action = str(row.get("order_action") or row.get("action") or "NO_ORDER").upper()
        side = str(row.get("side") or "LONG").upper()
        weight = float(row.get("planned_weight") or row.get("weight_delta") or 0.0)
        gate = str(row.get("execution_gate") or "OPEN")

        errors = []

        if not safety_approved:
            errors.append("Safety Governor did not approve execution.")

        if risk_label in {"high_risk", "critical_risk"}:
            errors.append(f"Risk label blocks execution: {risk_label}.")

        if gate.startswith("BLOCKED"):
            errors.append(f"Execution gate blocked: {gate}.")

        if action not in {"BUY", "SELL"}:
            errors.append(f"Unsupported order action: {action}.")

        if weight <= 0:
            errors.append("Order weight must be positive.")

        rows.append({
            "asset": asset,
            "side": side,
            "action": action,
            "requested_weight": round(weight, 6),
            "execution_gate": gate,
            "safety_status": safety_status,
            "risk_label": risk_label,
            "validation_status": "VALID" if not errors else "INVALID",
            "validation_errors": "; ".join(errors),
            "source": row.get("source", "execution_planner_v2"),
            "reason": row.get("reason"),
        })

    return rows
