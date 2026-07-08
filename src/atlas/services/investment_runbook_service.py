
"""Investment Runbook dashboard service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


RUNBOOK_JSON = Path("output/investment_runbook/daily_investment_runbook.json")
HISTORY_CSV = Path("output/investment_runbook/runbook_history.csv")


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_runbook_payload() -> dict[str, Any]:
    payload = load_json(RUNBOOK_JSON)
    history = pd.read_csv(HISTORY_CSV) if HISTORY_CSV.exists() else pd.DataFrame()

    snapshot = payload.get("final_snapshot", {}) or {}
    decision = snapshot.get("decision", {}) or {}
    sim = snapshot.get("simulation_summary", {}) or {}

    return {
        "success": bool(payload.get("success")),
        "summary": payload.get("summary", ""),
        "decision": decision,
        "simulation": sim,
        "orders": snapshot.get("execution_orders", []) or [],
        "fills": snapshot.get("simulation_fills", []) or [],
        "steps": payload.get("steps", []) or [],
        "history": history,
        "raw": payload,
    }


def append_runbook_history(report: dict[str, Any]) -> None:
    HISTORY_CSV.parent.mkdir(parents=True, exist_ok=True)

    snapshot = report.get("final_snapshot", {}) or {}
    decision = snapshot.get("decision", {}) or {}
    sim = snapshot.get("simulation_summary", {}) or {}

    row = {
        "ended": report.get("ended"),
        "success": report.get("success"),
        "step_count": report.get("step_count"),
        "direction": decision.get("final_direction"),
        "confidence": decision.get("final_confidence"),
        "target_exposure": decision.get("target_net_exposure"),
        "cash_weight": decision.get("target_cash_weight"),
        "risk_label": decision.get("risk_label"),
        "filled_weight": sim.get("filled_weight"),
        "waiting_weight": sim.get("waiting_weight"),
        "cost_drag": sim.get("total_cost_drag"),
        "warning_count": sim.get("warning_count"),
    }

    old = pd.read_csv(HISTORY_CSV) if HISTORY_CSV.exists() else pd.DataFrame()
    new = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    new.to_csv(HISTORY_CSV, index=False)
