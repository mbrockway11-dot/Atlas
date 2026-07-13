"""Paper-account valuation and shadow-cycle performance attribution."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.execution.contracts import (
    AccountSnapshot,
)
from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

SHADOW_ATTRIBUTION_JSON = (
    OUTPUT_DIR
    / "shadow_performance_attribution.json"
)

SHADOW_ATTRIBUTION_HISTORY_JSONL = (
    OUTPUT_DIR
    / "shadow_performance_history.jsonl"
)

ATTRIBUTION_VERSION = "1.0.0"


def value_account(
    account: AccountSnapshot,
    reference_prices: Mapping[
        str,
        float,
    ],
) -> dict[str, Any]:
    """Mark one paper account using canonical reference prices."""
    normalized_prices = {
        normalize_symbol(
            symbol
        ): float(price)
        for symbol, price
        in reference_prices.items()
    }

    rows: list[
        dict[str, Any]
    ] = []

    market_value_total = 0.0
    gross_exposure = 0.0
    missing_prices: list[str] = []

    for asset, position in sorted(
        account.positions.items()
    ):
        canonical = normalize_symbol(
            asset
        )

        instrument = get_instrument(
            canonical
        )

        assert instrument is not None

        price = normalized_prices.get(
            canonical
        )

        if price is None:
            missing_prices.append(
                canonical
            )
            continue

        quantity = float(
            position.quantity
        )

        market_value = (
            quantity
            * price
            * instrument.contract_multiplier
        )

        cost_basis = (
            quantity
            * position.average_price
            * instrument.contract_multiplier
        )

        unrealized_pnl = (
            market_value
            - cost_basis
        )

        absolute_notional = abs(
            market_value
        )

        market_value_total += (
            market_value
        )

        gross_exposure += (
            absolute_notional
        )

        rows.append({
            "asset": canonical,
            "asset_class": (
                instrument.asset_class
            ),
            "instrument_type": (
                instrument.instrument_type
            ),
            "quantity": quantity,
            "average_price": float(
                position.average_price
            ),
            "mark_price": price,
            "contract_multiplier": (
                instrument.contract_multiplier
            ),
            "cost_basis": cost_basis,
            "market_value": market_value,
            "absolute_notional": (
                absolute_notional
            ),
            "unrealized_pnl": (
                unrealized_pnl
            ),
        })

    net_liquidation_value = (
        float(account.cash)
        + market_value_total
    )

    return {
        "success": not missing_prices,
        "cash": float(
            account.cash
        ),
        "market_value": (
            market_value_total
        ),
        "gross_exposure": (
            gross_exposure
        ),
        "net_liquidation_value": (
            net_liquidation_value
        ),
        "realized_pnl": float(
            account.realized_pnl
        ),
        "daily_pnl": float(
            account.daily_pnl
        ),
        "positions": rows,
        "missing_prices": (
            missing_prices
        ),
    }


def build_shadow_attribution(
    *,
    cycle_id: str,
    plan_id: str,
    snapshot_id: str,
    account_before: AccountSnapshot,
    account_after: AccountSnapshot,
    reference_prices: Mapping[
        str,
        float,
    ],
    execution_results: list[
        Mapping[str, Any]
    ] | None = None,
    write_output: bool = True,
    output_path: Path = (
        SHADOW_ATTRIBUTION_JSON
    ),
    history_path: Path = (
        SHADOW_ATTRIBUTION_HISTORY_JSONL
    ),
) -> dict[str, Any]:
    """Attribute one paper cycle by asset and asset class."""
    before = value_account(
        account_before,
        reference_prices,
    )

    after = value_account(
        account_after,
        reference_prices,
    )

    errors: list[str] = []

    if not before["success"]:
        errors.extend(
            "MISSING_BEFORE_PRICE:"
            + asset
            for asset
            in before[
                "missing_prices"
            ]
        )

    if not after["success"]:
        errors.extend(
            "MISSING_AFTER_PRICE:"
            + asset
            for asset
            in after[
                "missing_prices"
            ]
        )

    before_map = {
        row["asset"]: row
        for row
        in before["positions"]
    }

    after_map = {
        row["asset"]: row
        for row
        in after["positions"]
    }

    assets = sorted(
        set(before_map)
        | set(after_map)
    )

    asset_rows: list[
        dict[str, Any]
    ] = []

    class_rows: dict[
        str,
        dict[str, Any],
    ] = {}

    for asset in assets:
        before_row = before_map.get(
            asset,
            {}
        )

        after_row = after_map.get(
            asset,
            {}
        )

        instrument = get_instrument(
            asset
        )

        assert instrument is not None

        before_value = float(
            before_row.get(
                "market_value",
                0.0,
            )
        )

        after_value = float(
            after_row.get(
                "market_value",
                0.0,
            )
        )

        before_unrealized = float(
            before_row.get(
                "unrealized_pnl",
                0.0,
            )
        )

        after_unrealized = float(
            after_row.get(
                "unrealized_pnl",
                0.0,
            )
        )

        contribution = (
            after_unrealized
            - before_unrealized
        )

        row = {
            "asset": asset,
            "asset_class": (
                instrument.asset_class
            ),
            "before_quantity": float(
                before_row.get(
                    "quantity",
                    0.0,
                )
            ),
            "after_quantity": float(
                after_row.get(
                    "quantity",
                    0.0,
                )
            ),
            "before_market_value": (
                before_value
            ),
            "after_market_value": (
                after_value
            ),
            "market_value_change": (
                after_value
                - before_value
            ),
            "before_unrealized_pnl": (
                before_unrealized
            ),
            "after_unrealized_pnl": (
                after_unrealized
            ),
            "unrealized_pnl_change": (
                contribution
            ),
        }

        asset_rows.append(
            row
        )

        class_row = (
            class_rows.setdefault(
                instrument.asset_class,
                {
                    "asset_class": (
                        instrument.asset_class
                    ),
                    "asset_count": 0,
                    "before_market_value": 0.0,
                    "after_market_value": 0.0,
                    "market_value_change": 0.0,
                    "unrealized_pnl_change": 0.0,
                },
            )
        )

        class_row[
            "asset_count"
        ] += 1

        class_row[
            "before_market_value"
        ] += before_value

        class_row[
            "after_market_value"
        ] += after_value

        class_row[
            "market_value_change"
        ] += (
            after_value
            - before_value
        )

        class_row[
            "unrealized_pnl_change"
        ] += contribution

    executions = list(
        execution_results or []
    )

    fees = sum(
        float(
            result.get(
                "execution",
                {},
            ).get(
                "order",
                {},
            ).get(
                "fee_paid",
                0.0,
            )
        )
        for result
        in executions
    )

    fills = sum(
        len(
            result.get(
                "execution",
                {},
            ).get(
                "fills",
                [],
            )
        )
        for result
        in executions
    )

    before_nlv = float(
        before[
            "net_liquidation_value"
        ]
    )

    after_nlv = float(
        after[
            "net_liquidation_value"
        ]
    )

    total_pnl = (
        after_nlv
        - before_nlv
    )

    return_pct = (
        total_pnl
        / before_nlv
        if before_nlv
        else 0.0
    )

    attribution_id = (
        build_attribution_id(
            cycle_id=cycle_id,
            plan_id=plan_id,
            snapshot_id=snapshot_id,
            before_nlv=before_nlv,
            after_nlv=after_nlv,
        )
    )

    report = {
        "success": not errors,
        "version": (
            ATTRIBUTION_VERSION
        ),
        "attribution_id": (
            attribution_id
        ),
        "generated_at": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "snapshot_id": (
            snapshot_id
        ),
        "before": before,
        "after": after,
        "performance": {
            "starting_net_liquidation_value": (
                before_nlv
            ),
            "ending_net_liquidation_value": (
                after_nlv
            ),
            "total_pnl": (
                total_pnl
            ),
            "return_pct": (
                return_pct
            ),
            "realized_pnl_change": (
                float(
                    account_after.realized_pnl
                )
                - float(
                    account_before.realized_pnl
                )
            ),
            "daily_pnl_change": (
                float(
                    account_after.daily_pnl
                )
                - float(
                    account_before.daily_pnl
                )
            ),
            "fees": fees,
            "fill_count": fills,
        },
        "asset_attribution": (
            asset_rows
        ),
        "asset_class_attribution": [
            class_rows[key]
            for key
            in sorted(
                class_rows
            )
        ],
        "errors": errors,
        "contract": {
            "paper_only": True,
            "mark_to_market": True,
            "asset_attribution": True,
            "asset_class_attribution": True,
            "live_execution": False,
        },
    }

    if write_output:
        write_json_atomic(
            output_path,
            report,
        )

        append_history(
            history_path,
            report,
        )

    return report


def build_attribution_id(
    *,
    cycle_id: str,
    plan_id: str,
    snapshot_id: str,
    before_nlv: float,
    after_nlv: float,
) -> str:
    payload = {
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "snapshot_id": (
            snapshot_id
        ),
        "before_nlv": (
            before_nlv
        ),
        "after_nlv": (
            after_nlv
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return (
        "ATTRIBUTION-"
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


def append_history(
    path: Path,
    report: Mapping[
        str,
        Any,
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = {
        "attribution_id": (
            report.get(
                "attribution_id",
                "",
            )
        ),
        "generated_at": (
            report.get(
                "generated_at",
                "",
            )
        ),
        "cycle_id": (
            report.get(
                "cycle_id",
                "",
            )
        ),
        "plan_id": (
            report.get(
                "plan_id",
                "",
            )
        ),
        "snapshot_id": (
            report.get(
                "snapshot_id",
                "",
            )
        ),
        "success": bool(
            report.get(
                "success",
                False,
            )
        ),
        "performance": (
            report.get(
                "performance",
                {},
            )
        ),
    }

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                summary,
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


__all__ = [
    "ATTRIBUTION_VERSION",
    "SHADOW_ATTRIBUTION_HISTORY_JSONL",
    "SHADOW_ATTRIBUTION_JSON",
    "build_shadow_attribution",
    "value_account",
]
