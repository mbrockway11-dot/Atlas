"""Append-only historical ledger for Atlas shadow performance observations."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

SHADOW_PERFORMANCE_LEDGER_JSONL = (
    OUTPUT_DIR
    / "shadow_performance_ledger.jsonl"
)

SHADOW_PERFORMANCE_SUMMARY_JSON = (
    OUTPUT_DIR
    / "shadow_performance_summary.json"
)

SHADOW_EQUITY_CURVE_JSON = (
    OUTPUT_DIR
    / "shadow_equity_curve.json"
)

SHADOW_DRAWDOWN_CURVE_JSON = (
    OUTPUT_DIR
    / "shadow_drawdown_curve.json"
)

SHADOW_ROLLING_METRICS_JSON = (
    OUTPUT_DIR
    / "shadow_rolling_metrics.json"
)

PERFORMANCE_LEDGER_VERSION = "1.0.0"


def build_performance_observation(
    *,
    analytics_report: Mapping[
        str,
        Any,
    ],
    pipeline_report: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:
    """Build one canonical ledger observation from G.12 and G.13 outputs."""
    analytics = dict(
        analytics_report
    )

    pipeline = dict(
        pipeline_report
    )

    if not analytics.get(
        "success",
        False,
    ):
        raise ValueError(
            "EXECUTION_ANALYTICS_NOT_SUCCESSFUL"
        )

    if not pipeline.get(
        "success",
        False,
    ):
        raise ValueError(
            "SHADOW_PIPELINE_NOT_SUCCESSFUL"
        )

    analytics_id = required_text(
        analytics,
        "analytics_id",
    )

    pipeline_id = required_text(
        pipeline,
        "pipeline_id",
    )

    analytics_cycle_id = required_text(
        analytics,
        "cycle_id",
    )

    pipeline_cycle_id = required_text(
        pipeline,
        "cycle_id",
    )

    if (
        analytics_cycle_id
        != pipeline_cycle_id
    ):
        raise ValueError(
            "ANALYTICS_PIPELINE_CYCLE_MISMATCH:"
            + analytics_cycle_id
            + "!="
            + pipeline_cycle_id
        )

    analytics_plan_id = required_text(
        analytics,
        "plan_id",
    )

    pipeline_plan_id = required_text(
        pipeline,
        "plan_id",
    )

    if (
        analytics_plan_id
        != pipeline_plan_id
    ):
        raise ValueError(
            "ANALYTICS_PIPELINE_PLAN_MISMATCH:"
            + analytics_plan_id
            + "!="
            + pipeline_plan_id
        )

    reported_pipeline_id = str(
        analytics.get(
            "pipeline_id",
            "",
        )
    ).strip()

    if (
        reported_pipeline_id
        and reported_pipeline_id
        != pipeline_id
    ):
        raise ValueError(
            "ANALYTICS_PIPELINE_ID_MISMATCH:"
            + reported_pipeline_id
            + "!="
            + pipeline_id
        )

    analytics_contract = dict(
        analytics.get(
            "contract",
            {},
        )
        or {}
    )

    pipeline_contract = dict(
        pipeline.get(
            "contract",
            {},
        )
        or {}
    )

    validate_safety_contracts(
        analytics_contract=(
            analytics_contract
        ),
        pipeline_contract=(
            pipeline_contract
        ),
    )

    summary = dict(
        analytics.get(
            "summary",
            {},
        )
        or {}
    )

    utilization = dict(
        analytics.get(
            "utilization",
            {},
        )
        or {}
    )

    performance = dict(
        pipeline.get(
            "performance",
            {},
        )
        or {}
    )

    starting_equity = finite(
        performance.get(
            "starting_net_liquidation_value",
            utilization.get(
                "starting_equity",
                0.0,
            ),
        ),
        name="starting_equity",
    )

    ending_equity = finite(
        performance.get(
            "ending_net_liquidation_value",
            utilization.get(
                "ending_equity",
                0.0,
            ),
        ),
        name="ending_equity",
    )

    if starting_equity <= 0:
        raise ValueError(
            "STARTING_EQUITY_MUST_BE_POSITIVE"
        )

    cycle_pnl = finite(
        performance.get(
            "total_pnl",
            ending_equity
            - starting_equity,
        ),
        name="cycle_pnl",
    )

    cycle_return = finite(
        performance.get(
            "return_pct",
            cycle_pnl
            / starting_equity,
        ),
        name="cycle_return",
    )

    fee_cost = finite(
        summary.get(
            "fee_cost",
            0.0,
        ),
        name="fee_cost",
    )

    slippage_cost = finite(
        summary.get(
            "slippage_cost",
            0.0,
        ),
        name="slippage_cost",
    )

    total_execution_cost = finite(
        summary.get(
            "total_execution_cost",
            fee_cost
            + slippage_cost,
        ),
        name="total_execution_cost",
    )

    if not close(
        total_execution_cost,
        fee_cost
        + slippage_cost,
    ):
        raise ValueError(
            "EXECUTION_COST_DECOMPOSITION_MISMATCH"
        )

    generated_at = str(
        analytics.get(
            "generated_at",
            pipeline.get(
                "completed_at",
                utc_now(),
            ),
        )
    )

    observation = {
        "version": (
            PERFORMANCE_LEDGER_VERSION
        ),
        "analytics_id": analytics_id,
        "pipeline_id": pipeline_id,
        "cycle_id": (
            analytics_cycle_id
        ),
        "plan_id": (
            analytics_plan_id
        ),
        "snapshot_id": str(
            pipeline.get(
                "snapshot_id",
                "",
            )
        ),
        "observed_at": generated_at,
        "pipeline_started_at": str(
            pipeline.get(
                "started_at",
                "",
            )
        ),
        "pipeline_completed_at": str(
            pipeline.get(
                "completed_at",
                "",
            )
        ),
        "starting_equity": (
            starting_equity
        ),
        "ending_equity": (
            ending_equity
        ),
        "cycle_pnl": cycle_pnl,
        "cycle_return": (
            cycle_return
        ),
        "realized_pnl_change": finite(
            performance.get(
                "realized_pnl_change",
                0.0,
            ),
            name=(
                "realized_pnl_change"
            ),
        ),
        "fee_cost": fee_cost,
        "slippage_cost": (
            slippage_cost
        ),
        "total_execution_cost": (
            total_execution_cost
        ),
        "execution_cost_bps": finite(
            utilization.get(
                "execution_cost_bps_of_starting_equity",
                (
                    total_execution_cost
                    / starting_equity
                    * 10_000.0
                ),
            ),
            name="execution_cost_bps",
        ),
        "gross_fill_notional": finite(
            summary.get(
                "gross_fill_notional",
                0.0,
            ),
            name=(
                "gross_fill_notional"
            ),
        ),
        "turnover_ratio": finite(
            utilization.get(
                "turnover_ratio",
                0.0,
            ),
            name="turnover_ratio",
        ),
        "ending_cash_weight": finite(
            utilization.get(
                "ending_cash_weight",
                0.0,
            ),
            name=(
                "ending_cash_weight"
            ),
        ),
        "ending_gross_exposure_ratio": finite(
            utilization.get(
                "ending_gross_exposure_ratio",
                0.0,
            ),
            name=(
                "ending_gross_exposure_ratio"
            ),
        ),
        "order_count": integer(
            summary.get(
                "order_count",
                0,
            ),
            name="order_count",
        ),
        "filled_order_count": integer(
            summary.get(
                "filled_order_count",
                0,
            ),
            name=(
                "filled_order_count"
            ),
        ),
        "full_fill_rate": finite(
            summary.get(
                "full_fill_rate",
                0.0,
            ),
            name="full_fill_rate",
        ),
        "rejection_rate": finite(
            summary.get(
                "rejection_rate",
                0.0,
            ),
            name="rejection_rate",
        ),
        "reconciliation_success_rate": finite(
            summary.get(
                "reconciliation_success_rate",
                0.0,
            ),
            name=(
                "reconciliation_success_rate"
            ),
        ),
        "weighted_slippage_bps": finite(
            summary.get(
                "weighted_slippage_bps",
                0.0,
            ),
            name=(
                "weighted_slippage_bps"
            ),
        ),
        "weighted_implementation_shortfall_bps": finite(
            summary.get(
                "weighted_implementation_shortfall_bps",
                0.0,
            ),
            name=(
                "weighted_implementation_shortfall_bps"
            ),
        ),
        "average_time_to_completion_ms": finite(
            summary.get(
                "average_time_to_completion_ms",
                0.0,
            ),
            name=(
                "average_time_to_completion_ms"
            ),
        ),
        "paper_only": True,
        "live_execution": False,
        "credentials_used": False,
    }

    observation["observation_id"] = (
        build_observation_id(
            observation
        )
    )

    return observation


def append_performance_observation(
    observation: Mapping[
        str,
        Any,
    ],
    *,
    path: Path = (
        SHADOW_PERFORMANCE_LEDGER_JSONL
    ),
) -> dict[str, Any]:
    """Append one unique observation to the tamper-evident ledger."""
    validate_observation(
        observation
    )

    records = read_performance_ledger(
        path
    )

    analytics_id = str(
        observation["analytics_id"]
    )

    cycle_id = str(
        observation["cycle_id"]
    )

    for record in records:
        if str(
            record.get(
                "analytics_id",
                "",
            )
        ) == analytics_id:
            return {
                "appended": False,
                "duplicate": True,
                "duplicate_field": (
                    "analytics_id"
                ),
                "record": record,
                "record_count": len(
                    records
                ),
            }

        if str(
            record.get(
                "cycle_id",
                "",
            )
        ) == cycle_id:
            return {
                "appended": False,
                "duplicate": True,
                "duplicate_field": (
                    "cycle_id"
                ),
                "record": record,
                "record_count": len(
                    records
                ),
            }

    previous_hash = (
        str(
            records[-1].get(
                "record_hash",
                "",
            )
        )
        if records
        else ""
    )

    record = {
        **dict(observation),
        "ledger_index": (
            len(records)
            + 1
        ),
        "previous_record_hash": (
            previous_hash
        ),
        "recorded_at": utc_now(),
    }

    record["record_hash"] = (
        build_record_hash(
            record
        )
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                record,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            + "\n"
        )

    return {
        "appended": True,
        "duplicate": False,
        "duplicate_field": "",
        "record": record,
        "record_count": (
            len(records)
            + 1
        ),
    }


def rebuild_performance_outputs(
    *,
    ledger_path: Path = (
        SHADOW_PERFORMANCE_LEDGER_JSONL
    ),
    summary_path: Path = (
        SHADOW_PERFORMANCE_SUMMARY_JSON
    ),
    equity_path: Path = (
        SHADOW_EQUITY_CURVE_JSON
    ),
    drawdown_path: Path = (
        SHADOW_DRAWDOWN_CURVE_JSON
    ),
    rolling_path: Path = (
        SHADOW_ROLLING_METRICS_JSON
    ),
    rolling_window: int = 5,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Rebuild all historical performance views from the ledger."""
    validation = (
        validate_performance_ledger(
            path=ledger_path
        )
    )

    records = read_performance_ledger(
        ledger_path
    )

    if not validation["valid"]:
        return {
            "success": False,
            "validation": validation,
            "summary": {},
            "equity_curve": [],
            "drawdown_curve": [],
            "rolling_metrics": [],
        }

    curves = build_equity_and_drawdown_curves(
        records
    )

    summary = summarize_performance(
        records,
        equity_curve=(
            curves["equity_curve"]
        ),
        drawdown_curve=(
            curves["drawdown_curve"]
        ),
    )

    rolling = build_rolling_metrics(
        records,
        window=rolling_window,
    )

    report = {
        "success": True,
        "version": (
            PERFORMANCE_LEDGER_VERSION
        ),
        "generated_at": utc_now(),
        "validation": validation,
        "summary": summary,
        "equity_curve": (
            curves["equity_curve"]
        ),
        "drawdown_curve": (
            curves["drawdown_curve"]
        ),
        "rolling_metrics": rolling,
        "contract": {
            "append_only_source": True,
            "hash_chained": True,
            "read_only_views": True,
            "paper_only": True,
            "mutates_account": False,
            "submits_orders": False,
            "live_execution": False,
            "credentials_used": False,
        },
    }

    if write_outputs:
        write_json_atomic(
            summary_path,
            {
                "version": (
                    PERFORMANCE_LEDGER_VERSION
                ),
                "generated_at": (
                    report["generated_at"]
                ),
                "validation": (
                    validation
                ),
                "summary": summary,
                "contract": (
                    report["contract"]
                ),
            },
        )

        write_json_atomic(
            equity_path,
            {
                "version": (
                    PERFORMANCE_LEDGER_VERSION
                ),
                "generated_at": (
                    report["generated_at"]
                ),
                "rows": (
                    curves[
                        "equity_curve"
                    ]
                ),
            },
        )

        write_json_atomic(
            drawdown_path,
            {
                "version": (
                    PERFORMANCE_LEDGER_VERSION
                ),
                "generated_at": (
                    report["generated_at"]
                ),
                "rows": (
                    curves[
                        "drawdown_curve"
                    ]
                ),
            },
        )

        write_json_atomic(
            rolling_path,
            {
                "version": (
                    PERFORMANCE_LEDGER_VERSION
                ),
                "generated_at": (
                    report["generated_at"]
                ),
                "window": int(
                    rolling_window
                ),
                "rows": rolling,
            },
        )

    return report


