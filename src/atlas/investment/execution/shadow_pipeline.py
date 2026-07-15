"""End-to-end Atlas paper shadow portfolio pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.execution.account_store import (
    PAPER_ACCOUNT_JSON,
    account_from_mapping,
    load_paper_account,
)
from atlas.investment.execution.attribution import (
    build_shadow_attribution,
)
from atlas.investment.execution.contracts import (
    RiskLimits,
)
from atlas.investment.execution.paper_broker import (
    PaperBrokerConfig,
)
from atlas.investment.execution.portfolio_bridge import (
    LATEST_INTENT_PLAN_JSON,
    PortfolioTarget,
    RebalancePolicy,
    build_portfolio_intent_plan,
)
from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)
from atlas.investment.market_data import (
    LATEST_MARKET_SNAPSHOT_JSON,
    load_market_snapshot,
    reference_prices_from_snapshot,
    validate_market_data_audit,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

SHADOW_PIPELINE_REPORT_JSON = (
    OUTPUT_DIR
    / "shadow_pipeline_report.json"
)

SHADOW_PIPELINE_HISTORY_JSONL = (
    OUTPUT_DIR
    / "shadow_pipeline_history.jsonl"
)

SHADOW_PIPELINE_CHECKPOINT_JSON = (
    OUTPUT_DIR
    / "shadow_pipeline_checkpoint.json"
)

SHADOW_PIPELINE_VERSION = "1.0.0"


def run_shadow_pipeline(
    *,
    targets_path: Path,
    snapshot_path: Path = (
        LATEST_MARKET_SNAPSHOT_JSON
    ),
    account_path: Path = (
        PAPER_ACCOUNT_JSON
    ),
    intent_plan_path: Path = (
        LATEST_INTENT_PLAN_JSON
    ),
    report_path: Path = (
        SHADOW_PIPELINE_REPORT_JSON
    ),
    history_path: Path = (
        SHADOW_PIPELINE_HISTORY_JSONL
    ),
    checkpoint_path: Path = (
        SHADOW_PIPELINE_CHECKPOINT_JSON
    ),
    strategy_id: str = (
        "atlas-shadow-portfolio"
    ),
    evidence_id: str = "",
    initial_cash: float = 10_000.0,
    policy: RebalancePolicy | None = None,
    limits: RiskLimits | None = None,
    broker_config: (
        PaperBrokerConfig | None
    ) = None,
    maximum_intents: int | None = None,
    resume: bool = True,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run market snapshot ? intent plan ? shadow execution ? attribution."""
    snapshot = (
        load_market_snapshot(
            snapshot_path
        )
    )

    if not snapshot:
        raise RuntimeError(
            "MARKET_SNAPSHOT_MISSING"
        )

    if not bool(
        snapshot.get(
            "success",
            False,
        )
    ):
        raise RuntimeError(
            "MARKET_SNAPSHOT_INVALID"
        )

    market_contract = snapshot.get(
        "contract",
        {}
    )

    if bool(
        market_contract.get(
            "live_execution",
            False,
        )
    ):
        raise RuntimeError(
            "MARKET_SNAPSHOT_LIVE_EXECUTION_FORBIDDEN"
        )

    if bool(
        market_contract.get(
            "credentials_used",
            False,
        )
    ):
        raise RuntimeError(
            "MARKET_SNAPSHOT_CREDENTIAL_BOUNDARY_VIOLATION"
        )

    audit = (
        validate_market_data_audit()
    )

    if not audit["valid"]:
        raise RuntimeError(
            "MARKET_DATA_AUDIT_INVALID:"
            + "|".join(
                audit["errors"]
            )
        )

    prices = (
        reference_prices_from_snapshot(
            snapshot
        )
    )

    targets_payload = load_target_allocations(
        targets_path
    )

    targets = build_targets(
        targets_payload,
        prices,
    )

    account_before = (
        load_paper_account(
            path=account_path,
            initial_cash=initial_cash,
        )
    )

    snapshot_id = str(
        snapshot.get(
            "snapshot_id",
            "",
        )
    )

    effective_evidence_id = (
        evidence_id.strip()
        or snapshot_id
    )

    pipeline_id = (
        build_pipeline_id(
            snapshot_id=snapshot_id,
            targets=targets,
            account=(
                account_before.to_dict()
            ),
            strategy_id=strategy_id,
            evidence_id=(
                effective_evidence_id
            ),
        )
    )

    started_at = (
        datetime.now(
            UTC
        ).isoformat()
    )

    if write_outputs:
        write_json_atomic(
            checkpoint_path,
            {
                "pipeline_id": (
                    pipeline_id
                ),
                "status": "RUNNING",
                "started_at": (
                    started_at
                ),
                "snapshot_id": (
                    snapshot_id
                ),
                "paper_only": True,
                "live_execution": False,
            },
        )

    intent_plan = (
        build_portfolio_intent_plan(
            targets=targets,
            account=account_before,
            strategy_id=(
                strategy_id
            ),
            evidence_id=(
                effective_evidence_id
            ),
            policy=policy,
            write_output=(
                write_outputs
            ),
        )
    )

    if write_outputs:
        write_json_atomic(
            intent_plan_path,
            intent_plan,
        )

    shadow_report = (
        run_shadow_cycle(
            intent_plan_path=(
                intent_plan_path
            ),
            account_path=(
                account_path
            ),
            initial_cash=(
                initial_cash
            ),
            limits=limits,
            broker_config=(
                broker_config
            ),
            maximum_intents=(
                maximum_intents
            ),
            resume=resume,
            write_outputs=(
                write_outputs
            ),
        )
    )

    account_after = (
        account_from_mapping(
            shadow_report[
                "account_after"
            ]
        )
    )

    attribution = (
        build_shadow_attribution(
            cycle_id=str(
                shadow_report.get(
                    "cycle_id",
                    "",
                )
            ),
            plan_id=str(
                intent_plan.get(
                    "plan_id",
                    "",
                )
            ),
            snapshot_id=(
                snapshot_id
            ),
            account_before=(
                account_before
            ),
            account_after=(
                account_after
            ),
            reference_prices=prices,
            execution_results=list(
                shadow_report.get(
                    "results",
                    [],
                )
            ),
            write_output=(
                write_outputs
            ),
        )
    )

    errors: list[str] = []

    if not shadow_report.get(
        "success",
        False,
    ):
        errors.append(
            "SHADOW_CYCLE_FAILED:"
            + str(
                shadow_report.get(
                    "halt_reason",
                    "",
                )
            )
        )

    if not attribution.get(
        "success",
        False,
    ):
        errors.extend(
            str(error)
            for error
            in attribution.get(
                "errors",
                [],
            )
        )

    status = (
        "HALTED"
        if errors
        else str(
            shadow_report.get(
                "status",
                "UNKNOWN",
            )
        )
    )

    completed_at = (
        datetime.now(
            UTC
        ).isoformat()
    )

    report = {
        "success": not errors,
        "version": (
            SHADOW_PIPELINE_VERSION
        ),
        "pipeline_id": (
            pipeline_id
        ),
        "status": status,
        "started_at": (
            started_at
        ),
        "completed_at": (
            completed_at
        ),
        "snapshot_id": (
            snapshot_id
        ),
        "plan_id": str(
            intent_plan.get(
                "plan_id",
                "",
            )
        ),
        "cycle_id": str(
            shadow_report.get(
                "cycle_id",
                "",
            )
        ),
        "attribution_id": str(
            attribution.get(
                "attribution_id",
                "",
            )
        ),
        "market_data": {
            "snapshot_id": (
                snapshot_id
            ),
            "resolved_symbols": (
                snapshot.get(
                    "counts",
                    {},
                ).get(
                    "resolved",
                    0,
                )
            ),
            "audit_valid": (
                audit["valid"]
            ),
        },
        "intent_plan": {
            "plan_id": (
                intent_plan.get(
                    "plan_id",
                    "",
                )
            ),
            "counts": (
                intent_plan.get(
                    "counts",
                    {},
                )
            ),
            "turnover_weight": (
                intent_plan.get(
                    "total_turnover_weight",
                    0.0,
                )
            ),
        },
        "shadow_cycle": {
            "status": (
                shadow_report.get(
                    "status",
                    "",
                )
            ),
            "counts": (
                shadow_report.get(
                    "counts",
                    {},
                )
            ),
            "halt_reason": (
                shadow_report.get(
                    "halt_reason",
                    "",
                )
            ),
        },
        "performance": (
            attribution.get(
                "performance",
                {},
            )
        ),
        "asset_attribution": (
            attribution.get(
                "asset_attribution",
                [],
            )
        ),
        "asset_class_attribution": (
            attribution.get(
                "asset_class_attribution",
                [],
            )
        ),
        "errors": errors,
        "contract": {
            "paper_only": True,
            "provider_neutral_market_data": True,
            "broker_neutral_intents": True,
            "restart_safe_execution": True,
            "mark_to_market": True,
            "performance_attribution": True,
            "credentials_used": False,
            "live_execution": False,
        },
        "paths": {
            "targets": str(
                targets_path
            ),
            "market_snapshot": str(
                snapshot_path
            ),
            "intent_plan": str(
                intent_plan_path
            ),
            "account": str(
                account_path
            ),
            "report": str(
                report_path
            ),
            "checkpoint": str(
                checkpoint_path
            ),
        },
    }

    checkpoint = {
        "pipeline_id": (
            pipeline_id
        ),
        "status": status,
        "started_at": (
            started_at
        ),
        "completed_at": (
            completed_at
        ),
        "snapshot_id": (
            snapshot_id
        ),
        "plan_id": report[
            "plan_id"
        ],
        "cycle_id": report[
            "cycle_id"
        ],
        "attribution_id": (
            report[
                "attribution_id"
            ]
        ),
        "errors": errors,
        "paper_only": True,
        "live_execution": False,
    }

    if write_outputs:
        write_json_atomic(
            report_path,
            report,
        )

        write_json_atomic(
            checkpoint_path,
            checkpoint,
        )

        append_history(
            history_path,
            report,
        )

    return report


