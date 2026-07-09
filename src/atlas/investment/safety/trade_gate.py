
"""Trade Safety Governor v3.

Consumes Risk Engine v3 MTM-aware risk output and hard-gates execution.
"""

from __future__ import annotations

import pandas as pd

from atlas.investment.safety import limits


MAX_MTM_RISK_SCORE = 0.45
MAX_MTM_DRAWDOWN = -0.10
MAX_MTM_GROSS_EXPOSURE = 0.85
MIN_MTM_CASH_WEIGHT = 0.15


def build_trade_safety_checks(inputs: dict) -> list[dict]:
    orders = inputs.get("orders")
    simulator = inputs.get("simulator", {}) or {}
    performance = inputs.get("performance", {}) or {}
    learning = inputs.get("learning", {}) or {}
    decision = inputs.get("decision", {}) or {}
    risk = inputs.get("risk", {}) or {}

    checks = []

    if orders is None or orders.empty:
        checks.append({
            "name": "orders_available",
            "status": "REJECT",
            "message": "No broker orders available.",
        })
        return checks

    checks.extend(check_orders(orders))
    checks.extend(check_simulator(simulator))
    checks.extend(check_performance(performance))
    checks.extend(check_learning(learning))
    checks.extend(check_decision(decision))
    checks.extend(check_risk_engine(risk))

    return checks


def check_orders(orders: pd.DataFrame) -> list[dict]:
    checks = []

    actionable = orders[orders["action"].isin(["BUY", "SELL"])] if "action" in orders else pd.DataFrame()

    checks.append(pass_or_reject(
        len(actionable) <= limits.MAX_ORDER_COUNT,
        "order_count",
        f"Actionable order count {len(actionable)} <= {limits.MAX_ORDER_COUNT}.",
        f"Actionable order count {len(actionable)} exceeds {limits.MAX_ORDER_COUNT}.",
    ))

    if "side" in orders:
        has_short = bool((orders["side"].astype(str).str.upper() == "SHORT").any())
        checks.append(pass_or_reject(
            not has_short,
            "shorts_disabled",
            "No short orders present.",
            "Short orders are disabled.",
        ))

    if "planned_weight" in orders:
        non_cash = orders[orders["asset"] != "CASH"].copy() if "asset" in orders else orders.copy()
        weights = pd.to_numeric(non_cash["planned_weight"], errors="coerce").fillna(0.0) if not non_cash.empty else pd.Series(dtype=float)
        max_weight = float(weights.max()) if len(weights) else 0.0
        checks.append(pass_or_reject(
            max_weight <= limits.MAX_SINGLE_ASSET_EXPOSURE,
            "single_asset_exposure",
            f"Max non-cash asset planned weight {max_weight:.6f} within limit.",
            f"Single non-cash asset planned weight {max_weight:.6f} exceeds limit {limits.MAX_SINGLE_ASSET_EXPOSURE}.",
        ))

    return checks


def check_simulator(simulator: dict) -> list[dict]:
    summary = simulator.get("summary", {}) or {}

    filled = float(summary.get("filled_weight") or 0.0)
    waiting = float(summary.get("waiting_weight") or 0.0)
    cost = float(summary.get("total_cost_drag") or 0.0)

    return [
        pass_or_reject(
            filled <= limits.MAX_TOTAL_EXPOSURE,
            "total_exposure",
            f"Filled exposure {filled:.6f} within limit.",
            f"Filled exposure {filled:.6f} exceeds limit {limits.MAX_TOTAL_EXPOSURE}.",
        ),
        pass_or_reject(
            waiting <= limits.MAX_WAITING_WEIGHT,
            "waiting_weight",
            f"Waiting weight {waiting:.6f} within limit.",
            f"Waiting weight {waiting:.6f} exceeds limit {limits.MAX_WAITING_WEIGHT}.",
        ),
        pass_or_reject(
            cost <= limits.MAX_COST_DRAG,
            "cost_drag",
            f"Cost drag {cost:.8f} within limit.",
            f"Cost drag {cost:.8f} exceeds limit {limits.MAX_COST_DRAG}.",
        ),
    ]