def build_equity_and_drawdown_curves(
    records: Sequence[
        Mapping[str, Any]
    ],
) -> dict[str, list[dict[str, Any]]]:
    """Create linked equity and drawdown curves in ledger order."""
    equity_rows: list[
        dict[str, Any]
    ] = []

    drawdown_rows: list[
        dict[str, Any]
    ] = []

    if not records:
        return {
            "equity_curve": (
                equity_rows
            ),
            "drawdown_curve": (
                drawdown_rows
            ),
        }

    initial_equity = finite(
        records[0].get(
            "starting_equity",
            0.0,
        ),
        name="initial_equity",
    )

    linked_equity = (
        initial_equity
    )

    peak_equity = (
        initial_equity
    )

    cumulative_pnl = 0.0

    for record in records:
        cycle_return = finite(
            record.get(
                "cycle_return",
                0.0,
            ),
            name="cycle_return",
        )

        cycle_pnl = finite(
            record.get(
                "cycle_pnl",
                0.0,
            ),
            name="cycle_pnl",
        )

        linked_equity *= (
            1.0
            + cycle_return
        )

        cumulative_pnl += (
            cycle_pnl
        )

        peak_equity = max(
            peak_equity,
            linked_equity,
        )

        drawdown_value = (
            linked_equity
            - peak_equity
        )

        drawdown_pct = (
            drawdown_value
            / peak_equity
            if peak_equity
            else 0.0
        )

        common = {
            "ledger_index": (
                record.get(
                    "ledger_index"
                )
            ),
            "observation_id": (
                record.get(
                    "observation_id",
                    "",
                )
            ),
            "analytics_id": (
                record.get(
                    "analytics_id",
                    "",
                )
            ),
            "pipeline_id": (
                record.get(
                    "pipeline_id",
                    "",
                )
            ),
            "cycle_id": (
                record.get(
                    "cycle_id",
                    "",
                )
            ),
            "observed_at": (
                record.get(
                    "observed_at",
                    "",
                )
            ),
        }

        equity_rows.append({
            **common,
            "cycle_return": (
                cycle_return
            ),
            "cycle_pnl": (
                cycle_pnl
            ),
            "linked_equity": (
                linked_equity
            ),
            "cumulative_pnl": (
                cumulative_pnl
            ),
            "peak_equity": (
                peak_equity
            ),
        })

        drawdown_rows.append({
            **common,
            "linked_equity": (
                linked_equity
            ),
            "peak_equity": (
                peak_equity
            ),
            "drawdown_value": (
                drawdown_value
            ),
            "drawdown_pct": (
                drawdown_pct
            ),
        })

    return {
        "equity_curve": equity_rows,
        "drawdown_curve": (
            drawdown_rows
        ),
    }


