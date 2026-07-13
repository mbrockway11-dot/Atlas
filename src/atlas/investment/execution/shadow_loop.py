"""Restart-safe continuous Atlas shadow trading loop.

The loop is intentionally paper-only. It consumes previously generated
portfolio intents and executes them through the deterministic PaperBroker.
Any reconciliation, provenance, lifecycle, or safety failure halts the cycle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from atlas.investment.execution.account_store import (
    PAPER_ACCOUNT_JSON,
    account_from_mapping,
    load_paper_account,
    write_paper_account,
)
from atlas.investment.execution.contracts import (
    OrderIntent,
    OrderRecord,
    RiskLimits,
)
from atlas.investment.execution.lifecycle import (
    ORDER_STATE_JSON,
    ORDER_TRANSITIONS_JSONL,
    PaperOrderLifecycleStore,
)
from atlas.investment.execution.paper_broker import (
    PaperBrokerConfig,
)
from atlas.investment.execution.portfolio_bridge import (
    LATEST_INTENT_PLAN_JSON,
)
from atlas.investment.execution.provenance import (
    validate_execution_provenance,
)
from atlas.investment.execution.risk import (
    evaluate_order_intent,
)
from atlas.investment.execution.service import (
    run_paper_execution,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

SHADOW_CHECKPOINT_JSON = (
    OUTPUT_DIR
    / "shadow_cycle_checkpoint.json"
)

SHADOW_REPORT_JSON = (
    OUTPUT_DIR
    / "shadow_cycle_report.json"
)

SHADOW_HISTORY_JSONL = (
    OUTPUT_DIR
    / "shadow_cycle_history.jsonl"
)

SHADOW_LOOP_VERSION = "1.0.0"


def run_shadow_cycle(
    *,
    intent_plan_path: Path = (
        LATEST_INTENT_PLAN_JSON
    ),
    account_path: Path = (
        PAPER_ACCOUNT_JSON
    ),
    checkpoint_path: Path = (
        SHADOW_CHECKPOINT_JSON
    ),
    report_path: Path = (
        SHADOW_REPORT_JSON
    ),
    history_path: Path = (
        SHADOW_HISTORY_JSONL
    ),
    lifecycle_state_path: Path = (
        ORDER_STATE_JSON
    ),
    lifecycle_transitions_path: Path = (
        ORDER_TRANSITIONS_JSONL
    ),
    initial_cash: float = 10_000.0,
    limits: RiskLimits | None = None,
    broker_config: (
        PaperBrokerConfig | None
    ) = None,
    maximum_intents: int | None = None,
    resume: bool = True,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Execute one complete restart-safe paper shadow cycle."""
    plan = load_intent_plan(
        intent_plan_path
    )

    plan_id = str(
        plan.get(
            "plan_id",
            "",
        )
    )

    if not plan_id:
        raise RuntimeError(
            "SHADOW_PLAN_ID_MISSING"
        )

    intents = [
        intent_from_mapping(
            row
        )
        for row in plan.get(
            "intents",
            [],
        )
    ]

    account = load_paper_account(
        path=account_path,
        initial_cash=initial_cash,
    )

    lifecycle = (
        PaperOrderLifecycleStore(
            state_path=(
                lifecycle_state_path
            ),
            transitions_path=(
                lifecycle_transitions_path
            ),
        )
    )

    checkpoint = (
        load_shadow_checkpoint(
            checkpoint_path
        )
        if resume
        else {}
    )

    same_plan = bool(
        checkpoint.get(
            "plan_id"
        )
        == plan_id
    )

    completed_intent_ids = set(
        checkpoint.get(
            "completed_intent_ids",
            [],
        )
        if same_plan
        else []
    )

    failed_intent_ids = set(
        checkpoint.get(
            "failed_intent_ids",
            [],
        )
        if same_plan
        else []
    )

    cycle_id = (
        str(
            checkpoint.get(
                "cycle_id",
                "",
            )
        )
        if same_plan
        and checkpoint.get(
            "status"
        )
        in {
            "RUNNING",
            "HALTED",
        }
        else build_cycle_id(
            plan_id
        )
    )

    started_at = (
        str(
            checkpoint.get(
                "started_at",
                "",
            )
        )
        if same_plan
        and checkpoint.get(
            "started_at"
        )
        else utc_now()
    )

    effective_limits = (
        limits
        or RiskLimits()
    )

    results: list[
        dict[str, Any]
    ] = []

    halted = False
    halt_reason = ""

    pending = [
        intent
        for intent in intents
        if intent.intent_id
        not in completed_intent_ids
    ]

    if maximum_intents is not None:
        pending = pending[
            :max(
                0,
                int(maximum_intents),
            )
        ]

    write_checkpoint_if_enabled(
        write_outputs=write_outputs,
        checkpoint_path=(
            checkpoint_path
        ),
        payload=build_checkpoint(
            cycle_id=cycle_id,
            plan_id=plan_id,
            status="RUNNING",
            started_at=started_at,
            completed_intent_ids=(
                completed_intent_ids
            ),
            failed_intent_ids=(
                failed_intent_ids
            ),
            account=account,
            halt_reason="",
        ),
    )

    for intent in pending:
        result = execute_shadow_intent(
            intent=intent,
            account=account,
            limits=effective_limits,
            broker_config=(
                broker_config
            ),
            lifecycle=lifecycle,
        )

        results.append(result)

        if not result["success"]:
            halted = True
            halt_reason = str(
                result.get(
                    "halt_reason",
                    "SHADOW_EXECUTION_FAILED",
                )
            )

            failed_intent_ids.add(
                intent.intent_id
            )

            write_checkpoint_if_enabled(
                write_outputs=(
                    write_outputs
                ),
                checkpoint_path=(
                    checkpoint_path
                ),
                payload=build_checkpoint(
                    cycle_id=cycle_id,
                    plan_id=plan_id,
                    status="HALTED",
                    started_at=(
                        started_at
                    ),
                    completed_intent_ids=(
                        completed_intent_ids
                    ),
                    failed_intent_ids=(
                        failed_intent_ids
                    ),
                    account=account,
                    halt_reason=(
                        halt_reason
                    ),
                ),
            )

            break

        account = account_from_mapping(
            result["execution"][
                "account_after"
            ]
        )

        completed_intent_ids.add(
            intent.intent_id
        )

        if write_outputs:
            write_paper_account(
                account,
                path=account_path,
                source_execution_id=str(
                    result["execution"].get(
                        "execution_id",
                        "",
                    )
                ),
            )

        write_checkpoint_if_enabled(
            write_outputs=write_outputs,
            checkpoint_path=(
                checkpoint_path
            ),
            payload=build_checkpoint(
                cycle_id=cycle_id,
                plan_id=plan_id,
                status="RUNNING",
                started_at=started_at,
                completed_intent_ids=(
                    completed_intent_ids
                ),
                failed_intent_ids=(
                    failed_intent_ids
                ),
                account=account,
                halt_reason="",
            ),
        )

    all_completed = bool(
        len(completed_intent_ids)
        >= len(intents)
    )

    status = (
        "HALTED"
        if halted
        else (
            "COMPLETED"
            if all_completed
            else "PAUSED"
        )
    )

    completed_at = utc_now()

    report = {
        "success": bool(
            not halted
        ),
        "version": (
            SHADOW_LOOP_VERSION
        ),
        "mode": "SHADOW_PAPER",
        "live_execution": False,
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "started_at": (
            started_at
        ),
        "completed_at": (
            completed_at
        ),
        "status": status,
        "halt_reason": (
            halt_reason
        ),
        "resumed": bool(
            same_plan
            and resume
        ),
        "account_before": (
            load_paper_account(
                path=account_path,
                initial_cash=initial_cash,
            ).to_dict()
            if not results
            else results[0][
                "execution"
            ][
                "account_before"
            ]
        ),
        "account_after": (
            account.to_dict()
        ),
        "completed_intent_ids": sorted(
            completed_intent_ids
        ),
        "failed_intent_ids": sorted(
            failed_intent_ids
        ),
        "results": results,
        "counts": {
            "plan_intents": len(
                intents
            ),
            "processed_this_run": len(
                results
            ),
            "completed_total": len(
                completed_intent_ids
            ),
            "failed_total": len(
                failed_intent_ids
            ),
            "remaining": max(
                0,
                len(intents)
                - len(
                    completed_intent_ids
                ),
            ),
        },
        "contract": {
            "paper_only": True,
            "shadow_mode": True,
            "live_execution": False,
            "live_credentials_used": False,
            "halts_on_reconciliation_failure": True,
            "halts_on_provenance_failure": True,
            "persistent_account": True,
            "restart_safe": True,
        },
        "paths": {
            "intent_plan": str(
                intent_plan_path
            ),
            "account": str(
                account_path
            ),
            "checkpoint": str(
                checkpoint_path
            ),
            "report": str(
                report_path
            ),
            "history": str(
                history_path
            ),
        },
    }

    final_checkpoint = (
        build_checkpoint(
            cycle_id=cycle_id,
            plan_id=plan_id,
            status=status,
            started_at=started_at,
            completed_intent_ids=(
                completed_intent_ids
            ),
            failed_intent_ids=(
                failed_intent_ids
            ),
            account=account,
            halt_reason=halt_reason,
        )
    )

    if write_outputs:
        write_shadow_json(
            report_path,
            report,
        )

        write_shadow_json(
            checkpoint_path,
            final_checkpoint,
        )

        append_shadow_history(
            history_path,
            report,
        )

    return report


