
"""Investment Intelligence v2.1 state reconciliation.

Builds one canonical read-only portfolio snapshot from authoritative
broker/MTM state and current Alpha Portfolio targets. Stale rebalance
artifacts are audited but never allowed to control explanations.
"""

from __future__ import annotations

from datetime import datetime, UTC
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv, safe_read_json


PATHS = {
    "portfolio_state": Path(
        "output/investment_portfolio_state/portfolio_state.json"
    ),
    "portfolio_holdings": Path(
        "output/investment_portfolio_state/portfolio_holdings.csv"
    ),
    "mtm_report": Path(
        "output/investment_mark_to_market/mark_to_market_report.json"
    ),
    "mtm_positions": Path(
        "output/investment_mark_to_market/positions.csv"
    ),
    "alpha_portfolio_report": Path(
        "output/investment_alpha/alpha_portfolio_report.json"
    ),
    "alpha_portfolio": Path(
        "output/investment_alpha/alpha_portfolio.csv"
    ),
    "adaptive_weighting_report": Path(
        "output/investment_adaptive_weighting/"
        "adaptive_weighting_report.json"
    ),
    "adaptive_weights": Path(
        "output/investment_adaptive_weighting/adaptive_weights.csv"
    ),
    "rebalance_report": Path(
        "output/investment_rebalance/rebalance_report.json"
    ),
    "rebalance_orders": Path(
        "output/investment_rebalance/rebalance_orders.csv"
    ),
    "broker_ledger_report": Path(
        "output/investment_broker_ledger/broker_ledger_report.json"
    ),
}


DEFAULT_TOLERANCE = 0.0005