def summarize_performance(
    records: Sequence[
        Mapping[str, Any]
    ],
    *,
    equity_curve: Sequence[
        Mapping[str, Any]
    ],
    drawdown_curve: Sequence[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:
    """Summarize historical shadow performance without annualization."""
    returns = [
        finite(
            record.get(
                "cycle_return",
                0.0,
            ),
            name="cycle_return",
        )
        for record in records
    ]

    pnls = [
        finite(
            record.get(
                "cycle_pnl",
                0.0,
            ),
            name="cycle_pnl",
        )
        for record in records
    ]

    fees = sum(
        finite(
            record.get(
                "fee_cost",
                0.0,
            ),
            name="fee_cost",
        )
        for record in records
    )

    slippage = sum(
        finite(
            record.get(
                "slippage_cost",
                0.0,
            ),
            name="slippage_cost",
        )
        for record in records
    )

    total_cost = sum(
        finite(
            record.get(
                "total_execution_cost",
                0.0,
            ),
            name=(
                "total_execution_cost"
            ),
        )
        for record in records
    )

    positive_pnls = [
        value
        for value in pnls
        if value > 0
    ]

    negative_pnls = [
        value
        for value in pnls
        if value < 0
    ]

    gross_profit = sum(
        positive_pnls
    )

    gross_loss = abs(
        sum(
            negative_pnls
        )
    )

    linked_return = (
        product(
            1.0 + value
            for value in returns
        )
        - 1.0
        if returns
        else 0.0
    )

    maximum_drawdown_pct = min(
        (
            finite(
                row.get(
                    "drawdown_pct",
                    0.0,
                ),
                name="drawdown_pct",
            )
            for row
            in drawdown_curve
        ),
        default=0.0,
    )

    maximum_drawdown_value = min(
        (
            finite(
                row.get(
                    "drawdown_value",
                    0.0,
                ),
                name=(
                    "drawdown_value"
                ),
            )
            for row
            in drawdown_curve
        ),
        default=0.0,
    )

    starting_equity = (
        finite(
            records[0].get(
                "starting_equity",
                0.0,
            ),
            name="starting_equity",
        )
        if records
        else 0.0
    )

    linked_ending_equity = (
        finite(
            equity_curve[-1].get(
                "linked_equity",
                0.0,
            ),
            name=(
                "linked_ending_equity"
            ),
        )
        if equity_curve
        else starting_equity
    )

    average_return = (
        statistics.fmean(
            returns
        )
        if returns
        else 0.0
    )

    return_volatility = (
        statistics.pstdev(
            returns
        )
        if len(returns) > 1
        else 0.0
    )

    average_cost_bps = (
        statistics.fmean([
            finite(
                record.get(
                    "execution_cost_bps",
                    0.0,
                ),
                name=(
                    "execution_cost_bps"
                ),
            )
            for record in records
        ])
        if records
        else 0.0
    )

    average_fill_rate = (
        statistics.fmean([
            finite(
                record.get(
                    "full_fill_rate",
                    0.0,
                ),
                name="full_fill_rate",
            )
            for record in records
        ])
        if records
        else 0.0
    )

    average_reconciliation_rate = (
        statistics.fmean([
            finite(
                record.get(
                    "reconciliation_success_rate",
                    0.0,
                ),
                name=(
                    "reconciliation_success_rate"
                ),
            )
            for record in records
        ])
        if records
        else 0.0
    )

    return {
        "observation_count": len(
            records
        ),
        "winning_cycles": len(
            positive_pnls
        ),
        "losing_cycles": len(
            negative_pnls
        ),
        "flat_cycles": sum(
            1
            for value in pnls
            if value == 0
        ),
        "win_rate": ratio(
            len(
                positive_pnls
            ),
            len(records),
        ),
        "starting_equity": (
            starting_equity
        ),
        "linked_ending_equity": (
            linked_ending_equity
        ),
        "cumulative_pnl": sum(
            pnls
        ),
        "linked_return": (
            linked_return
        ),
        "average_cycle_pnl": (
            statistics.fmean(
                pnls
            )
            if pnls
            else 0.0
        ),
        "average_cycle_return": (
            average_return
        ),
        "cycle_return_volatility": (
            return_volatility
        ),
        "best_cycle_return": (
            max(
                returns
            )
            if returns
            else 0.0
        ),
        "worst_cycle_return": (
            min(
                returns
            )
            if returns
            else 0.0
        ),
        "maximum_drawdown_value": (
            maximum_drawdown_value
        ),
        "maximum_drawdown_pct": (
            maximum_drawdown_pct
        ),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": (
            gross_profit
            / gross_loss
            if gross_loss > 0
            else (
                None
                if gross_profit == 0
                else float("inf")
            )
        ),
        "total_fees": fees,
        "total_slippage_cost": (
            slippage
        ),
        "total_execution_cost": (
            total_cost
        ),
        "average_execution_cost_bps": (
            average_cost_bps
        ),
        "average_full_fill_rate": (
            average_fill_rate
        ),
        "average_reconciliation_success_rate": (
            average_reconciliation_rate
        ),
        "total_orders": sum(
            integer(
                record.get(
                    "order_count",
                    0,
                ),
                name="order_count",
            )
            for record in records
        ),
    }


def build_rolling_metrics(
    records: Sequence[
        Mapping[str, Any]
    ],
    *,
    window: int = 5,
) -> list[dict[str, Any]]:
    """Compute nonannualized rolling metrics over ledger observations."""
    effective_window = max(
        1,
        int(window),
    )

    rows: list[
        dict[str, Any]
    ] = []

    for end_index in range(
        len(records)
    ):
        start_index = max(
            0,
            end_index
            - effective_window
            + 1,
        )

        subset = records[
            start_index:
            end_index + 1
        ]

        returns = [
            finite(
                record.get(
                    "cycle_return",
                    0.0,
                ),
                name="cycle_return",
            )
            for record in subset
        ]

        pnls = [
            finite(
                record.get(
                    "cycle_pnl",
                    0.0,
                ),
                name="cycle_pnl",
            )
            for record in subset
        ]

        total_cost = sum(
            finite(
                record.get(
                    "total_execution_cost",
                    0.0,
                ),
                name=(
                    "total_execution_cost"
                ),
            )
            for record in subset
        )

        rows.append({
            "ledger_index": (
                records[end_index].get(
                    "ledger_index"
                )
            ),
            "observation_id": (
                records[end_index].get(
                    "observation_id",
                    "",
                )
            ),
            "observed_at": (
                records[end_index].get(
                    "observed_at",
                    "",
                )
            ),
            "window": (
                effective_window
            ),
            "observations_in_window": (
                len(subset)
            ),
            "rolling_pnl": sum(
                pnls
            ),
            "rolling_linked_return": (
                product(
                    1.0 + value
                    for value in returns
                )
                - 1.0
            ),
            "rolling_average_return": (
                statistics.fmean(
                    returns
                )
            ),
            "rolling_return_volatility": (
                statistics.pstdev(
                    returns
                )
                if len(
                    returns
                )
                > 1
                else 0.0
            ),
            "rolling_win_rate": ratio(
                sum(
                    1
                    for value in pnls
                    if value > 0
                ),
                len(subset),
            ),
            "rolling_execution_cost": (
                total_cost
            ),
            "rolling_average_execution_cost_bps": (
                statistics.fmean([
                    finite(
                        record.get(
                            "execution_cost_bps",
                            0.0,
                        ),
                        name=(
                            "execution_cost_bps"
                        ),
                    )
                    for record in subset
                ])
            ),
        })

    return rows


def validate_performance_ledger(
    *,
    path: Path = (
        SHADOW_PERFORMANCE_LEDGER_JSONL
    ),
) -> dict[str, Any]:
    """Validate indexes, hashes, uniqueness, and safety fields."""
    records = read_performance_ledger(
        path
    )

    errors: list[str] = []
    warnings: list[str] = []

    previous_hash = ""
    analytics_ids: set[str] = set()
    cycle_ids: set[str] = set()
    observation_ids: set[str] = set()

    for expected_index, record in enumerate(
        records,
        start=1,
    ):
        actual_index = integer(
            record.get(
                "ledger_index",
                0,
            ),
            name="ledger_index",
        )

        if actual_index != expected_index:
            errors.append(
                "LEDGER_INDEX_MISMATCH:"
                + str(expected_index)
            )

        if str(
            record.get(
                "previous_record_hash",
                "",
            )
        ) != previous_hash:
            errors.append(
                "PREVIOUS_HASH_MISMATCH:"
                + str(expected_index)
            )

        expected_hash = (
            build_record_hash(
                record
            )
        )

        stored_hash = str(
            record.get(
                "record_hash",
                "",
            )
        )

        if expected_hash != stored_hash:
            errors.append(
                "RECORD_HASH_MISMATCH:"
                + str(expected_index)
            )

        previous_hash = (
            stored_hash
        )

        analytics_id = str(
            record.get(
                "analytics_id",
                "",
            )
        )

        cycle_id = str(
            record.get(
                "cycle_id",
                "",
            )
        )

        observation_id = str(
            record.get(
                "observation_id",
                "",
            )
        )

        if analytics_id in analytics_ids:
            errors.append(
                "DUPLICATE_ANALYTICS_ID:"
                + analytics_id
            )

        if cycle_id in cycle_ids:
            errors.append(
                "DUPLICATE_CYCLE_ID:"
                + cycle_id
            )

        if observation_id in (
            observation_ids
        ):
            errors.append(
                "DUPLICATE_OBSERVATION_ID:"
                + observation_id
            )

        analytics_ids.add(
            analytics_id
        )

        cycle_ids.add(
            cycle_id
        )

        observation_ids.add(
            observation_id
        )

        if not bool(
            record.get(
                "paper_only",
                False,
            )
        ):
            errors.append(
                "PAPER_ONLY_BOUNDARY_INVALID:"
                + str(expected_index)
            )

        if bool(
            record.get(
                "live_execution",
                False,
            )
        ):
            errors.append(
                "LIVE_EXECUTION_BOUNDARY_INVALID:"
                + str(expected_index)
            )

        if bool(
            record.get(
                "credentials_used",
                False,
            )
        ):
            errors.append(
                "CREDENTIAL_BOUNDARY_INVALID:"
                + str(expected_index)
            )

        if finite(
            record.get(
                "reconciliation_success_rate",
                0.0,
            ),
            name=(
                "reconciliation_success_rate"
            ),
        ) < 1.0:
            warnings.append(
                "RECONCILIATION_RATE_BELOW_ONE:"
                + str(expected_index)
            )

    return {
        "valid": not errors,
        "record_count": len(
            records
        ),
        "errors": errors,
        "warnings": warnings,
        "latest_record_hash": (
            previous_hash
        ),
    }


def read_performance_ledger(
    path: Path = (
        SHADOW_PERFORMANCE_LEDGER_JSONL
    ),
) -> list[dict[str, Any]]:
    """Read valid JSON objects from the historical ledger."""
    if not path.exists():
        return []

    records: list[
        dict[str, Any]
    ] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line_number, line in enumerate(
            handle,
            start=1,
        ):
            text = line.strip()

            if not text:
                continue

            try:
                payload = json.loads(
                    text
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    "INVALID_LEDGER_JSON:"
                    + str(line_number)
                ) from error

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "LEDGER_RECORD_NOT_OBJECT:"
                    + str(line_number)
                )

            records.append(
                payload
            )

    return records