def execute_shadow_intent(
    *,
    intent: OrderIntent,
    account,
    limits: RiskLimits,
    broker_config: (
        PaperBrokerConfig | None
    ),
    lifecycle: (
        PaperOrderLifecycleStore
    ),
) -> dict[str, Any]:
    """Execute one intent and verify all safety contracts."""
    try:
        lifecycle_record = (
            lifecycle.create(
                intent
            )
        )
    except ValueError as error:
        if str(error).startswith(
            "DUPLICATE_ACTIVE_INTENT"
        ):
            return {
                "success": False,
                "intent_id": (
                    intent.intent_id
                ),
                "halt_reason": (
                    "DUPLICATE_ACTIVE_INTENT"
                ),
                "error": str(error),
            }

        raise

    risk = evaluate_order_intent(
        intent,
        account,
        limits,
    )

    lifecycle_record = (
        lifecycle.apply_risk_decision(
            intent.intent_id,
            risk,
        )
    )

    if risk.approved:
        lifecycle_record = (
            lifecycle.transition(
                intent.intent_id,
                "SUBMITTED",
                reason=(
                    "SHADOW_PAPER_SUBMITTED"
                ),
            )
        )

    execution = run_paper_execution(
        intent=intent,
        account=account,
        limits=limits,
        broker_config=(
            broker_config
        ),
        write_outputs=True,
    )

    if bool(
        execution.get(
            "live_execution",
            False,
        )
    ):
        return {
            "success": False,
            "intent_id": (
                intent.intent_id
            ),
            "halt_reason": (
                "LIVE_EXECUTION_BOUNDARY_VIOLATION"
            ),
            "execution": execution,
        }

    if not bool(
        execution.get(
            "reconciliation",
            {},
        ).get(
            "success",
            False,
        )
    ):
        return {
            "success": False,
            "intent_id": (
                intent.intent_id
            ),
            "halt_reason": (
                "RECONCILIATION_FAILED"
            ),
            "execution": execution,
        }

    provenance = (
        validate_execution_provenance()
    )

    if not provenance["valid"]:
        return {
            "success": False,
            "intent_id": (
                intent.intent_id
            ),
            "halt_reason": (
                "PROVENANCE_CHAIN_INVALID"
            ),
            "provenance": (
                provenance
            ),
            "execution": execution,
        }

    execution_risk = execution.get(
        "risk",
        {},
    )

    if bool(
        execution_risk.get(
            "approved",
            False,
        )
    ) != risk.approved:
        return {
            "success": False,
            "intent_id": (
                intent.intent_id
            ),
            "halt_reason": (
                "RISK_DECISION_PARITY_FAILURE"
            ),
            "execution": execution,
        }

    order_payload = execution.get(
        "order",
        {},
    )

    if risk.approved:
        order = OrderRecord(
            order_id=str(
                order_payload.get(
                    "order_id",
                    "",
                )
            ),
            intent_id=str(
                order_payload.get(
                    "intent_id",
                    "",
                )
            ),
            asset=str(
                order_payload.get(
                    "asset",
                    "",
                )
            ),
            side=str(
                order_payload.get(
                    "side",
                    "",
                )
            ),
            requested_quantity=float(
                order_payload.get(
                    "requested_quantity",
                    0.0,
                )
            ),
            filled_quantity=float(
                order_payload.get(
                    "filled_quantity",
                    0.0,
                )
            ),
            remaining_quantity=float(
                order_payload.get(
                    "remaining_quantity",
                    0.0,
                )
            ),
            status=str(
                order_payload.get(
                    "status",
                    "",
                )
            ),
            submitted_at=str(
                order_payload.get(
                    "submitted_at",
                    "",
                )
            ),
            completed_at=str(
                order_payload.get(
                    "completed_at",
                    "",
                )
            ),
            average_fill_price=float(
                order_payload.get(
                    "average_fill_price",
                    0.0,
                )
            ),
            fee_paid=float(
                order_payload.get(
                    "fee_paid",
                    0.0,
                )
            ),
            rejection_reason=str(
                order_payload.get(
                    "rejection_reason",
                    "",
                )
            ),
        )

        lifecycle_record = (
            lifecycle.apply_order_record(
                intent.intent_id,
                order,
            )
        )

    lifecycle_validation = (
        lifecycle
        .validate_transition_chain()
    )

    if not lifecycle_validation[
        "valid"
    ]:
        return {
            "success": False,
            "intent_id": (
                intent.intent_id
            ),
            "halt_reason": (
                "LIFECYCLE_CHAIN_INVALID"
            ),
            "execution": execution,
            "lifecycle_validation": (
                lifecycle_validation
            ),
        }

    successful_terminal = bool(
        lifecycle_record.state
        in {
            "FILLED",
            "RISK_REJECTED",
            "CANCELLED",
            "REJECTED",
        }
    )

    return {
        "success": bool(
            successful_terminal
        ),
        "intent_id": (
            intent.intent_id
        ),
        "risk_approved": (
            risk.approved
        ),
        "lifecycle_state": (
            lifecycle_record.state
        ),
        "execution": execution,
        "provenance": provenance,
        "lifecycle_validation": (
            lifecycle_validation
        ),
        "halt_reason": (
            ""
            if successful_terminal
            else "NONTERMINAL_EXECUTION_STATE"
        ),
    }