def load_target_allocations(
    path: Path,
) -> dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    rows = (
        payload.get(
            "targets",
            payload.get(
                "portfolio_rows",
                payload.get(
                    "portfolio",
                    payload,
                ),
            ),
        )
        if isinstance(
            payload,
            dict,
        )
        else payload
    )

    result: dict[
        str,
        float,
    ] = {}

    if isinstance(
        rows,
        Mapping,
    ):
        iterator = (
            rows.items()
        )
    elif isinstance(
        rows,
        list,
    ):
        iterator = (
            (
                row.get(
                    "asset"
                ),
                row.get(
                    "target_weight",
                    row.get(
                        "weight"
                    ),
                ),
            )
            for row
            in rows
            if isinstance(
                row,
                Mapping,
            )
        )
    else:
        raise ValueError(
            "TARGET_ALLOCATION_FORMAT_INVALID"
        )

    for asset, weight in iterator:
        if asset is None:
            continue

        normalized_asset = str(
            asset
        ).strip().upper()

        number = float(
            weight
        )

        if number < 0:
            raise ValueError(
                "TARGET_WEIGHT_NEGATIVE:"
                + normalized_asset
            )

        if normalized_asset in result:
            raise ValueError(
                "DUPLICATE_TARGET:"
                + normalized_asset
            )

        result[
            normalized_asset
        ] = number

    if not result:
        raise ValueError(
            "TARGET_ALLOCATIONS_EMPTY"
        )

    return result