def build_reconciled_snapshot(
    *,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    inputs = load_reconciliation_inputs()

    current = build_current_weights(inputs)
    targets = build_target_weights(inputs)
    adaptive = build_adaptive_weights(inputs)
    rebalance_orders = normalize_rebalance_orders(
        inputs["rebalance_orders"]
    )

    assets = sorted(
        {
            *current.keys(),
            *targets.keys(),
            *adaptive.keys(),
            *set(rebalance_orders.get("asset", pd.Series(dtype=str)).astype(str)),
        }
        - {"", "CASH", "nan", "None"}
    )

    rows = []
    issues = []

    for asset in assets:
        current_weight = current.get(asset, 0.0)
        target_weight = targets.get(
            asset,
            adaptive.get(asset, 0.0),
        )
        adaptive_weight = adaptive.get(asset)

        order_rows = (
            rebalance_orders[
                rebalance_orders["asset"].astype(str) == asset
            ]
            if (
                not rebalance_orders.empty
                and "asset" in rebalance_orders.columns
            )
            else pd.DataFrame()
        )

        rebalance_target = None
        rebalance_delta = None
        rebalance_action = None

        if not order_rows.empty:
            latest_order = order_rows.iloc[-1]
            rebalance_target = optional_number(
                latest_order.get("target_weight")
            )
            rebalance_delta = optional_number(
                latest_order.get(
                    "signed_delta",
                    latest_order.get("weight_delta"),
                )
            )
            rebalance_action = latest_order.get("action")

        canonical_delta = round(
            target_weight - current_weight,
            6,
        )

        adaptive_mismatch = (
            adaptive_weight is not None
            and abs(target_weight - adaptive_weight) > tolerance
        )

        rebalance_target_mismatch = (
            rebalance_target is not None
            and abs(target_weight - rebalance_target) > tolerance
        )

        rebalance_delta_mismatch = (
            rebalance_delta is not None
            and abs(canonical_delta - rebalance_delta) > tolerance
        )

        if adaptive_mismatch:
            issues.append({
                "asset": asset,
                "issue": "TARGET_ADAPTIVE_MISMATCH",
                "canonical_target": target_weight,
                "adaptive_target": adaptive_weight,
                "difference": round(
                    target_weight - adaptive_weight,
                    6,
                ),
            })

        if rebalance_target_mismatch:
            issues.append({
                "asset": asset,
                "issue": "STALE_REBALANCE_TARGET",
                "canonical_target": target_weight,
                "rebalance_target": rebalance_target,
                "difference": round(
                    target_weight - rebalance_target,
                    6,
                ),
            })

        if rebalance_delta_mismatch:
            issues.append({
                "asset": asset,
                "issue": "STALE_REBALANCE_DELTA",
                "canonical_delta": canonical_delta,
                "rebalance_delta": rebalance_delta,
                "difference": round(
                    canonical_delta - rebalance_delta,
                    6,
                ),
            })

        rows.append({
            "asset": asset,
            "current_weight": round(current_weight, 6),
            "canonical_target_weight": round(target_weight, 6),
            "adaptive_weight": (
                round(adaptive_weight, 6)
                if adaptive_weight is not None
                else None
            ),
            "rebalance_target_weight": (
                round(rebalance_target, 6)
                if rebalance_target is not None
                else None
            ),
            "canonical_delta": canonical_delta,
            "rebalance_delta": (
                round(rebalance_delta, 6)
                if rebalance_delta is not None
                else None
            ),
            "rebalance_action": rebalance_action,
            "target_matches_adaptive": not adaptive_mismatch,
            "rebalance_target_current": not rebalance_target_mismatch,
            "rebalance_delta_current": not rebalance_delta_mismatch,
            "canonical_current_source": current_source(inputs, asset),
            "canonical_target_source": "alpha_portfolio_v3",
        })

    canonical_trades = build_canonical_trades(
        rows,
        tolerance=tolerance,
    )

    cash_current = current.get("CASH", current_cash_weight(inputs))
    cash_target = targets.get("CASH", adaptive.get("CASH", 0.0))

    source_manifest = build_source_manifest()
    fingerprint = build_fingerprint(source_manifest)

    stale_rebalance = any(
        issue["issue"].startswith("STALE_REBALANCE")
        for issue in issues
    )

    state_consistent = len(issues) == 0

    return {
        "version": "investment_intelligence_reconciliation_v2_1",
        "generated_at": datetime.now(UTC).isoformat(),
        "snapshot_fingerprint": fingerprint,
        "state_consistent": state_consistent,
        "stale_rebalance_detected": stale_rebalance,
        "tolerance": tolerance,
        "summary": (
            f"Reconciled {len(rows)} risky asset(s); "
            f"generated {len(canonical_trades)} canonical trade action(s); "
            f"detected {len(issues)} source inconsistency/inconsistencies."
        ),
        "portfolio": {
            "current_risky_weight": round(
                sum(
                    row["current_weight"]
                    for row in rows
                ),
                6,
            ),
            "target_risky_weight": round(
                sum(
                    row["canonical_target_weight"]
                    for row in rows
                ),
                6,
            ),
            "current_cash_weight": round(cash_current, 6),
            "target_cash_weight": round(cash_target, 6),
        },
        "asset_reconciliation": rows,
        "canonical_trades": canonical_trades,
        "issues": issues,
        "source_manifest": source_manifest,
        "authority": {
            "current_positions": (
                "portfolio_state_v4_then_mtm_v4"
            ),
            "target_portfolio": "alpha_portfolio_v3",
            "adaptive_cross_check": "adaptive_weighting_v4",
            "rebalance_role": "audit_only",
            "execution_influence": False,
        },
    }


def load_reconciliation_inputs() -> dict[str, Any]:
    return {
        "portfolio_state": safe_read_json(
            PATHS["portfolio_state"]
        ),
        "portfolio_holdings": safe_read_csv(
            PATHS["portfolio_holdings"]
        ),
        "mtm_report": safe_read_json(
            PATHS["mtm_report"]
        ),
        "mtm_positions": safe_read_csv(
            PATHS["mtm_positions"]
        ),
        "alpha_portfolio_report": safe_read_json(
            PATHS["alpha_portfolio_report"]
        ),
        "alpha_portfolio": safe_read_csv(
            PATHS["alpha_portfolio"]
        ),
        "adaptive_weighting_report": safe_read_json(
            PATHS["adaptive_weighting_report"]
        ),
        "adaptive_weights": safe_read_csv(
            PATHS["adaptive_weights"]
        ),
        "rebalance_report": safe_read_json(
            PATHS["rebalance_report"]
        ),
        "rebalance_orders": safe_read_csv(
            PATHS["rebalance_orders"]
        ),
        "broker_ledger_report": safe_read_json(
            PATHS["broker_ledger_report"]
        ),
    }


def build_current_weights(inputs: dict) -> dict[str, float]:
    holdings = inputs["portfolio_holdings"]

    result = weights_from_frame(
        holdings,
        candidates=[
            "portfolio_weight",
            "paper_weight",
            "weight",
            "net_weight",
        ],
    )

    if risky_asset_count(result) > 0:
        return result

    return weights_from_frame(
        inputs["mtm_positions"],
        candidates=[
            "portfolio_weight",
            "weight",
            "net_weight",
        ],
    )


def build_target_weights(inputs: dict) -> dict[str, float]:
    return weights_from_frame(
        inputs["alpha_portfolio"],
        candidates=[
            "target_weight",
            "target_exposure",
            "allocation",
            "paper_weight",
            "weight",
        ],
    )


def build_adaptive_weights(inputs: dict) -> dict[str, float]:
    return weights_from_frame(
        inputs["adaptive_weights"],
        candidates=[
            "adaptive_weight",
            "target_weight",
            "weight",
        ],
    )


def weights_from_frame(
    frame: pd.DataFrame,
    *,
    candidates: list[str],
) -> dict[str, float]:
    if (
        frame is None
        or frame.empty
        or "asset" not in frame.columns
    ):
        return {}

    weight_column = next(
        (
            column
            for column in candidates
            if column in frame.columns
        ),
        None,
    )

    if weight_column is None:
        return {}

    result = {}

    for _, row in frame.iterrows():
        asset = str(row.get("asset", "")).strip()

        if not asset:
            continue

        result[asset] = number(
            row.get(weight_column)
        )

    return result


def normalize_rebalance_orders(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=[
                "asset",
                "action",
                "current_weight",
                "target_weight",
                "signed_delta",
                "weight_delta",
                "priority",
                "reason",
            ]
        )

    result = frame.copy()

    if "asset" not in result.columns:
        result["asset"] = ""

    for column in [
        "current_weight",
        "target_weight",
        "signed_delta",
        "weight_delta",
        "priority",
    ]:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result.reset_index(drop=True)


def build_canonical_trades(
    rows: list[dict],
    *,
    tolerance: float,
) -> list[dict]:
    trades = []

    actionable = [
        row
        for row in rows
        if abs(row["canonical_delta"]) > tolerance
    ]

    actionable.sort(
        key=lambda row: abs(row["canonical_delta"]),
        reverse=True,
    )

    for priority, row in enumerate(actionable, start=1):
        delta = row["canonical_delta"]
        action = "BUY" if delta > 0 else "SELL"

        trades.append({
            "asset": row["asset"],
            "action": action,
            "current_weight": row["current_weight"],
            "target_weight": row["canonical_target_weight"],
            "signed_delta": delta,
            "weight_delta": round(abs(delta), 6),
            "priority": priority,
            "reason": (
                "Reconciled current broker/MTM state against the "
                "latest Alpha Portfolio target."
            ),
            "source": "investment_intelligence_v2_1_reconciliation",
            "authoritative": True,
            "execution_instruction": False,
            "explanation": (
                f"{action} {row['asset']} because the reconciled "
                f"current weight is {row['current_weight']:.4%} "
                f"and the current canonical target is "
                f"{row['canonical_target_weight']:.4%}. "
                f"Required change: {delta:.4%}."
            ),
        })

    return trades


def current_cash_weight(inputs: dict) -> float:
    portfolio = inputs["portfolio_state"] or {}
    state = portfolio.get("state", {}) or {}
    exposure = state.get("exposure", {}) or {}

    if not exposure:
        exposure = portfolio.get("exposure", {}) or {}

    return number(exposure.get("cash_weight"))


def current_source(inputs: dict, asset: str) -> str:
    holdings = inputs["portfolio_holdings"]

    if (
        holdings is not None
        and not holdings.empty
        and "asset" in holdings.columns
        and asset in holdings["asset"].astype(str).tolist()
    ):
        return "portfolio_state_v4"

    return "mark_to_market_v4"


def risky_asset_count(weights: dict[str, float]) -> int:
    return sum(
        1
        for asset in weights
        if asset.upper() != "CASH"
    )


def build_source_manifest() -> list[dict]:
    rows = []

    for name, path in PATHS.items():
        exists = path.exists()
        stat = path.stat() if exists else None

        rows.append({
            "source": name,
            "path": str(path),
            "exists": exists,
            "size_bytes": stat.st_size if stat else 0,
            "modified_at": (
                datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=UTC,
                ).isoformat()
                if stat
                else None
            ),
        })

    return rows


def build_fingerprint(
    manifest: list[dict],
) -> str:
    payload = json.dumps(
        manifest,
        sort_keys=True,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def number(value) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def optional_number(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