def check_performance(performance: dict) -> list[dict]:
    pnl = performance.get("pnl", {}) or {}
    pnl_pct = float(pnl.get("pnl_pct") or 0.0)

    max_drawdown = getattr(limits, "MAX_PAPER_DRAWDOWN", -0.10)

    return [
        pass_or_reject(
            pnl_pct >= max_drawdown,
            "paper_drawdown",
            f"Paper PnL acceptable: {pnl_pct:.6f}.",
            f"Paper PnL below allowed drawdown: {pnl_pct:.6f}.",
        )
    ]


def check_learning(learning: dict) -> list[dict]:
    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime")

    if regime == "deteriorating":
        return [{
            "name": "learning_regime",
            "status": "WARN",
            "message": "Learning regime is deteriorating.",
        }]

    return [{
        "name": "learning_regime",
        "status": "PASS",
        "message": f"Learning regime acceptable: {regime}.",
    }]


def check_decision(decision: dict) -> list[dict]:
    adjusted = decision.get("risk_adjusted_decision", {}) or {}
    confirmation = adjusted.get("confirmation_adjustment", {}) or {}

    if confirmation.get("status") == "execution_idle":
        return [{
            "name": "execution_confirmation",
            "status": "WARN",
            "message": "Execution layer is idle; exposure should remain reduced.",
        }]

    return [{
        "name": "execution_confirmation",
        "status": "PASS",
        "message": "Execution confirmation acceptable.",
    }]


def check_risk_engine(risk: dict) -> list[dict]:
    aggregate = risk.get("aggregate", {}) or {}
    blocks = risk.get("risk_blocks", []) or []

    score = float(aggregate.get("aggregate_risk_score") or 0.0)
    label = str(aggregate.get("risk_label") or "unknown")

    checks = []

    checks.append(pass_or_reject(
        score < MAX_MTM_RISK_SCORE and label not in {"high_risk", "critical_risk"},
        "risk_engine_score",
        f"Risk Engine acceptable: score={score:.6f}, label={label}.",
        f"Risk Engine blocks execution: score={score:.6f}, label={label}.",
    ))

    exposure_block = find_block(blocks, "exposure")
    drawdown_block = find_block(blocks, "drawdown")

    gross = float(exposure_block.get("gross_exposure") or 0.0)
    cash = float(exposure_block.get("cash_weight") or 0.0)
    drawdown = float(drawdown_block.get("drawdown") or 0.0)

    checks.append(pass_or_reject(
        gross <= MAX_MTM_GROSS_EXPOSURE,
        "mtm_gross_exposure",
        f"MTM gross exposure {gross:.6f} within limit.",
        f"MTM gross exposure {gross:.6f} exceeds limit {MAX_MTM_GROSS_EXPOSURE}.",
    ))

    checks.append(pass_or_reject(
        cash >= MIN_MTM_CASH_WEIGHT,
        "mtm_cash_reserve",
        f"MTM cash reserve {cash:.6f} above minimum.",
        f"MTM cash reserve {cash:.6f} below minimum {MIN_MTM_CASH_WEIGHT}.",
    ))

    checks.append(pass_or_reject(
        drawdown >= MAX_MTM_DRAWDOWN,
        "mtm_drawdown",
        f"MTM drawdown {drawdown:.6f} within limit.",
        f"MTM drawdown {drawdown:.6f} below limit {MAX_MTM_DRAWDOWN}.",
    ))

    return checks


def find_block(blocks: list[dict], risk_type: str) -> dict:
    for block in blocks:
        if block.get("risk_type") == risk_type:
            return block
    return {}


def pass_or_reject(condition: bool, name: str, pass_message: str, reject_message: str) -> dict:
    return {
        "name": name,
        "status": "PASS" if condition else "REJECT",
        "message": pass_message if condition else reject_message,
    }



def evaluate_trade_safety(inputs: dict) -> dict:
    checks = build_trade_safety_checks(inputs)

    has_reject = any(c.get("status") == "REJECT" for c in checks)
    has_warn = any(c.get("status") == "WARN" for c in checks)

    status = "REJECTED" if has_reject else "APPROVED"
    decision = "BLOCK_EXECUTION" if has_reject else "ALLOW_PAPER_EXECUTION"

    if has_reject:
        reason = next((c.get("message") for c in checks if c.get("status") == "REJECT"), "Rejected by safety checks.")
    elif has_warn:
        reason = "All hard safety checks passed with warnings."
    else:
        reason = "All hard safety checks passed."

    return {
        "success": True,
        "approved": not has_reject,
        "status": status,
        "safety_status": status,
        "decision": decision,
        "reason": reason,
        "checks": checks,
    }
