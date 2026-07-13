"""Portfolio-target to broker-neutral order-intent bridge.

This module translates target portfolio weights into deterministic OrderIntent
objects. It does not submit orders, mutate account state, or access a broker.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.execution.contracts import (
    AccountSnapshot,
    OrderIntent,
)
from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
    require_paper_instrument,
)


PORTFOLIO_BRIDGE_VERSION = "1.0.0"

DEFAULT_PORTFOLIO_REPORT = Path(
    "output/investment_portfolio_optimizer/"
    "portfolio_optimizer_report.json"
)

OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

LATEST_INTENT_PLAN_JSON = (
    OUTPUT_DIR
    / "portfolio_intent_plan.json"
)


@dataclass(frozen=True)
class PortfolioTarget:
    """One normalized target portfolio weight."""

    asset: str
    target_weight: float
    reference_price: float
    source_rank: float | None = None
    source_label: str = ""

    def __post_init__(self) -> None:
        asset = normalize_symbol(
            self.asset
        )

        weight = float(
            self.target_weight
        )

        price = float(
            self.reference_price
        )

        if not asset:
            raise ValueError(
                "asset is required."
            )

        if not math.isfinite(
            weight
        ):
            raise ValueError(
                "target_weight must be finite."
            )

        if weight < 0:
            raise ValueError(
                "target_weight cannot be negative."
            )

        if not math.isfinite(
            price
        ) or price <= 0:
            raise ValueError(
                "reference_price must be positive and finite."
            )

        object.__setattr__(
            self,
            "asset",
            asset,
        )
        object.__setattr__(
            self,
            "target_weight",
            weight,
        )
        object.__setattr__(
            self,
            "reference_price",
            price,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RebalancePolicy:
    """Hard limits controlling intent generation."""

    minimum_weight_delta: float = 0.01
    minimum_order_notional: float = 25.0
    maximum_order_notional: float = 5_000.0
    maximum_total_turnover: float = 0.25
    minimum_cash_weight: float = 0.10
    quantity_precision: int = 8
    allow_new_short_positions: bool = False
    liquidate_missing_assets: bool = False
    require_registered_assets: bool = True
    require_paper_enabled_assets: bool = True

    def __post_init__(self) -> None:
        for name in (
            "minimum_weight_delta",
            "minimum_order_notional",
            "maximum_order_notional",
            "maximum_total_turnover",
            "minimum_cash_weight",
        ):
            value = float(
                getattr(
                    self,
                    name,
                )
            )

            if not math.isfinite(
                value
            ) or value < 0:
                raise ValueError(
                    f"{name} must be finite and nonnegative."
                )

        if (
            self.minimum_cash_weight
            > 1
        ):
            raise ValueError(
                "minimum_cash_weight cannot exceed 1."
            )

        if (
            self.maximum_total_turnover
            > 2
        ):
            raise ValueError(
                "maximum_total_turnover cannot exceed 2."
            )

        if self.quantity_precision < 0:
            raise ValueError(
                "quantity_precision cannot be negative."
            )


@dataclass(frozen=True)
class RebalanceLine:
    """One normalized portfolio rebalance calculation."""

    asset: str
    reference_price: float
    current_quantity: float
    current_notional: float
    current_weight: float
    target_weight: float
    weight_delta: float
    requested_notional_delta: float
    approved_notional_delta: float
    side: str
    quantity: float
    skipped: bool
    skip_reason: str
    asset_class: str = ""
    instrument_type: str = ""
    contract_multiplier: float = 1.0
    market_session: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_portfolio_intent_plan(
    *,
    targets: Sequence[
        PortfolioTarget
    ],
    account: AccountSnapshot,
    strategy_id: str,
    evidence_id: str,
    policy: RebalancePolicy | None = None,
    write_output: bool = True,
) -> dict[str, Any]:
    """Convert normalized target weights into deterministic order intents."""
    effective_policy = (
        policy
        or RebalancePolicy()
    )

    if not strategy_id.strip():
        raise ValueError(
            "strategy_id is required."
        )

    if not evidence_id.strip():
        raise ValueError(
            "evidence_id is required."
        )

    normalized_targets = normalize_targets(
        targets
    )

    validate_target_instruments(
        normalized_targets,
        require_registered=(
            effective_policy
            .require_registered_assets
        ),
        require_paper_enabled=(
            effective_policy
            .require_paper_enabled_assets
        ),
    )

    target_weight_total = sum(
        target.target_weight
        for target
        in normalized_targets
    )

    maximum_invested_weight = (
        1.0
        - effective_policy.minimum_cash_weight
    )

    if (
        target_weight_total
        > maximum_invested_weight
        + 1e-12
    ):
        raise ValueError(
            "TARGET_WEIGHT_EXCEEDS_CASH_BUFFER:"
            f"{target_weight_total:.12f}>"
            f"{maximum_invested_weight:.12f}"
        )

    equity = (
        account.net_liquidation_value
    )

    if equity <= 0:
        raise ValueError(
            "ACCOUNT_EQUITY_MUST_BE_POSITIVE"
        )

    target_map = {
        target.asset: target
        for target in normalized_targets
    }

    assets = set(
        target_map
    )

    if (
        effective_policy
        .liquidate_missing_assets
    ):
        assets.update(
            account.positions
        )

    raw_lines: list[
        RebalanceLine
    ] = []

    for asset in sorted(
        assets
    ):
        target = target_map.get(
            asset
        )

        position = (
            account.positions.get(
                asset
            )
        )

        current_quantity = (
            position.quantity
            if position is not None
            else 0.0
        )

        instrument = get_instrument(
            asset,
            require_registered=(
                effective_policy
                .require_registered_assets
            ),
        )

        instrument_precision = (
            instrument.quantity_precision
            if instrument is not None
            else effective_policy.quantity_precision
        )

        instrument_minimum_notional = max(
            effective_policy.minimum_order_notional,
            (
                instrument.minimum_notional
                if instrument is not None
                else 0.0
            ),
        )

        contract_multiplier = (
            instrument.contract_multiplier
            if instrument is not None
            else 1.0
        )

        reference_price = (
            target.reference_price
            if target is not None
            else (
                position.mark_price
                if position is not None
                else 0.0
            )
        )

        if reference_price <= 0:
            continue

        current_notional = (
            current_quantity
            * reference_price
            * contract_multiplier
        )

        current_weight = (
            current_notional
            / equity
        )

        target_weight = (
            target.target_weight
            if target is not None
            else 0.0
        )

        weight_delta = (
            target_weight
            - current_weight
        )

        requested_notional_delta = (
            weight_delta
            * equity
        )

        side = (
            "BUY"
            if requested_notional_delta > 0
            else "SELL"
        )

        approved_notional_delta = (
            requested_notional_delta
        )

        skipped = False
        skip_reason = ""

        if (
            abs(weight_delta)
            < effective_policy.minimum_weight_delta
        ):
            skipped = True
            skip_reason = (
                "BELOW_WEIGHT_THRESHOLD"
            )

        if (
            not skipped
            and abs(
                requested_notional_delta
            )
            < instrument_minimum_notional
        ):
            skipped = True
            skip_reason = (
                "BELOW_MINIMUM_NOTIONAL"
            )

        if (
            not skipped
            and abs(
                approved_notional_delta
            )
            > effective_policy.maximum_order_notional
        ):
            approved_notional_delta = (
                math.copysign(
                    effective_policy.maximum_order_notional,
                    approved_notional_delta,
                )
            )

        projected_quantity = (
            current_quantity
            + (
                approved_notional_delta
                / reference_price
            )
        )

        if (
            not skipped
            and not effective_policy.allow_new_short_positions
            and projected_quantity < -1e-12
        ):
            if current_quantity <= 0:
                skipped = True
                skip_reason = (
                    "SHORT_POSITION_DISABLED"
                )
            else:
                approved_notional_delta = (
                    -current_quantity
                    * reference_price
                )

        quantity = (
            round(
                abs(
                    approved_notional_delta
                )
                / (
                    reference_price
                    * contract_multiplier
                ),
                instrument_precision,
            )
            if not skipped
            else 0.0
        )

        if (
            not skipped
            and quantity <= 0
        ):
            skipped = True
            skip_reason = (
                "ZERO_QUANTITY_AFTER_ROUNDING"
            )

        raw_lines.append(
            RebalanceLine(
                asset=asset,
                reference_price=(
                    reference_price
                ),
                current_quantity=(
                    current_quantity
                ),
                current_notional=(
                    current_notional
                ),
                current_weight=(
                    current_weight
                ),
                target_weight=(
                    target_weight
                ),
                weight_delta=(
                    weight_delta
                ),
                requested_notional_delta=(
                    requested_notional_delta
                ),
                approved_notional_delta=(
                    approved_notional_delta
                    if not skipped
                    else 0.0
                ),
                side=side,
                quantity=quantity,
                skipped=skipped,
                skip_reason=(
                    skip_reason
                ),
                asset_class=(
                    instrument.asset_class
                    if instrument is not None
                    else ""
                ),
                instrument_type=(
                    instrument.instrument_type
                    if instrument is not None
                    else ""
                ),
                contract_multiplier=(
                    contract_multiplier
                ),
                market_session=(
                    instrument.market_session
                    if instrument is not None
                    else ""
                ),
            )
        )

    lines = apply_turnover_cap(
        raw_lines,
        equity=equity,
        policy=effective_policy,
    )

    intents: list[
        OrderIntent
    ] = []

    for line in lines:
        if line.skipped:
            continue

        intents.append(
            OrderIntent(
                asset=line.asset,
                side=line.side,
                quantity=line.quantity,
                reference_price=(
                    line.reference_price
                ),
                strategy_id=(
                    strategy_id
                ),
                evidence_id=(
                    evidence_id
                ),
                order_type="MARKET",
                time_in_force="IOC",
                reduce_only=bool(
                    line.side == "SELL"
                    and line.target_weight
                    <= line.current_weight
                ),
            )
        )

    total_turnover_notional = sum(
        abs(
            line.approved_notional_delta
        )
        for line in lines
        if not line.skipped
    )

    total_turnover_weight = (
        total_turnover_notional
        / equity
    )

    generated_at = (
        datetime.now(
            UTC
        ).isoformat()
    )

    plan_id = build_plan_id(
        targets=normalized_targets,
        account=account,
        strategy_id=strategy_id,
        evidence_id=evidence_id,
        policy=effective_policy,
    )

    report = {
        "success": True,
        "version": (
            PORTFOLIO_BRIDGE_VERSION
        ),
        "mode": "INTENT_GENERATION_ONLY",
        "live_execution": False,
        "plan_id": plan_id,
        "generated_at": generated_at,
        "strategy_id": (
            strategy_id
        ),
        "evidence_id": (
            evidence_id
        ),
        "account_equity": equity,
        "target_weight_total": (
            target_weight_total
        ),
        "minimum_cash_weight": (
            effective_policy
            .minimum_cash_weight
        ),
        "total_turnover_notional": (
            total_turnover_notional
        ),
        "total_turnover_weight": (
            total_turnover_weight
        ),
        "targets": [
            target.to_dict()
            for target
            in normalized_targets
        ],
        "rebalance_lines": [
            line.to_dict()
            for line in lines
        ],
        "intents": [
            intent.to_dict()
            for intent in intents
        ],
        "counts": {
            "targets": len(
                normalized_targets
            ),
            "rebalance_lines": len(
                lines
            ),
            "generated_intents": len(
                intents
            ),
            "skipped_lines": sum(
                1
                for line in lines
                if line.skipped
            ),
        },
        "contract": {
            "intent_generation_only": True,
            "submits_orders": False,
            "mutates_account": False,
            "broker_neutral": True,
            "paper_compatible": True,
            "live_credentials_used": False,
        },
        "outputs": {
            "intent_plan_json": str(
                LATEST_INTENT_PLAN_JSON
            ),
        },
    }

    if write_output:
        write_intent_plan(
            report
        )

    return report


def validate_target_instruments(
    targets: Iterable[
        PortfolioTarget
    ],
    *,
    require_registered: bool,
    require_paper_enabled: bool,
) -> None:
    for target in targets:
        if target.asset == "CASH":
            continue

        if require_paper_enabled:
            require_paper_instrument(
                target.asset
            )
            continue

        get_instrument(
            target.asset,
            require_registered=(
                require_registered
            ),
        )


def normalize_targets(
    targets: Iterable[
        PortfolioTarget
    ],
) -> list[PortfolioTarget]:
    result: dict[
        str,
        PortfolioTarget,
    ] = {}

    for target in targets:
        if target.asset == "CASH":
            continue

        if target.asset in result:
            raise ValueError(
                "DUPLICATE_TARGET_ASSET:"
                + target.asset
            )

        result[
            target.asset
        ] = target

    return [
        result[asset]
        for asset in sorted(
            result
        )
    ]


def apply_turnover_cap(
    lines: Sequence[
        RebalanceLine
    ],
    *,
    equity: float,
    policy: RebalancePolicy,
) -> list[RebalanceLine]:
    """Scale executable lines proportionally to the total-turnover limit."""
    executable_total = sum(
        abs(
            line.approved_notional_delta
        )
        for line in lines
        if not line.skipped
    )

    turnover_limit = (
        equity
        * policy.maximum_total_turnover
    )

    if (
        executable_total <= turnover_limit
        or executable_total <= 0
    ):
        return list(lines)

    scale = (
        turnover_limit
        / executable_total
    )

    result: list[
        RebalanceLine
    ] = []

    for line in lines:
        if line.skipped:
            result.append(line)
            continue

        scaled_notional = (
            line.approved_notional_delta
            * scale
        )

        instrument = get_instrument(
            line.asset,
            require_registered=(
                policy
                .require_registered_assets
            ),
        )

        precision = (
            instrument.quantity_precision
            if instrument is not None
            else policy.quantity_precision
        )

        multiplier = (
            instrument.contract_multiplier
            if instrument is not None
            else line.contract_multiplier
        )

        quantity = round(
            abs(
                scaled_notional
            )
            / (
                line.reference_price
                * multiplier
            ),
            precision,
        )

        if (
            abs(scaled_notional)
            < policy.minimum_order_notional
            or quantity <= 0
        ):
            result.append(
                RebalanceLine(
                    **{
                        **line.to_dict(),
                        "approved_notional_delta": 0.0,
                        "quantity": 0.0,
                        "skipped": True,
                        "skip_reason": (
                            "BELOW_MINIMUM_AFTER_TURNOVER_SCALING"
                        ),
                    }
                )
            )
            continue

        result.append(
            RebalanceLine(
                **{
                    **line.to_dict(),
                    "approved_notional_delta": (
                        scaled_notional
                    ),
                    "quantity": quantity,
                }
            )
        )

    return result


def load_portfolio_targets(
    *,
    report_path: Path = (
        DEFAULT_PORTFOLIO_REPORT
    ),
    prices: Mapping[
        str,
        float,
    ],
) -> list[PortfolioTarget]:
    """Load targets from common Atlas optimizer report shapes."""
    if not report_path.exists():
        raise FileNotFoundError(
            str(report_path)
        )

    payload = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    rows = extract_target_rows(
        payload
    )

    targets: list[
        PortfolioTarget
    ] = []

    for row in rows:
        asset = first_value(
            row,
            (
                "asset",
                "symbol",
                "ticker",
            ),
        )

        weight = first_value(
            row,
            (
                "target_weight",
                "weight",
                "portfolio_weight",
                "allocation",
            ),
        )

        if asset is None or weight is None:
            continue

        normalized_asset = normalize_symbol(
            asset
        )

        if normalized_asset == "CASH":
            continue

        price = prices.get(
            normalized_asset
        )

        if price is None:
            continue

        targets.append(
            PortfolioTarget(
                asset=normalized_asset,
                target_weight=float(
                    weight
                ),
                reference_price=float(
                    price
                ),
                source_rank=optional_float(
                    first_value(
                        row,
                        (
                            "rank",
                            "portfolio_rank",
                        ),
                    )
                ),
                source_label=str(
                    first_value(
                        row,
                        (
                            "label",
                            "classification",
                        ),
                    )
                    or ""
                ),
            )
        )

    if not targets:
        raise ValueError(
            "NO_PORTFOLIO_TARGETS_FOUND"
        )

    return normalize_targets(
        targets
    )


def extract_target_rows(
    payload: Any,
) -> list[Mapping[str, Any]]:
    if isinstance(
        payload,
        list,
    ):
        return [
            row
            for row in payload
            if isinstance(
                row,
                Mapping,
            )
        ]

    if not isinstance(
        payload,
        Mapping,
    ):
        return []

    candidate_keys = (
        "portfolio",
        "portfolio_rows",
        "allocations",
        "weights",
        "targets",
        "positions",
        "data",
    )

    for key in candidate_keys:
        value = payload.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return [
                row
                for row in value
                if isinstance(
                    row,
                    Mapping,
                )
            ]

        if isinstance(
            value,
            Mapping,
        ):
            nested = extract_target_rows(
                value
            )

            if nested:
                return nested

    for value in payload.values():
        if isinstance(
            value,
            Mapping,
        ):
            nested = extract_target_rows(
                value
            )

            if nested:
                return nested

    return []


def first_value(
    row: Mapping[str, Any],
    keys: Sequence[str],
) -> Any:
    for key in keys:
        if key in row:
            return row[key]

    return None


def optional_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def build_plan_id(
    *,
    targets: Sequence[
        PortfolioTarget
    ],
    account: AccountSnapshot,
    strategy_id: str,
    evidence_id: str,
    policy: RebalancePolicy,
) -> str:
    payload = {
        "targets": [
            target.to_dict()
            for target in targets
        ],
        "account": account.to_dict(),
        "strategy_id": strategy_id,
        "evidence_id": evidence_id,
        "policy": asdict(
            policy
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return (
        "PORTFOLIO-PLAN-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )


def write_intent_plan(
    report: Mapping[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        LATEST_INTENT_PLAN_JSON
        .with_suffix(
            ".json.tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            dict(report),
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        LATEST_INTENT_PLAN_JSON
    )


__all__ = [
    "DEFAULT_PORTFOLIO_REPORT",
    "LATEST_INTENT_PLAN_JSON",
    "PORTFOLIO_BRIDGE_VERSION",
    "PortfolioTarget",
    "RebalanceLine",
    "RebalancePolicy",
    "apply_turnover_cap",
    "build_portfolio_intent_plan",
    "extract_target_rows",
    "load_portfolio_targets",
    "normalize_targets",
    "validate_target_instruments",
]