def validate_observation(
    observation: Mapping[
        str,
        Any,
    ],
) -> None:
    required = (
        "observation_id",
        "analytics_id",
        "pipeline_id",
        "cycle_id",
        "plan_id",
        "starting_equity",
        "ending_equity",
        "cycle_pnl",
        "cycle_return",
    )

    for key in required:
        if key not in observation:
            raise ValueError(
                "OBSERVATION_FIELD_MISSING:"
                + key
            )

    if not bool(
        observation.get(
            "paper_only",
            False,
        )
    ):
        raise ValueError(
            "OBSERVATION_NOT_PAPER_ONLY"
        )

    if bool(
        observation.get(
            "live_execution",
            False,
        )
    ):
        raise ValueError(
            "OBSERVATION_LIVE_EXECUTION_FORBIDDEN"
        )

    if bool(
        observation.get(
            "credentials_used",
            False,
        )
    ):
        raise ValueError(
            "OBSERVATION_CREDENTIALS_FORBIDDEN"
        )

    expected_id = (
        build_observation_id(
            observation
        )
    )

    if str(
        observation.get(
            "observation_id",
            "",
        )
    ) != expected_id:
        raise ValueError(
            "OBSERVATION_ID_MISMATCH"
        )


def validate_safety_contracts(
    *,
    analytics_contract: Mapping[
        str,
        Any,
    ],
    pipeline_contract: Mapping[
        str,
        Any,
    ],
) -> None:
    if not bool(
        analytics_contract.get(
            "paper_only",
            False,
        )
    ):
        raise ValueError(
            "ANALYTICS_NOT_PAPER_ONLY"
        )

    if not bool(
        analytics_contract.get(
            "read_only",
            False,
        )
    ):
        raise ValueError(
            "ANALYTICS_NOT_READ_ONLY"
        )

    if bool(
        analytics_contract.get(
            "live_execution",
            False,
        )
    ):
        raise ValueError(
            "ANALYTICS_LIVE_EXECUTION_FORBIDDEN"
        )

    if not bool(
        pipeline_contract.get(
            "paper_only",
            False,
        )
    ):
        raise ValueError(
            "PIPELINE_NOT_PAPER_ONLY"
        )

    if bool(
        pipeline_contract.get(
            "live_execution",
            False,
        )
    ):
        raise ValueError(
            "PIPELINE_LIVE_EXECUTION_FORBIDDEN"
        )

    if bool(
        pipeline_contract.get(
            "credentials_used",
            False,
        )
    ):
        raise ValueError(
            "PIPELINE_CREDENTIALS_FORBIDDEN"
        )


