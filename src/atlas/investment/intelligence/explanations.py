
"""Asset and portfolio explanations."""

from __future__ import annotations

import pandas as pd


def build_portfolio_explanation(
    inputs: dict,
    confidence: dict,
) -> dict:
    portfolio = inputs.get("portfolio_state", {}) or {}
    learning = inputs.get("learning", {}) or {}
    risk = inputs.get("risk", {}) or {}
    rebalance = inputs.get("rebalance", {}) or {}

    state = portfolio.get("state", {}) or {}
    equity = state.get("equity", {}) or {}
    exposure = state.get("exposure", {}) or {}

    if not equity:
        equity = portfolio.get("equity", {}) or {}

    if not exposure:
        exposure = portfolio.get("exposure", {}) or {}

    learning_regime = (
        learning.get("learning_regime", {}) or {}
    ).get("learning_regime", "unknown")

    aggregate_risk = risk.get("aggregate", {}) or {}

    return {
        "current_equity": number(
            equity.get("current_equity")
            or equity.get("equity")
        ),
        "pnl_pct": number(equity.get("pnl_pct")),
        "drawdown": number(equity.get("drawdown")),
        "risky_weight": number(
            exposure.get("risky_weight")
        ),
        "cash_weight": number(
            exposure.get("cash_weight")
        ),
        "learning_regime": learning_regime,
        "risk_label": aggregate_risk.get(
            "risk_label",
            "unknown",
        ),
        "overall_confidence": confidence.get(
            "overall_confidence",
            0.0,
        ),
        "confidence_label": confidence.get(
            "confidence_label",
            "LOW",
        ),
        "rebalance_order_count": len(
            rebalance.get("orders", []) or []
        ),
        "explanation": portfolio_narrative(
            exposure,
            learning_regime,
            confidence,
            rebalance,
        ),
    }


def build_asset_explanations(inputs: dict) -> list[dict]:
    scores = inputs.get("alpha_ensemble_scores")
    adaptive = inputs.get("adaptive_weights")
    mtm = inputs.get("mtm_positions")
    registry = inputs.get("strategy_registry_csv")

    assets = collect_assets(
        scores,
        adaptive,
        mtm,
        registry,
    )

    rows = []

    for asset in sorted(assets):
        score_row = find_row(scores, asset)
        weight_row = find_row(adaptive, asset)
        mtm_row = find_row(mtm, asset)
        registry_row = find_row(registry, asset)

        current_weight = number(
            mtm_row.get("portfolio_weight")
            or mtm_row.get("weight")
        )
        target_weight = number(
            weight_row.get("adaptive_weight")
        )

        ensemble_score = number(
            score_row.get("ensemble_score")
        )

        lifecycle_status = str(
            registry_row.get("status") or "UNKNOWN"
        )

        rows.append({
            "asset": asset,
            "ensemble_score": ensemble_score,
            "ensemble_action": score_row.get(
                "ensemble_action",
                "UNKNOWN",
            ),
            "source_count": int(
                number(score_row.get("source_count"))
            ),
            "current_weight": current_weight,
            "target_weight": target_weight,
            "weight_delta": round(
                target_weight - current_weight,
                6,
            ),
            "unrealized_pnl": number(
                mtm_row.get("unrealized_pnl")
            ),
            "unrealized_pnl_pct": number(
                mtm_row.get("unrealized_pnl_pct")
            ),
            "registry_status": lifecycle_status,
            "asset_confidence": number(
                registry_row.get("asset_confidence")
            ),
            "explanation": asset_narrative(
                asset=asset,
                ensemble_score=ensemble_score,
                current_weight=current_weight,
                target_weight=target_weight,
                lifecycle_status=lifecycle_status,
            ),
        })

    return rows


