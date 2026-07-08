
"""Trade safety gate."""

from __future__ import annotations

import pandas as pd

from atlas.investment.safety import limits


def evaluate_trade_safety(inputs: dict) -> dict:
    orders = inputs.get("orders")
    simulation = inputs.get("simulation", {}) or {}
    performance = inputs.get("performance", {}) or {}
    learning = inputs.get("learning", {}) or {}
    decision = inputs.get("decision", {}) or {}

    if orders is None or orders.empty:
        return reject("No execution orders available.")

    checks = []

    checks.extend(check_orders(orders))
    checks.extend(check_simulation(simulation))
    checks.extend(check_performance(performance))
    checks.extend(check_learning(learning))
    checks.extend(check_decision(decision))

    rejected = [c for c in checks if c["status"] == "REJECT"]
    warnings = [c for c in checks if c["status"] == "WARN"]

    approved = not rejected

    return {
        "success": True,
        "approved": approved,
        "safety_status": "APPROVED" if approved else "REJECTED",
        "check_count": len(checks),
        "reject_count": len(rejected),
        "warning_count": len(warnings),
        "checks": checks,
        "decision": "ALLOW_PAPER_EXECUTION" if approved else "BLOCK_EXECUTION",
        "reason": "All hard safety checks passed." if approved else rejected[0]["message"],
    }


def check_orders(orders: pd.DataFrame) -> list[dict]:
    checks = []

    actionable = orders[orders["order_action"].isin(["BUY", "SELL_SHORT"])] if "order_action" in orders else pd.DataFrame()

    checks.append(pass_or_reject(
        len(actionable) <= limits.MAX_ORDER_COUNT,
        "order_count",
        f"Actionable order count {len(actionable)} <= {limits.MAX_ORDER_COUNT}.",
        f"Too many actionable orders: {len(actionable)}.",
    ))

    if not limits.ALLOW_SHORTS and not actionable.empty:
        shorts = actionable[actionable["order_action"] == "SELL_SHORT"]
        checks.append(pass_or_reject(
            shorts.empty,
            "shorts_disabled",
            "No short orders present.",
            "Short orders present while shorts are disabled.",
        ))

    if "planned_weight" in orders:
        weights = pd.to_numeric(orders["planned_weight"], errors="coerce").fillna(0.0)
        max_weight = float(weights.max()) if len(weights) else 0.0
        checks.append(pass_or_reject(
            max_weight <= limits.MAX_SINGLE_ASSET_EXPOSURE,
            "single_asset_exposure",
            f"Max single asset planned weight {max_weight:.6f} within limit.",
            f"Single asset planned weight {max_weight:.6f} exceeds limit {limits.MAX_SINGLE_ASSET_EXPOSURE}.",
        ))

    return checks


def check_simulation(simulation: dict) -> list[dict]:
    summary = simulation.get("summary", {}) or {}
    checks = []

    filled = float(summary.get("filled_weight") or 0.0)
    cash = float(summary.get("cash_weight") or 0.0)
    waiting = float(summary.get("waiting_weight") or 0.0)
    cost = float(summary.get("total_cost_drag") or 0.0)

    checks.append(pass_or_reject(
        filled <= limits.MAX_TOTAL_EXPOSURE,
        "total_exposure",
        f"Filled exposure {filled:.6f} within limit.",
        f"Filled exposure {filled:.6f} exceeds limit {limits.MAX_TOTAL_EXPOSURE}.",
    ))

    checks.append(pass_or_reject(
        cash >= limits.MIN_CASH_WEIGHT,
        "cash_reserve",
        f"Cash reserve {cash:.6f} above minimum.",
        f"Cash reserve {cash:.6f} below minimum {limits.MIN_CASH_WEIGHT}.",
    ))

    checks.append(pass_or_reject(
        waiting <= limits.MAX_WAITING_WEIGHT,
        "waiting_weight",
        f"Waiting weight {waiting:.6f} within limit.",
        f"Waiting weight {waiting:.6f} exceeds limit {limits.MAX_WAITING_WEIGHT}.",
    ))

    checks.append(pass_or_reject(
        cost <= limits.MAX_COST_DRAG,
        "cost_drag",
        f"Cost drag {cost:.8f} within limit.",
        f"Cost drag {cost:.8f} exceeds limit {limits.MAX_COST_DRAG}.",
    ))

    return checks


def check_performance(performance: dict) -> list[dict]:
    pnl = performance.get("pnl", {}) or {}
    pnl_pct = float(pnl.get("pnl_pct") or 0.0)

    # Warning only for now because early paper trading may have sparse history.
    if pnl_pct < -0.05:
        return [{
            "name": "paper_drawdown",
            "status": "WARN",
            "message": f"Paper PnL is below -5%: {pnl_pct:.6f}.",
        }]

    return [{
        "name": "paper_drawdown",
        "status": "PASS",
        "message": f"Paper PnL acceptable: {pnl_pct:.6f}.",
    }]


def check_learning(learning: dict) -> list[dict]:
    regime = learning.get("learning_regime", {}) or {}
    state = regime.get("learning_regime")

    if state == "deteriorating":
        return [{
            "name": "learning_regime",
            "status": "WARN",
            "message": "Learning regime is deteriorating.",
        }]

    return [{
        "name": "learning_regime",
        "status": "PASS",
        "message": f"Learning regime acceptable: {state}.",
    }]


def check_decision(decision: dict) -> list[dict]:
    risk = decision.get("risk_adjusted_decision", {}) or {}
    confirmation = risk.get("confirmation_adjustment", {}) or {}

    if confirmation.get("status") == "execution_idle":
        return [{
            "name": "execution_confirmation",
            "status": "WARN",
            "message": "Execution layer is idle; exposure should remain reduced.",
        }]

    return [{
        "name": "execution_confirmation",
        "status": "PASS",
        "message": f"Execution confirmation status: {confirmation.get('status')}.",
    }]


def pass_or_reject(condition: bool, name: str, pass_message: str, reject_message: str) -> dict:
    return {
        "name": name,
        "status": "PASS" if condition else "REJECT",
        "message": pass_message if condition else reject_message,
    }


def reject(message: str) -> dict:
    return {
        "success": False,
        "approved": False,
        "safety_status": "REJECTED",
        "check_count": 0,
        "reject_count": 1,
        "warning_count": 0,
        "checks": [],
        "decision": "BLOCK_EXECUTION",
        "reason": message,
    }
