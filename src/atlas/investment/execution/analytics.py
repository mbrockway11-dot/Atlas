"""Read-only execution quality and cost analytics for Atlas paper trading."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

EXECUTION_ANALYTICS_JSON = (
    OUTPUT_DIR
    / "execution_analytics_report.json"
)

EXECUTION_ANALYTICS_HISTORY_JSONL = (
    OUTPUT_DIR
    / "execution_analytics_history.jsonl"
)

DAILY_EXECUTION_SUMMARY_JSON = (
    OUTPUT_DIR
    / "daily_execution_summary.json"
)

ASSET_EXECUTION_SCORECARD_JSON = (
    OUTPUT_DIR
    / "asset_execution_scorecard.json"
)

ASSET_CLASS_EXECUTION_SCORECARD_JSON = (
    OUTPUT_DIR
    / "asset_class_execution_scorecard.json"
)

EXECUTION_ANALYTICS_VERSION = "1.0.0"


def build_execution_analytics(
    shadow_report: Mapping[str, Any],
    *,
    pipeline_report: Mapping[
        str,
        Any,
    ] | None = None,
    write_outputs: bool = True,
    report_path: Path = (
        EXECUTION_ANALYTICS_JSON
    ),
    history_path: Path = (
        EXECUTION_ANALYTICS_HISTORY_JSONL
    ),
    daily_path: Path = (
        DAILY_EXECUTION_SUMMARY_JSON
    ),
    asset_path: Path = (
        ASSET_EXECUTION_SCORECARD_JSON
    ),
    asset_class_path: Path = (
        ASSET_CLASS_EXECUTION_SCORECARD_JSON
    ),
) -> dict[str, Any]:
    """Analyze one verified paper shadow-cycle report."""
    pipeline = dict(
        pipeline_report or {}
    )

    cycle_id = str(
        shadow_report.get(
            "cycle_id",
            "",
        )
    )

    plan_id = str(
        shadow_report.get(
            "plan_id",
            "",
        )
    )

    pipeline_id = str(
        pipeline.get(
            "pipeline_id",
            "",
        )
    )

    results = list(
        shadow_report.get(
            "results",
            [],
        )
        or []
    )

    rows: list[
        dict[str, Any]
    ] = []

    errors: list[str] = []
    warnings: list[str] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        if not isinstance(
            result,
            Mapping,
        ):
            errors.append(
                "RESULT_NOT_MAPPING:"
                + str(index)
            )
            continue

        try:
            row = analyze_execution_result(
                result,
                index=index,
            )
        except Exception as error:
            errors.append(
                "RESULT_ANALYSIS_FAILED:"
                + str(index)
                + ":"
                + str(error)
            )
            continue

        rows.append(row)

        if not row[
            "reconciliation_success"
        ]:
            errors.append(
                "RECONCILIATION_NOT_VERIFIED:"
                + row["intent_id"]
            )

        if not row[
            "result_success"
        ]:
            warnings.append(
                "EXECUTION_RESULT_FAILED:"
                + row["intent_id"]
            )

    summary = summarize_rows(
        rows
    )

    account_before = dict(
        shadow_report.get(
            "account_before",
            {},
        )
        or {}
    )

    account_after = dict(
        shadow_report.get(
            "account_after",
            {},
        )
        or {}
    )

    starting_equity = account_equity(
        account_before
    )

    ending_equity = account_equity(
        account_after
    )

    utilization = build_utilization(
        rows=rows,
        account_before=account_before,
        account_after=account_after,
        starting_equity=starting_equity,
        ending_equity=ending_equity,
    )

    asset_scorecard = aggregate_scorecard(
        rows,
        key_name="asset",
    )

    class_scorecard = (
        aggregate_scorecard(
            rows,
            key_name="asset_class",
        )
    )

    analytics_id = build_analytics_id(
        cycle_id=cycle_id,
        plan_id=plan_id,
        pipeline_id=pipeline_id,
        rows=rows,
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    daily_summary = {
        "version": (
            EXECUTION_ANALYTICS_VERSION
        ),
        "analytics_id": analytics_id,
        "generated_at": generated_at,
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "pipeline_id": pipeline_id,
        "date": extract_date(
            shadow_report.get(
                "completed_at",
                generated_at,
            )
        ),
        "summary": summary,
        "utilization": utilization,
        "success": not errors,
    }

    report = {
        "success": not errors,
        "version": (
            EXECUTION_ANALYTICS_VERSION
        ),
        "analytics_id": analytics_id,
        "generated_at": generated_at,
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "pipeline_id": pipeline_id,
        "shadow_status": str(
            shadow_report.get(
                "status",
                "",
            )
        ),
        "summary": summary,
        "utilization": utilization,
        "orders": rows,
        "asset_scorecard": (
            asset_scorecard
        ),
        "asset_class_scorecard": (
            class_scorecard
        ),
        "errors": errors,
        "warnings": warnings,
        "contract": {
            "read_only": True,
            "paper_only": True,
            "verified_records_only": True,
            "mutates_account": False,
            "submits_orders": False,
            "uses_credentials": False,
            "live_execution": False,
        },
        "outputs": {
            "analytics_report": str(
                report_path
            ),
            "analytics_history": str(
                history_path
            ),
            "daily_summary": str(
                daily_path
            ),
            "asset_scorecard": str(
                asset_path
            ),
            "asset_class_scorecard": str(
                asset_class_path
            ),
        },
    }

    if write_outputs:
        write_json_atomic(
            report_path,
            report,
        )

        append_jsonl(
            history_path,
            {
                "analytics_id": (
                    analytics_id
                ),
                "generated_at": (
                    generated_at
                ),
                "cycle_id": cycle_id,
                "plan_id": plan_id,
                "pipeline_id": (
                    pipeline_id
                ),
                "success": (
                    report["success"]
                ),
                "summary": summary,
                "utilization": (
                    utilization
                ),
            },
        )

        write_json_atomic(
            daily_path,
            daily_summary,
        )

        write_json_atomic(
            asset_path,
            {
                "analytics_id": (
                    analytics_id
                ),
                "generated_at": (
                    generated_at
                ),
                "rows": (
                    asset_scorecard
                ),
            },
        )

        write_json_atomic(
            asset_class_path,
            {
                "analytics_id": (
                    analytics_id
                ),
                "generated_at": (
                    generated_at
                ),
                "rows": (
                    class_scorecard
                ),
            },
        )

    return report


def analyze_execution_result(
    result: Mapping[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    execution = dict(
        result.get(
            "execution",
            {},
        )
        or {}
    )

    intent = dict(
        execution.get(
            "intent",
            {},
        )
        or {}
    )

    risk = dict(
        execution.get(
            "risk",
            {},
        )
        or {}
    )

    order = dict(
        execution.get(
            "order",
            {},
        )
        or {}
    )

    fills = [
        dict(fill)
        for fill
        in execution.get(
            "fills",
            [],
        )
        or []
        if isinstance(
            fill,
            Mapping,
        )
    ]

    reconciliation = dict(
        execution.get(
            "reconciliation",
            {},
        )
        or {}
    )

    asset = normalize_symbol(
        order.get(
            "asset",
            intent.get(
                "asset",
                "",
            ),
        )
    )

    instrument = get_instrument(
        asset
    )

    if instrument is None:
        raise KeyError(
            "UNREGISTERED_INSTRUMENT:"
            + asset
        )

    side = str(
        order.get(
            "side",
            intent.get(
                "side",
                "",
            ),
        )
    ).strip().upper()

    direction = (
        1.0
        if side == "BUY"
        else -1.0
    )

    requested_quantity = finite(
        order.get(
            "requested_quantity",
            intent.get(
                "quantity",
                0.0,
            ),
        )
    )

    filled_quantity = finite(
        order.get(
            "filled_quantity",
            0.0,
        )
    )

    remaining_quantity = finite(
        order.get(
            "remaining_quantity",
            max(
                0.0,
                requested_quantity
                - filled_quantity,
            ),
        )
    )

    arrival_price = finite(
        intent.get(
            "reference_price",
            0.0,
        )
    )

    average_fill_price = finite(
        order.get(
            "average_fill_price",
            weighted_fill_price(
                fills
            ),
        )
    )

    fill_notional = sum(
        finite(
            fill.get(
                "notional",
                finite(
                    fill.get(
                        "quantity",
                        0.0,
                    )
                )
                * finite(
                    fill.get(
                        "price",
                        0.0,
                    )
                ),
            )
        )
        for fill in fills
    )

    fee_cost = sum(
        finite(
            fill.get(
                "fee",
                0.0,
            )
        )
        for fill in fills
    )

    if not fills:
        fee_cost = finite(
            order.get(
                "fee_paid",
                0.0,
            )
        )

    price_difference = (
        average_fill_price
        - arrival_price
        if (
            average_fill_price > 0
            and arrival_price > 0
        )
        else 0.0
    )

    signed_price_difference = (
        direction
        * price_difference
    )

    slippage_bps = (
        signed_price_difference
        / arrival_price
        * 10_000.0
        if arrival_price > 0
        else 0.0
    )

    slippage_cost = (
        signed_price_difference
        * filled_quantity
        * instrument.contract_multiplier
    )

    arrival_notional = (
        arrival_price
        * filled_quantity
        * instrument.contract_multiplier
    )

    implementation_shortfall = (
        slippage_cost
        + fee_cost
    )

    implementation_shortfall_bps = (
        implementation_shortfall
        / abs(
            arrival_notional
        )
        * 10_000.0
        if arrival_notional
        else 0.0
    )

    fill_ratio = (
        filled_quantity
        / requested_quantity
        if requested_quantity > 0
        else 0.0
    )

    submitted_at = str(
        order.get(
            "submitted_at",
            "",
        )
    )

    completed_at = str(
        order.get(
            "completed_at",
            "",
        )
    )

    time_to_completion_ms = (
        duration_milliseconds(
            submitted_at,
            completed_at,
        )
    )

    configured_slippage = (
        weighted_fill_field(
            fills,
            field="slippage_bps",
        )
    )

    return {
        "sequence": index,
        "result_success": bool(
            result.get(
                "success",
                False,
            )
        ),
        "execution_id": str(
            execution.get(
                "execution_id",
                "",
            )
        ),
        "intent_id": str(
            intent.get(
                "intent_id",
                result.get(
                    "intent_id",
                    "",
                ),
            )
        ),
        "order_id": str(
            order.get(
                "order_id",
                "",
            )
        ),
        "asset": asset,
        "asset_class": (
            instrument.asset_class
        ),
        "instrument_type": (
            instrument.instrument_type
        ),
        "side": side,
        "status": str(
            order.get(
                "status",
                "",
            )
        ).strip().upper(),
        "risk_approved": bool(
            risk.get(
                "approved",
                False,
            )
        ),
        "reconciliation_success": bool(
            reconciliation.get(
                "success",
                False,
            )
        ),
        "requested_quantity": (
            requested_quantity
        ),
        "filled_quantity": (
            filled_quantity
        ),
        "remaining_quantity": (
            remaining_quantity
        ),
        "fill_ratio": fill_ratio,
        "fill_count": len(
            fills
        ),
        "arrival_price": (
            arrival_price
        ),
        "average_fill_price": (
            average_fill_price
        ),
        "arrival_notional": (
            arrival_notional
        ),
        "fill_notional": (
            fill_notional
        ),
        "configured_slippage_bps": (
            configured_slippage
        ),
        "signed_slippage_bps": (
            slippage_bps
        ),
        "slippage_cost": (
            slippage_cost
        ),
        "fee_cost": fee_cost,
        "implementation_shortfall": (
            implementation_shortfall
        ),
        "implementation_shortfall_bps": (
            implementation_shortfall_bps
        ),
        "submitted_at": (
            submitted_at
        ),
        "completed_at": (
            completed_at
        ),
        "time_to_completion_ms": (
            time_to_completion_ms
        ),
        "rejection_reason": str(
            order.get(
                "rejection_reason",
                "",
            )
        ),
    }


def summarize_rows(
    rows: Sequence[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:
    order_count = len(rows)

    requested_quantity = sum(
        finite(
            row.get(
                "requested_quantity",
                0.0,
            )
        )
        for row in rows
    )

    filled_quantity = sum(
        finite(
            row.get(
                "filled_quantity",
                0.0,
            )
        )
        for row in rows
    )

    gross_arrival_notional = sum(
        abs(
            finite(
                row.get(
                    "arrival_notional",
                    0.0,
                )
            )
        )
        for row in rows
    )

    gross_fill_notional = sum(
        abs(
            finite(
                row.get(
                    "fill_notional",
                    0.0,
                )
            )
        )
        for row in rows
    )

    buy_notional = sum(
        abs(
            finite(
                row.get(
                    "fill_notional",
                    0.0,
                )
            )
        )
        for row in rows
        if row.get(
            "side"
        )
        == "BUY"
    )

    sell_notional = sum(
        abs(
            finite(
                row.get(
                    "fill_notional",
                    0.0,
                )
            )
        )
        for row in rows
        if row.get(
            "side"
        )
        == "SELL"
    )

    fee_cost = sum(
        finite(
            row.get(
                "fee_cost",
                0.0,
            )
        )
        for row in rows
    )

    slippage_cost = sum(
        finite(
            row.get(
                "slippage_cost",
                0.0,
            )
        )
        for row in rows
    )

    total_cost = (
        fee_cost
        + slippage_cost
    )

    filled_orders = count_status(
        rows,
        "FILLED",
    )

    partial_orders = count_status(
        rows,
        "PARTIALLY_FILLED",
    )

    cancelled_orders = count_status(
        rows,
        "CANCELLED",
    )

    rejected_orders = count_status(
        rows,
        "REJECTED",
    )

    approved_orders = sum(
        1
        for row in rows
        if bool(
            row.get(
                "risk_approved",
                False,
            )
        )
    )

    reconciled_orders = sum(
        1
        for row in rows
        if bool(
            row.get(
                "reconciliation_success",
                False,
            )
        )
    )

    times = [
        finite(
            row.get(
                "time_to_completion_ms",
                0.0,
            )
        )
        for row in rows
        if row.get(
            "time_to_completion_ms"
        )
        is not None
    ]

    weighted_slippage = weighted_average(
        rows,
        value_field=(
            "signed_slippage_bps"
        ),
        weight_field=(
            "arrival_notional"
        ),
    )

    weighted_shortfall = weighted_average(
        rows,
        value_field=(
            "implementation_shortfall_bps"
        ),
        weight_field=(
            "arrival_notional"
        ),
    )

    return {
        "order_count": order_count,
        "approved_order_count": (
            approved_orders
        ),
        "filled_order_count": (
            filled_orders
        ),
        "partial_fill_order_count": (
            partial_orders
        ),
        "cancelled_order_count": (
            cancelled_orders
        ),
        "rejected_order_count": (
            rejected_orders
        ),
        "reconciled_order_count": (
            reconciled_orders
        ),
        "requested_quantity": (
            requested_quantity
        ),
        "filled_quantity": (
            filled_quantity
        ),
        "fill_rate": ratio(
            filled_orders
            + partial_orders,
            order_count,
        ),
        "full_fill_rate": ratio(
            filled_orders,
            order_count,
        ),
        "partial_fill_rate": ratio(
            partial_orders,
            order_count,
        ),
        "cancellation_rate": ratio(
            cancelled_orders,
            order_count,
        ),
        "rejection_rate": ratio(
            rejected_orders,
            order_count,
        ),
        "risk_approval_rate": ratio(
            approved_orders,
            order_count,
        ),
        "reconciliation_success_rate": (
            ratio(
                reconciled_orders,
                order_count,
            )
        ),
        "gross_arrival_notional": (
            gross_arrival_notional
        ),
        "gross_fill_notional": (
            gross_fill_notional
        ),
        "buy_notional": buy_notional,
        "sell_notional": (
            sell_notional
        ),
        "net_traded_notional": (
            buy_notional
            - sell_notional
        ),
        "fee_cost": fee_cost,
        "slippage_cost": (
            slippage_cost
        ),
        "total_execution_cost": (
            total_cost
        ),
        "weighted_slippage_bps": (
            weighted_slippage
        ),
        "weighted_implementation_shortfall_bps": (
            weighted_shortfall
        ),
        "average_time_to_completion_ms": (
            sum(times)
            / len(times)
            if times
            else 0.0
        ),
        "maximum_time_to_completion_ms": (
            max(times)
            if times
            else 0.0
        ),
    }


def build_utilization(
    *,
    rows: Sequence[
        Mapping[str, Any]
    ],
    account_before: Mapping[
        str,
        Any,
    ],
    account_after: Mapping[
        str,
        Any,
    ],
    starting_equity: float,
    ending_equity: float,
) -> dict[str, Any]:
    gross_traded = sum(
        abs(
            finite(
                row.get(
                    "fill_notional",
                    0.0,
                )
            )
        )
        for row in rows
    )

    total_cost = sum(
        finite(
            row.get(
                "implementation_shortfall",
                0.0,
            )
        )
        for row in rows
    )

    ending_cash = finite(
        account_after.get(
            "cash",
            0.0,
        )
    )

    starting_cash = finite(
        account_before.get(
            "cash",
            0.0,
        )
    )

    ending_gross_exposure = (
        account_gross_exposure(
            account_after
        )
    )

    return {
        "starting_equity": (
            starting_equity
        ),
        "ending_equity": (
            ending_equity
        ),
        "starting_cash": (
            starting_cash
        ),
        "ending_cash": ending_cash,
        "turnover_ratio": ratio(
            gross_traded,
            starting_equity,
        ),
        "execution_cost_to_starting_equity": (
            ratio(
                total_cost,
                starting_equity,
            )
        ),
        "execution_cost_bps_of_starting_equity": (
            ratio(
                total_cost,
                starting_equity,
            )
            * 10_000.0
        ),
        "ending_cash_weight": ratio(
            ending_cash,
            ending_equity,
        ),
        "ending_gross_exposure": (
            ending_gross_exposure
        ),
        "ending_gross_exposure_ratio": (
            ratio(
                ending_gross_exposure,
                ending_equity,
            )
        ),
    }


def aggregate_scorecard(
    rows: Sequence[
        Mapping[str, Any]
    ],
    *,
    key_name: str,
) -> list[dict[str, Any]]:
    groups: dict[
        str,
        list[Mapping[str, Any]],
    ] = {}

    for row in rows:
        key = str(
            row.get(
                key_name,
                "",
            )
        )

        groups.setdefault(
            key,
            [],
        ).append(row)

    result: list[
        dict[str, Any]
    ] = []

    for key in sorted(groups):
        members = groups[key]
        summary = summarize_rows(
            members
        )

        result.append({
            key_name: key,
            **summary,
        })

    return result


def weighted_fill_price(
    fills: Sequence[
        Mapping[str, Any]
    ],
) -> float:
    quantity = sum(
        finite(
            fill.get(
                "quantity",
                0.0,
            )
        )
        for fill in fills
    )

    if quantity <= 0:
        return 0.0

    return sum(
        finite(
            fill.get(
                "quantity",
                0.0,
            )
        )
        * finite(
            fill.get(
                "price",
                0.0,
            )
        )
        for fill in fills
    ) / quantity


def weighted_fill_field(
    fills: Sequence[
        Mapping[str, Any]
    ],
    *,
    field: str,
) -> float:
    quantity = sum(
        finite(
            fill.get(
                "quantity",
                0.0,
            )
        )
        for fill in fills
    )

    if quantity <= 0:
        return 0.0

    return sum(
        finite(
            fill.get(
                "quantity",
                0.0,
            )
        )
        * finite(
            fill.get(
                field,
                0.0,
            )
        )
        for fill in fills
    ) / quantity


def weighted_average(
    rows: Sequence[
        Mapping[str, Any]
    ],
    *,
    value_field: str,
    weight_field: str,
) -> float:
    weights = [
        abs(
            finite(
                row.get(
                    weight_field,
                    0.0,
                )
            )
        )
        for row in rows
    ]

    total_weight = sum(
        weights
    )

    if total_weight <= 0:
        return 0.0

    return sum(
        finite(
            row.get(
                value_field,
                0.0,
            )
        )
        * weight
        for row, weight
        in zip(
            rows,
            weights,
            strict=True,
        )
    ) / total_weight


def account_equity(
    account: Mapping[
        str,
        Any,
    ],
) -> float:
    explicit = account.get(
        "net_liquidation_value"
    )

    if explicit is not None:
        return finite(
            explicit
        )

    cash = finite(
        account.get(
            "cash",
            0.0,
        )
    )

    positions = account.get(
        "positions",
        {},
    )

    if not isinstance(
        positions,
        Mapping,
    ):
        return cash

    position_value = 0.0

    for position in (
        positions.values()
    ):
        if not isinstance(
            position,
            Mapping,
        ):
            continue

        quantity = finite(
            position.get(
                "quantity",
                0.0,
            )
        )

        mark_price = finite(
            position.get(
                "mark_price",
                0.0,
            )
        )

        position_value += (
            quantity
            * mark_price
        )

    return (
        cash
        + position_value
    )


def account_gross_exposure(
    account: Mapping[
        str,
        Any,
    ],
) -> float:
    positions = account.get(
        "positions",
        {},
    )

    if not isinstance(
        positions,
        Mapping,
    ):
        return 0.0

    gross = 0.0

    for asset, position in (
        positions.items()
    ):
        if not isinstance(
            position,
            Mapping,
        ):
            continue

        canonical = normalize_symbol(
            asset
        )

        instrument = get_instrument(
            canonical
        )

        multiplier = (
            instrument.contract_multiplier
            if instrument is not None
            else 1.0
        )

        gross += abs(
            finite(
                position.get(
                    "quantity",
                    0.0,
                )
            )
            * finite(
                position.get(
                    "mark_price",
                    0.0,
                )
            )
            * multiplier
        )

    return gross


def duration_milliseconds(
    start: str,
    end: str,
) -> float | None:
    if not start or not end:
        return None

    try:
        start_value = parse_time(
            start
        )

        end_value = parse_time(
            end
        )
    except ValueError:
        return None

    return max(
        0.0,
        (
            end_value
            - start_value
        ).total_seconds()
        * 1_000.0,
    )


def parse_time(
    value: str,
) -> datetime:
    text = str(value).strip()

    if text.endswith("Z"):
        text = (
            text[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=UTC
        )

    return parsed.astimezone(
        UTC
    )


def extract_date(
    value: Any,
) -> str:
    try:
        return parse_time(
            str(value)
        ).date().isoformat()
    except ValueError:
        return datetime.now(
            UTC
        ).date().isoformat()


def count_status(
    rows: Sequence[
        Mapping[str, Any]
    ],
    status: str,
) -> int:
    return sum(
        1
        for row in rows
        if str(
            row.get(
                "status",
                "",
            )
        )
        == status
    )


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


def finite(
    value: Any,
) -> float:
    number = float(
        value or 0.0
    )

    if not math.isfinite(
        number
    ):
        raise ValueError(
            "NON_FINITE_NUMBER"
        )

    return number


def build_analytics_id(
    *,
    cycle_id: str,
    plan_id: str,
    pipeline_id: str,
    rows: Sequence[
        Mapping[str, Any]
    ],
) -> str:
    payload = {
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "pipeline_id": pipeline_id,
        "orders": [
            {
                "intent_id": row.get(
                    "intent_id",
                    "",
                ),
                "order_id": row.get(
                    "order_id",
                    "",
                ),
                "status": row.get(
                    "status",
                    "",
                ),
                "fill_notional": row.get(
                    "fill_notional",
                    0.0,
                ),
                "fee_cost": row.get(
                    "fee_cost",
                    0.0,
                ),
            }
            for row in rows
        ],
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
        "EXECUTION-ANALYTICS-"
        + digest[:24]
    )


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
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def append_jsonl(
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

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                dict(payload),
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


__all__ = [
    "ASSET_CLASS_EXECUTION_SCORECARD_JSON",
    "ASSET_EXECUTION_SCORECARD_JSON",
    "DAILY_EXECUTION_SUMMARY_JSON",
    "EXECUTION_ANALYTICS_HISTORY_JSONL",
    "EXECUTION_ANALYTICS_JSON",
    "EXECUTION_ANALYTICS_VERSION",
    "aggregate_scorecard",
    "analyze_execution_result",
    "build_execution_analytics",
    "summarize_rows",
]