def load_intent_plan(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "SHADOW_INTENT_PLAN_INVALID_JSON"
        ) from error

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "SHADOW_INTENT_PLAN_INVALID"
        )

    contract = payload.get(
        "contract",
        {},
    )

    if bool(
        payload.get(
            "live_execution",
            False,
        )
    ):
        raise RuntimeError(
            "SHADOW_PLAN_LIVE_EXECUTION_FORBIDDEN"
        )

    if bool(
        contract.get(
            "submits_orders",
            False,
        )
    ):
        raise RuntimeError(
            "SHADOW_PLAN_DIRECT_SUBMISSION_FORBIDDEN"
        )

    return payload


def intent_from_mapping(
    row: Mapping[str, Any],
) -> OrderIntent:
    return OrderIntent(
        asset=str(
            row["asset"]
        ),
        side=str(
            row["side"]
        ),
        quantity=float(
            row["quantity"]
        ),
        reference_price=float(
            row["reference_price"]
        ),
        strategy_id=str(
            row["strategy_id"]
        ),
        evidence_id=str(
            row["evidence_id"]
        ),
        order_type=str(
            row.get(
                "order_type",
                "MARKET",
            )
        ),
        limit_price=(
            float(
                row["limit_price"]
            )
            if row.get(
                "limit_price"
            )
            is not None
            else None
        ),
        time_in_force=str(
            row.get(
                "time_in_force",
                "IOC",
            )
        ),
        maximum_slippage_bps=float(
            row.get(
                "maximum_slippage_bps",
                25.0,
            )
        ),
        reduce_only=bool(
            row.get(
                "reduce_only",
                False,
            )
        ),
        expires_at=str(
            row.get(
                "expires_at",
                "",
            )
        ),
        created_at=str(
            row.get(
                "created_at",
                "",
            )
        ),
        intent_id=str(
            row.get(
                "intent_id",
                "",
            )
        ),
    )


