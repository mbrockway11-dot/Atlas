"""Paper execution reconciliation and accounting validation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

LATEST_RECONCILIATION_JSON = (
    OUTPUT_DIR
    / "paper_execution_reconciliation.json"
)


def reconcile_paper_execution(
    report: Mapping[str, Any],
    *,
    lifecycle_record: (
        Mapping[str, Any] | None
    ) = None,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    """Reconcile one complete paper execution report."""
    errors: list[str] = []
    warnings: list[str] = []

    intent = dict(
        report.get(
            "intent",
            {},
        )
        or {}
    )

    risk = dict(
        report.get(
            "risk",
            {},
        )
        or {}
    )

    order = dict(
        report.get(
            "order",
            {},
        )
        or {}
    )

    fills = [
        dict(fill)
        for fill in report.get(
            "fills",
            [],
        )
        or []
    ]

    before = dict(
        report.get(
            "account_before",
            {},
        )
        or {}
    )

    after = dict(
        report.get(
            "account_after",
            {},
        )
        or {}
    )

    intent_id = str(
        intent.get(
            "intent_id",
            "",
        )
    )

    order_id = str(
        order.get(
            "order_id",
            "",
        )
    )

    if str(
        risk.get(
            "intent_id",
            "",
        )
    ) != intent_id:
        errors.append(
            "RISK_INTENT_ID_MISMATCH"
        )

    if str(
        order.get(
            "intent_id",
            "",
        )
    ) != intent_id:
        errors.append(
            "ORDER_INTENT_ID_MISMATCH"
        )

    fill_ids: set[str] = set()
    fill_quantity = 0.0
    fill_notional = 0.0
    fill_fees = 0.0

    for fill in fills:
        fill_id = str(
            fill.get(
                "fill_id",
                "",
            )
        )

        if fill_id in fill_ids:
            errors.append(
                "DUPLICATE_FILL_ID:"
                + fill_id
            )

        fill_ids.add(fill_id)

        if str(
            fill.get(
                "intent_id",
                "",
            )
        ) != intent_id:
            errors.append(
                "FILL_INTENT_ID_MISMATCH:"
                + fill_id
            )

        if str(
            fill.get(
                "order_id",
                "",
            )
        ) != order_id:
            errors.append(
                "FILL_ORDER_ID_MISMATCH:"
                + fill_id
            )

        fill_quantity += number(
            fill.get(
                "quantity",
                0.0,
            )
        )

        fill_notional += number(
            fill.get(
                "notional",
                0.0,
            )
        )

        fill_fees += number(
            fill.get(
                "fee",
                0.0,
            )
        )

    order_filled = number(
        order.get(
            "filled_quantity",
            0.0,
        )
    )

    requested_quantity = number(
        order.get(
            "requested_quantity",
            intent.get(
                "quantity",
                0.0,
            ),
        )
    )

    remaining_quantity = number(
        order.get(
            "remaining_quantity",
            0.0,
        )
    )

    if not close(
        fill_quantity,
        order_filled,
        tolerance,
    ):
        errors.append(
            "FILL_QUANTITY_ORDER_MISMATCH"
        )

    if not close(
        requested_quantity,
        order_filled
        + remaining_quantity,
        tolerance,
    ):
        errors.append(
            "ORDER_QUANTITY_BALANCE_MISMATCH"
        )

    if not close(
        fill_fees,
        number(
            order.get(
                "fee_paid",
                0.0,
            )
        ),
        tolerance,
    ):
        errors.append(
            "FILL_FEE_ORDER_MISMATCH"
        )

    status = str(
        order.get(
            "status",
            "",
        )
    )

    if (
        status == "FILLED"
        and not close(
            remaining_quantity,
            0.0,
            tolerance,
        )
    ):
        errors.append(
            "FILLED_ORDER_HAS_REMAINDER"
        )

    if (
        status == "PARTIALLY_FILLED"
        and (
            order_filled <= 0
            or remaining_quantity <= 0
        )
    ):
        errors.append(
            "PARTIAL_FILL_STATE_INVALID"
        )

    if (
        status in {
            "REJECTED",
            "CANCELLED",
        }
        and fill_quantity > tolerance
    ):
        warnings.append(
            "TERMINAL_NONFILL_STATUS_HAS_FILLS"
        )

    side = str(
        intent.get(
            "side",
            "",
        )
    ).upper()

    cash_before = number(
        before.get(
            "cash",
            0.0,
        )
    )

    cash_after = number(
        after.get(
            "cash",
            cash_before,
        )
    )

    expected_cash_after = (
        cash_before
        - fill_notional
        - fill_fees
        if side == "BUY"
        else cash_before
        + fill_notional
        - fill_fees
    )

    if not close(
        cash_after,
        expected_cash_after,
        max(
            tolerance,
            1e-6,
        ),
    ):
        errors.append(
            "CASH_RECONCILIATION_MISMATCH"
        )

    asset = str(
        intent.get(
            "asset",
            "",
        )
    )

    before_quantity = position_quantity(
        before,
        asset,
    )

    after_quantity = position_quantity(
        after,
        asset,
    )

    expected_after_quantity = (
        before_quantity
        + fill_quantity
        if side == "BUY"
        else before_quantity
        - fill_quantity
    )

    if not close(
        after_quantity,
        expected_after_quantity,
        tolerance,
    ):
        errors.append(
            "POSITION_QUANTITY_MISMATCH"
        )

    before_nlv = number(
        before.get(
            "net_liquidation_value",
            cash_before,
        )
    )

    after_nlv = number(
        after.get(
            "net_liquidation_value",
            cash_after,
        )
    )

    expected_nlv_change = (
        -fill_fees
    )

    actual_nlv_change = (
        after_nlv
        - before_nlv
    )

    if not close(
        actual_nlv_change,
        expected_nlv_change,
        max(
            tolerance,
            1e-6,
        ),
    ):
        warnings.append(
            "NET_LIQUIDATION_CHANGE_DIFFERS_FROM_FEES"
        )

    lifecycle_checks = {
        "provided": bool(
            lifecycle_record
        ),
        "state_matches_order": None,
        "filled_quantity_matches": None,
        "remaining_quantity_matches": None,
    }

    if lifecycle_record:
        lifecycle_state = str(
            lifecycle_record.get(
                "state",
                "",
            )
        )

        expected_lifecycle_state = {
            "FILLED": "FILLED",
            "PARTIALLY_FILLED": (
                "PARTIALLY_FILLED"
            ),
            "CANCELLED": "CANCELLED",
            "REJECTED": "REJECTED",
        }.get(status)

        lifecycle_checks[
            "state_matches_order"
        ] = bool(
            expected_lifecycle_state
            is None
            or lifecycle_state
            == expected_lifecycle_state
        )

        lifecycle_checks[
            "filled_quantity_matches"
        ] = close(
            number(
                lifecycle_record.get(
                    "filled_quantity",
                    0.0,
                )
            ),
            order_filled,
            tolerance,
        )

        lifecycle_checks[
            "remaining_quantity_matches"
        ] = close(
            number(
                lifecycle_record.get(
                    "remaining_quantity",
                    0.0,
                )
            ),
            remaining_quantity,
            tolerance,
        )

        if not lifecycle_checks[
            "state_matches_order"
        ]:
            errors.append(
                "LIFECYCLE_ORDER_STATE_MISMATCH"
            )

        if not lifecycle_checks[
            "filled_quantity_matches"
        ]:
            errors.append(
                "LIFECYCLE_FILLED_QUANTITY_MISMATCH"
            )

        if not lifecycle_checks[
            "remaining_quantity_matches"
        ]:
            errors.append(
                "LIFECYCLE_REMAINING_QUANTITY_MISMATCH"
            )

    reconciliation_id = (
        build_reconciliation_id(
            {
                "intent_id": (
                    intent_id
                ),
                "order_id": order_id,
                "status": status,
                "fill_ids": sorted(
                    fill_ids
                ),
                "cash_before": (
                    cash_before
                ),
                "cash_after": (
                    cash_after
                ),
                "position_before": (
                    before_quantity
                ),
                "position_after": (
                    after_quantity
                ),
            }
        )
    )

    return {
        "success": not errors,
        "reconciliation_id": (
            reconciliation_id
        ),
        "intent_id": intent_id,
        "order_id": order_id,
        "order_status": status,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "fills": len(fills),
            "errors": len(errors),
            "warnings": len(
                warnings
            ),
        },
        "quantity": {
            "requested": (
                requested_quantity
            ),
            "filled_from_order": (
                order_filled
            ),
            "filled_from_fills": (
                fill_quantity
            ),
            "remaining": (
                remaining_quantity
            ),
        },
        "fees": {
            "order_fee": number(
                order.get(
                    "fee_paid",
                    0.0,
                )
            ),
            "fill_fee_total": (
                fill_fees
            ),
        },
        "cash": {
            "before": cash_before,
            "expected_after": (
                expected_cash_after
            ),
            "actual_after": (
                cash_after
            ),
        },
        "position": {
            "asset": asset,
            "before_quantity": (
                before_quantity
            ),
            "expected_after_quantity": (
                expected_after_quantity
            ),
            "actual_after_quantity": (
                after_quantity
            ),
        },
        "net_liquidation": {
            "before": before_nlv,
            "after": after_nlv,
            "actual_change": (
                actual_nlv_change
            ),
            "expected_change_from_fees": (
                expected_nlv_change
            ),
        },
        "lifecycle": (
            lifecycle_checks
        ),
        "contract": {
            "paper_only": bool(
                report.get(
                    "mode",
                    ""
                )
                == "PAPER"
            ),
            "live_execution": bool(
                report.get(
                    "live_execution",
                    False,
                )
            ),
            "identifier_consistency_checked": True,
            "quantity_reconciled": True,
            "cash_reconciled": True,
            "position_reconciled": True,
            "fees_reconciled": True,
        },
    }


def write_reconciliation_report(
    reconciliation: Mapping[
        str,
        Any,
    ],
    path: Path = (
        LATEST_RECONCILIATION_JSON
    ),
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
            dict(reconciliation),
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def position_quantity(
    account: Mapping[str, Any],
    asset: str,
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

    position = positions.get(
        asset,
        {},
    )

    if not isinstance(
        position,
        Mapping,
    ):
        return 0.0

    return number(
        position.get(
            "quantity",
            0.0,
        )
    )


def close(
    left: float,
    right: float,
    tolerance: float,
) -> bool:
    return math.isclose(
        float(left),
        float(right),
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def number(
    value: Any,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return (
        result
        if math.isfinite(result)
        else 0.0
    )


def build_reconciliation_id(
    payload: Mapping[str, Any],
) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return (
        "RECON-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )


__all__ = [
    "LATEST_RECONCILIATION_JSON",
    "reconcile_paper_execution",
    "write_reconciliation_report",
]