def build_trade_explanations(inputs: dict) -> list[dict]:
    rebalance = inputs.get("rebalance", {}) or {}
    orders = rebalance.get("orders", []) or []

    rows = []

    for row in orders:
        asset = row.get("asset")
        action = row.get("action")
        current = number(row.get("current_weight"))
        target = number(row.get("target_weight"))
        delta = number(row.get("signed_delta"))

        rows.append({
            "asset": asset,
            "action": action,
            "current_weight": current,
            "target_weight": target,
            "signed_delta": delta,
            "priority": row.get("priority"),
            "reason": row.get("reason"),
            "explanation": (
                f"{action} {asset} because its current portfolio "
                f"weight is {current:.4%} and its adaptive target "
                f"is {target:.4%}. Required change: {delta:.4%}."
            ),
        })

    return rows


def build_decision_chain(inputs: dict) -> list[dict]:
    chain = [
        ("Market Features", "market_features"),
        ("Alpha Hypotheses", "alpha_hypotheses"),
        ("Alpha Validation", "alpha_validation"),
        ("Alpha Ensemble v4", "alpha_ensemble"),
        ("Adaptive Weighting v4", "adaptive_weighting"),
        ("Alpha Portfolio", "alpha_portfolio"),
        ("Rebalance Engine v4", "rebalance"),
        ("Execution Planner", "execution_planner"),
        ("Safety Governor", "safety"),
        ("Execution Engine", "execution_engine"),
        ("Paper Broker", "paper_broker"),
        ("Broker Ledger v4.1", "broker_ledger"),
        ("Mark-to-Market v4", "mark_to_market"),
        ("Portfolio State", "portfolio_state"),
        ("Performance", "performance"),
        ("Learning", "learning"),
        ("Strategy Registry", "strategy_registry"),
    ]

    rows = []

    for sequence, (name, key) in enumerate(chain, start=1):
        payload = inputs.get(key, {}) or {}

        rows.append({
            "sequence": sequence,
            "layer": name,
            "source_key": key,
            "success": payload.get("success"),
            "version": payload.get("version"),
            "summary": (
                payload.get("summary")
                or payload.get("text_summary")
                or ""
            ),
        })

    return rows


def portfolio_narrative(
    exposure: dict,
    learning_regime: str,
    confidence: dict,
    rebalance: dict,
) -> str:
    risky = number(exposure.get("risky_weight"))
    cash = number(exposure.get("cash_weight"))
    orders = rebalance.get("orders", []) or []

    if orders:
        action_text = (
            f"{len(orders)} rebalance order(s) are required "
            "to move the portfolio toward adaptive targets."
        )
    else:
        action_text = (
            "No rebalance is currently required because broker "
            "weights match adaptive targets."
        )

    return (
        f"The portfolio is {risky:.2%} invested with "
        f"{cash:.2%} held in cash. The learning regime is "
        f"{learning_regime}. Overall confidence is "
        f"{confidence.get('confidence_label')} at "
        f"{confidence.get('overall_confidence', 0.0):.3f}. "
        f"{action_text}"
    )


def asset_narrative(
    *,
    asset: str,
    ensemble_score: float,
    current_weight: float,
    target_weight: float,
    lifecycle_status: str,
) -> str:
    delta = target_weight - current_weight

    if abs(delta) < 0.0005:
        allocation_text = (
            "Current exposure already matches the target."
        )
    elif delta > 0:
        allocation_text = (
            f"Increase exposure by approximately {delta:.2%}."
        )
    else:
        allocation_text = (
            f"Reduce exposure by approximately {abs(delta):.2%}."
        )

    return (
        f"{asset} has an ensemble conviction score of "
        f"{ensemble_score:.3f} and registry status "
        f"{lifecycle_status}. {allocation_text}"
    )


def collect_assets(*frames: pd.DataFrame) -> set[str]:
    assets = set()

    for frame in frames:
        if (
            frame is None
            or frame.empty
            or "asset" not in frame.columns
        ):
            continue

        assets.update(
            str(value)
            for value in frame["asset"].dropna().tolist()
            if str(value).upper() != "CASH"
        )

    return assets


def find_row(
    frame: pd.DataFrame,
    asset: str,
) -> dict:
    if (
        frame is None
        or frame.empty
        or "asset" not in frame.columns
    ):
        return {}

    match = frame[
        frame["asset"].astype(str) == str(asset)
    ]

    if match.empty:
        return {}

    return match.iloc[-1].to_dict()


def number(value) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