def build_targets(
    allocations: Mapping[
        str,
        float,
    ],
    reference_prices: Mapping[
        str,
        float,
    ],
) -> list[PortfolioTarget]:
    targets: list[
        PortfolioTarget
    ] = []

    missing: list[str] = []

    for asset, weight in sorted(
        allocations.items()
    ):
        if asset == "CASH":
            continue

        price = reference_prices.get(
            asset
        )

        if price is None:
            missing.append(
                asset
            )
            continue

        targets.append(
            PortfolioTarget(
                asset=asset,
                target_weight=float(
                    weight
                ),
                reference_price=float(
                    price
                ),
            )
        )

    if missing:
        raise ValueError(
            "TARGET_REFERENCE_PRICE_MISSING:"
            + ",".join(
                missing
            )
        )

    return targets


def build_pipeline_id(
    *,
    snapshot_id: str,
    targets,
    account: Mapping[
        str,
        Any,
    ],
    strategy_id: str,
    evidence_id: str,
) -> str:
    payload = {
        "snapshot_id": (
            snapshot_id
        ),
        "targets": [
            target.to_dict()
            for target
            in targets
        ],
        "account": dict(
            account
        ),
        "strategy_id": (
            strategy_id
        ),
        "evidence_id": (
            evidence_id
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
        "SHADOW-PIPELINE-"
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
        "pipeline_id": (
            report.get(
                "pipeline_id",
                "",
            )
        ),
        "status": (
            report.get(
                "status",
                "",
            )
        ),
        "started_at": (
            report.get(
                "started_at",
                "",
            )
        ),
        "completed_at": (
            report.get(
                "completed_at",
                "",
            )
        ),
        "snapshot_id": (
            report.get(
                "snapshot_id",
                "",
            )
        ),
        "plan_id": (
            report.get(
                "plan_id",
                "",
            )
        ),
        "cycle_id": (
            report.get(
                "cycle_id",
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
    "SHADOW_PIPELINE_CHECKPOINT_JSON",
    "SHADOW_PIPELINE_HISTORY_JSONL",
    "SHADOW_PIPELINE_REPORT_JSON",
    "SHADOW_PIPELINE_VERSION",
    "build_targets",
    "load_target_allocations",
    "run_shadow_pipeline",
]