def load_shadow_checkpoint(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    return (
        payload
        if isinstance(
            payload,
            dict,
        )
        else {}
    )


def build_checkpoint(
    *,
    cycle_id: str,
    plan_id: str,
    status: str,
    started_at: str,
    completed_intent_ids,
    failed_intent_ids,
    account,
    halt_reason: str,
) -> dict[str, Any]:
    return {
        "version": (
            SHADOW_LOOP_VERSION
        ),
        "cycle_id": cycle_id,
        "plan_id": plan_id,
        "status": status,
        "started_at": (
            started_at
        ),
        "updated_at": utc_now(),
        "completed_intent_ids": sorted(
            completed_intent_ids
        ),
        "failed_intent_ids": sorted(
            failed_intent_ids
        ),
        "halt_reason": (
            halt_reason
        ),
        "account": (
            account.to_dict()
        ),
        "paper_only": True,
        "live_execution": False,
    }


def write_checkpoint_if_enabled(
    *,
    write_outputs: bool,
    checkpoint_path: Path,
    payload: Mapping[str, Any],
) -> None:
    if write_outputs:
        write_shadow_json(
            checkpoint_path,
            payload,
        )


def write_shadow_json(
    path: Path,
    payload: Mapping[str, Any],
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


def append_shadow_history(
    path: Path,
    report: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = {
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
        "status": (
            report.get(
                "status",
                "",
            )
        ),
        "success": bool(
            report.get(
                "success",
                False,
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
        "counts": (
            report.get(
                "counts",
                {},
            )
        ),
        "halt_reason": (
            report.get(
                "halt_reason",
                "",
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


def build_cycle_id(
    plan_id: str,
) -> str:
    payload = (
        plan_id
        + "|"
        + utc_now()
    ).encode("utf-8")

    return (
        "SHADOW-"
        + hashlib.sha256(
            payload
        ).hexdigest()[:24]
    )


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


__all__ = [
    "SHADOW_CHECKPOINT_JSON",
    "SHADOW_HISTORY_JSONL",
    "SHADOW_LOOP_VERSION",
    "SHADOW_REPORT_JSON",
    "execute_shadow_intent",
    "load_shadow_checkpoint",
    "run_shadow_cycle",
]