def build_observation_id(
    observation: Mapping[
        str,
        Any,
    ],
) -> str:
    payload = {
        "analytics_id": (
            observation.get(
                "analytics_id",
                "",
            )
        ),
        "pipeline_id": (
            observation.get(
                "pipeline_id",
                "",
            )
        ),
        "cycle_id": (
            observation.get(
                "cycle_id",
                "",
            )
        ),
        "plan_id": (
            observation.get(
                "plan_id",
                "",
            )
        ),
        "starting_equity": (
            observation.get(
                "starting_equity",
                0.0,
            )
        ),
        "ending_equity": (
            observation.get(
                "ending_equity",
                0.0,
            )
        ),
        "cycle_pnl": (
            observation.get(
                "cycle_pnl",
                0.0,
            )
        ),
        "cycle_return": (
            observation.get(
                "cycle_return",
                0.0,
            )
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    return (
        "PERFORMANCE-OBSERVATION-"
        + digest[:24]
    )


def build_record_hash(
    record: Mapping[
        str,
        Any,
    ],
) -> str:
    payload = {
        key: value
        for key, value
        in record.items()
        if key != "record_hash"
    }

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def write_json_atomic(
    path: Path,
    payload: Mapping[
        str,
        Any,
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            default=str,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def required_text(
    payload: Mapping[
        str,
        Any,
    ],
    key: str,
) -> str:
    value = str(
        payload.get(
            key,
            "",
        )
    ).strip()

    if not value:
        raise ValueError(
            "REQUIRED_FIELD_MISSING:"
            + key
        )

    return value


def finite(
    value: Any,
    *,
    name: str,
) -> float:
    number = float(
        value
    )

    if not math.isfinite(
        number
    ):
        raise ValueError(
            "NON_FINITE_VALUE:"
            + name
        )

    return number


def integer(
    value: Any,
    *,
    name: str,
) -> int:
    number = int(
        value
    )

    if number < 0:
        raise ValueError(
            "NEGATIVE_INTEGER:"
            + name
        )

    return number


def close(
    left: float,
    right: float,
    tolerance: float = 1e-8,
) -> bool:
    return abs(
        left
        - right
    ) <= tolerance


def ratio(
    numerator: float,
    denominator: float,
) -> float:
    return (
        numerator
        / denominator
        if denominator
        else 0.0
    )


def product(
    values: Iterable[float],
) -> float:
    result = 1.0

    for value in values:
        result *= value

    return result


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


__all__ = [
    "PERFORMANCE_LEDGER_VERSION",
    "SHADOW_DRAWDOWN_CURVE_JSON",
    "SHADOW_EQUITY_CURVE_JSON",
    "SHADOW_PERFORMANCE_LEDGER_JSONL",
    "SHADOW_PERFORMANCE_SUMMARY_JSON",
    "SHADOW_ROLLING_METRICS_JSON",
    "append_performance_observation",
    "build_equity_and_drawdown_curves",
    "build_performance_observation",
    "build_rolling_metrics",
    "read_performance_ledger",
    "rebuild_performance_outputs",
    "summarize_performance",
    "validate_performance_ledger",
]
