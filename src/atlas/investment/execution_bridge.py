"""Canonical LYFE-to-Atlas execution orchestration bridge.

Connects existing Atlas components without adding strategy or broker logic:

LYFE instruction
    -> portfolio target mapping
    -> OrderIntent generation
    -> pre-trade risk
    -> paper execution or registered broker submission
    -> provenance
    -> bridge report

Live execution remains controlled by the selected broker adapter and its
execution-mode gate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.brokers import (
    DEFAULT_BROKER_PROVIDER,
    BrokerAdapter,
    BrokerOrderRequest,
    BrokerOrderType,
    BrokerSide,
    BrokerTimeInForce,
    default_registry,
)
from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    RebalancePolicy,
    RiskLimits,
    account_from_mapping,
    evaluate_order_intent,
    record_execution_events,
    run_paper_execution,
)
from atlas.investment.lyfe_bridge.contracts import (
    AtlasStrategyInstruction,
)
from atlas.investment.lyfe_bridge.portfolio_intent import (
    build_lyfe_portfolio_intent_plan,
)


EXECUTION_BRIDGE_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_execution_bridge"
)

LATEST_REPORT_JSON = (
    OUTPUT_DIR
    / "execution_bridge_report.json"
)

HISTORY_JSONL = (
    OUTPUT_DIR
    / "execution_bridge_history.jsonl"
)


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def execute_lyfe_instruction(
    instruction: AtlasStrategyInstruction,
    *,
    reference_price: float,
    account: AccountSnapshot,
    provider: str = "paper",
    human_approved: bool = False,
    limits: RiskLimits | None = None,
    rebalance_policy: RebalancePolicy | None = None,
    broker_kwargs: Mapping[str, Any] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Execute one validated LYFE instruction through Atlas.

    Supported routes:

    - ``paper``:
      Uses Atlas's canonical paper execution service, including fills,
      account mutation, reconciliation, ledger, and provenance.

    - any registered broker provider:
      Uses ``default_registry`` and submits provider-neutral
      ``BrokerOrderRequest`` objects. Broker safety gates remain authoritative.

    Human approval is required before any generated order may be submitted.
    Non-executable LYFE mappings return a successful blocked/no-op report.
    """
    effective_limits = (
        limits
        or RiskLimits()
    )

    effective_broker_kwargs = dict(
        broker_kwargs
        or {}
    )

    requested_provider = str(
        provider
        or "paper"
    ).strip().lower()

    if not requested_provider:
        raise ValueError(
            "provider is required."
        )

    started_at = utc_now()

    intent_plan = (
        build_lyfe_portfolio_intent_plan(
            instruction,
            reference_price=(
                reference_price
            ),
            account=account,
            policy=rebalance_policy,
            write_output=(
                write_outputs
            ),
        )
    )

    order_intents = [
        order_intent_from_mapping(
            row
        )
        for row in intent_plan.get(
            "intents",
            [],
        )
    ]

    bridge_id = build_bridge_id(
        instruction=instruction,
        intent_plan=intent_plan,
        provider=requested_provider,
    )

    approval_required = bool(
        instruction.requires_human_approval
    )

    approval_satisfied = bool(
        human_approved
    )

    if (
        approval_required
        and not approval_satisfied
        and order_intents
    ):
        report = build_bridge_report(
            bridge_id=bridge_id,
            started_at=started_at,
            instruction=instruction,
            provider=requested_provider,
            human_approved=False,
            intent_plan=intent_plan,
            order_intents=order_intents,
            execution_results=[],
            account_before=account,
            account_after=account,
            status="AWAITING_HUMAN_APPROVAL",
            success=False,
            execution_blocked=True,
            errors=[
                "HUMAN_APPROVAL_REQUIRED",
            ],
        )

        if write_outputs:
            write_bridge_outputs(
                report
            )

        return report

    if (
        intent_plan.get(
            "execution_blocked",
            False,
        )
        or not order_intents
    ):
        mapping = (
            intent_plan.get(
                "lyfe_mapping",
                intent_plan.get(
                    "mapping",
                    {},
                ),
            )
        )

        status = str(
            mapping.get(
                "status",
                "NO_EXECUTABLE_INTENTS",
            )
        )

        report = build_bridge_report(
            bridge_id=bridge_id,
            started_at=started_at,
            instruction=instruction,
            provider=requested_provider,
            human_approved=(
                approval_satisfied
            ),
            intent_plan=intent_plan,
            order_intents=order_intents,
            execution_results=[],
            account_before=account,
            account_after=account,
            status=status,
            success=True,
            execution_blocked=True,
            errors=[],
        )

        if write_outputs:
            write_bridge_outputs(
                report
            )

        return report

    if requested_provider == "paper":
        execution_results, final_account = (
            execute_with_paper_service(
                order_intents,
                account=account,
                limits=effective_limits,
                write_outputs=(
                    write_outputs
                ),
            )
        )
    else:
        execution_results, final_account = (
            execute_with_registered_broker(
                order_intents,
                account=account,
                limits=effective_limits,
                provider=(
                    requested_provider
                ),
                broker_kwargs=(
                    effective_broker_kwargs
                ),
                bridge_id=bridge_id,
                write_outputs=(
                    write_outputs
                ),
            )
        )

    success = bool(
        execution_results
        and all(
            result.get(
                "success",
                False,
            )
            for result
            in execution_results
        )
    )

    errors = [
        str(error)
        for result
        in execution_results
        for error
        in result.get(
            "errors",
            [],
        )
    ]

    if success:
        status = "COMPLETED"
    elif any(
        result.get(
            "status",
        ) == "RISK_REJECTED"
        for result
        in execution_results
    ):
        status = "RISK_REJECTED"
    else:
        status = "FAILED"

    report = build_bridge_report(
        bridge_id=bridge_id,
        started_at=started_at,
        instruction=instruction,
        provider=requested_provider,
        human_approved=(
            approval_satisfied
        ),
        intent_plan=intent_plan,
        order_intents=order_intents,
        execution_results=(
            execution_results
        ),
        account_before=account,
        account_after=final_account,
        status=status,
        success=success,
        execution_blocked=False,
        errors=errors,
    )

    if write_outputs:
        write_bridge_outputs(
            report
        )

    return report


def execute_with_paper_service(
    intents: list[OrderIntent],
    *,
    account: AccountSnapshot,
    limits: RiskLimits,
    write_outputs: bool,
) -> tuple[
    list[dict[str, Any]],
    AccountSnapshot,
]:
    """Execute intents sequentially through the canonical paper service."""
    results: list[
        dict[str, Any]
    ] = []

    current_account = account

    for intent in intents:
        execution = run_paper_execution(
            intent=intent,
            account=current_account,
            limits=limits,
            write_outputs=(
                write_outputs
            ),
        )

        results.append({
            "success": bool(
                execution.get(
                    "success",
                    False,
                )
            ),
            "status": (
                "COMPLETED"
                if execution.get(
                    "success",
                    False,
                )
                else "REJECTED"
            ),
            "provider": "paper",
            "intent_id": (
                intent.intent_id
            ),
            "risk": execution.get(
                "risk",
                {},
            ),
            "order": execution.get(
                "order",
                {},
            ),
            "fills": execution.get(
                "fills",
                [],
            ),
            "execution_id": (
                execution.get(
                    "execution_id",
                    "",
                )
            ),
            "reconciliation": (
                execution.get(
                    "reconciliation",
                    {},
                )
            ),
            "provenance": (
                execution.get(
                    "provenance",
                    {},
                )
            ),
            "errors": (
                []
                if execution.get(
                    "success",
                    False,
                )
                else [
                    str(code)
                    for code
                    in execution.get(
                        "risk",
                        {},
                    ).get(
                        "reason_codes",
                        [],
                    )
                ]
            ),
        })

        account_after = execution.get(
            "account_after"
        )

        if isinstance(
            account_after,
            Mapping,
        ):
            current_account = (
                account_from_mapping(
                    account_after
                )
            )

    return (
        results,
        current_account,
    )


def execute_with_registered_broker(
    intents: list[OrderIntent],
    *,
    account: AccountSnapshot,
    limits: RiskLimits,
    provider: str,
    broker_kwargs: Mapping[str, Any],
    bridge_id: str,
    write_outputs: bool,
) -> tuple[
    list[dict[str, Any]],
    AccountSnapshot,
]:
    """Risk-check and submit intents through a registered broker adapter."""
    broker = default_registry.create(
        provider,
        **dict(
            broker_kwargs
        ),
    )

    if not isinstance(
        broker,
        BrokerAdapter,
    ):
        raise TypeError(
            "Broker registry returned an invalid adapter."
        )

    health = broker.health_check()

    results: list[
        dict[str, Any]
    ] = []

    for intent in intents:
        risk = evaluate_order_intent(
            intent,
            account,
            limits,
        )

        if not risk.approved:
            result = {
                "success": False,
                "status": (
                    "RISK_REJECTED"
                ),
                "provider": provider,
                "intent_id": (
                    intent.intent_id
                ),
                "risk": risk.to_dict(),
                "broker_request": None,
                "broker_response": None,
                "health": serialize_value(
                    health
                ),
                "errors": list(
                    risk.reason_codes
                ),
            }

            results.append(
                result
            )

            if write_outputs:
                record_registered_broker_events(
                    bridge_id=bridge_id,
                    intent=intent,
                    risk=risk.to_dict(),
                    response=None,
                    status=(
                        "RISK_REJECTED"
                    ),
                )

            continue

        request = broker_request_from_intent(
            intent,
            broker=broker,
            bridge_id=bridge_id,
        )

        try:
            response = broker.submit_order(
                request
            )

            response_payload = (
                serialize_value(
                    response
                )
            )

            response_status = str(
                response_payload.get(
                    "status",
                    "",
                )
            )

            success = response_status in {
                "NEW",
                "ACCEPTED",
                "PARTIALLY_FILLED",
                "FILLED",
                "REPLACED",
            }

            result = {
                "success": success,
                "status": (
                    "SUBMITTED"
                    if success
                    else "BROKER_REJECTED"
                ),
                "provider": provider,
                "intent_id": (
                    intent.intent_id
                ),
                "risk": risk.to_dict(),
                "broker_request": (
                    serialize_value(
                        request
                    )
                ),
                "broker_response": (
                    response_payload
                ),
                "health": serialize_value(
                    health
                ),
                "errors": (
                    []
                    if success
                    else [
                        "BROKER_REJECTED",
                    ]
                ),
            }

            results.append(
                result
            )

            if write_outputs:
                record_registered_broker_events(
                    bridge_id=bridge_id,
                    intent=intent,
                    risk=risk.to_dict(),
                    response=(
                        response_payload
                    ),
                    status=(
                        result["status"]
                    ),
                )

        except Exception as exc:
            result = {
                "success": False,
                "status": (
                    "BROKER_ERROR"
                ),
                "provider": provider,
                "intent_id": (
                    intent.intent_id
                ),
                "risk": risk.to_dict(),
                "broker_request": (
                    serialize_value(
                        request
                    )
                ),
                "broker_response": None,
                "health": serialize_value(
                    health
                ),
                "errors": [
                    f"{type(exc).__name__}: {exc}",
                ],
            }

            results.append(
                result
            )

            if write_outputs:
                record_registered_broker_events(
                    bridge_id=bridge_id,
                    intent=intent,
                    risk=risk.to_dict(),
                    response=None,
                    status=(
                        "BROKER_ERROR"
                    ),
                    error=str(
                        exc
                    ),
                )

    # Registered broker responses do not mutate Atlas's canonical paper account.
    return (
        results,
        account,
    )


def order_intent_from_mapping(
    payload: Mapping[str, Any],
) -> OrderIntent:
    """Reconstruct a canonical OrderIntent from a serialized plan row."""
    allowed = {
        item.name
        for item
        in fields(
            OrderIntent
        )
    }

    values = {
        key: value
        for key, value
        in dict(
            payload
        ).items()
        if key in allowed
    }

    return OrderIntent(
        **values
    )


def broker_request_from_intent(
    intent: OrderIntent,
    *,
    broker: BrokerAdapter,
    bridge_id: str,
) -> BrokerOrderRequest:
    """Translate a canonical Atlas intent into a broker-neutral request."""
    supported_tif = {
        str(value).upper()
        for value
        in broker.capabilities.supported_time_in_force
    }

    requested_tif = (
        intent.time_in_force
        .strip()
        .upper()
    )

    if requested_tif in supported_tif:
        time_in_force = (
            BrokerTimeInForce(
                requested_tif
            )
        )
    elif (
        BrokerTimeInForce.DAY.value
        in supported_tif
    ):
        time_in_force = (
            BrokerTimeInForce.DAY
        )
    elif supported_tif:
        time_in_force = (
            BrokerTimeInForce(
                sorted(
                    supported_tif
                )[0]
            )
        )
    else:
        time_in_force = (
            BrokerTimeInForce.DAY
        )

    return BrokerOrderRequest(
        client_order_id=(
            intent.intent_id
        ),
        symbol=intent.asset,
        side=BrokerSide(
            intent.side
        ),
        order_type=(
            BrokerOrderType(
                intent.order_type
            )
        ),
        quantity=(
            intent.quantity
        ),
        time_in_force=(
            time_in_force
        ),
        limit_price=(
            intent.limit_price
        ),
        reduce_only=(
            intent.reduce_only
        ),
        metadata={
            "bridge_id": bridge_id,
            "strategy_id": (
                intent.strategy_id
            ),
            "evidence_id": (
                intent.evidence_id
            ),
            "reference_price": (
                intent.reference_price
            ),
            "maximum_slippage_bps": (
                intent.maximum_slippage_bps
            ),
            "requested_time_in_force": (
                requested_tif
            ),
            "effective_time_in_force": (
                time_in_force.value
            ),
            "paper_only": bool(
                broker.capabilities.paper_only
            ),
        },
    )


def record_registered_broker_events(
    *,
    bridge_id: str,
    intent: OrderIntent,
    risk: Mapping[str, Any],
    response: Mapping[str, Any] | None,
    status: str,
    error: str = "",
) -> None:
    """Persist provenance for non-paper-service broker submissions."""
    events = [
        {
            "event_type": (
                "EXECUTION_BRIDGE_INTENT"
            ),
            "intent_id": (
                intent.intent_id
            ),
            "status": "RECORDED",
            "payload": (
                intent.to_dict()
            ),
        },
        {
            "event_type": (
                "EXECUTION_BRIDGE_RISK"
            ),
            "intent_id": (
                intent.intent_id
            ),
            "status": (
                "APPROVED"
                if risk.get(
                    "approved",
                    False,
                )
                else "REJECTED"
            ),
            "payload": dict(
                risk
            ),
        },
        {
            "event_type": (
                "EXECUTION_BRIDGE_BROKER"
            ),
            "intent_id": (
                intent.intent_id
            ),
            "status": status,
            "payload": {
                "response": (
                    dict(
                        response
                    )
                    if response
                    is not None
                    else None
                ),
                "error": error,
            },
        },
    ]

    record_execution_events(
        execution_id=(
            bridge_id
        ),
        events=events,
    )


def build_bridge_id(
    *,
    instruction: AtlasStrategyInstruction,
    intent_plan: Mapping[str, Any],
    provider: str,
) -> str:
    payload = {
        "instruction_id": (
            instruction.instruction_id
        ),
        "strategy_id": (
            instruction.strategy_id
        ),
        "source_sha256": (
            instruction.source_decision_sha256
        ),
        "plan_id": (
            intent_plan.get(
                "plan_id",
                "",
            )
        ),
        "provider": provider,
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        "ATLAS-EXEC-BRIDGE-"
        + digest[:24]
    )


def build_bridge_report(
    *,
    bridge_id: str,
    started_at: str,
    instruction: AtlasStrategyInstruction,
    provider: str,
    human_approved: bool,
    intent_plan: Mapping[str, Any],
    order_intents: list[OrderIntent],
    execution_results: list[Mapping[str, Any]],
    account_before: AccountSnapshot,
    account_after: AccountSnapshot,
    status: str,
    success: bool,
    execution_blocked: bool,
    errors: list[str],
) -> dict[str, Any]:
    completed_at = utc_now()

    return {
        "success": bool(
            success
        ),
        "version": (
            EXECUTION_BRIDGE_VERSION
        ),
        "bridge_id": bridge_id,
        "status": status,
        "started_at": (
            started_at
        ),
        "completed_at": (
            completed_at
        ),
        "provider": provider,
        "human_approved": bool(
            human_approved
        ),
        "execution_blocked": bool(
            execution_blocked
        ),
        "instruction": (
            serialize_value(
                instruction
            )
        ),
        "intent_plan": dict(
            intent_plan
        ),
        "order_intents": [
            intent.to_dict()
            for intent
            in order_intents
        ],
        "execution_results": [
            dict(
                result
            )
            for result
            in execution_results
        ],
        "account_before": (
            account_before.to_dict()
        ),
        "account_after": (
            account_after.to_dict()
        ),
        "counts": {
            "generated_intents": len(
                order_intents
            ),
            "execution_results": len(
                execution_results
            ),
            "successful_executions": sum(
                1
                for result
                in execution_results
                if result.get(
                    "success",
                    False,
                )
            ),
            "failed_executions": sum(
                1
                for result
                in execution_results
                if not result.get(
                    "success",
                    False,
                )
            ),
        },
        "errors": list(
            errors
        ),
        "contract": {
            "canonical_entrypoint": True,
            "lyfe_instruction_consumed": True,
            "portfolio_intent_generated": True,
            "pre_trade_risk_required": True,
            "human_approval_required": bool(
                instruction.requires_human_approval
            ),
            "broker_registry_supported": True,
            "paper_service_supported": True,
            "live_execution_forced": False,
            "broker_safety_gate_authoritative": True,
            "private_keys_used": False,
        },
        "outputs": {
            "latest_report_json": str(
                LATEST_REPORT_JSON
            ),
            "history_jsonl": str(
                HISTORY_JSONL
            ),
        },
    }


def serialize_value(
    value: Any,
) -> Any:
    if value is None:
        return None

    if hasattr(
        value,
        "to_dict",
    ):
        return serialize_value(
            value.to_dict()
        )

    if hasattr(
        value,
        "__dataclass_fields__",
    ):
        return {
            field_name: (
                serialize_value(
                    getattr(
                        value,
                        field_name,
                    )
                )
            )
            for field_name
            in value.__dataclass_fields__
        }

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): (
                serialize_value(
                    item
                )
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            serialize_value(
                item
            )
            for item
            in value
        ]

    if hasattr(
        value,
        "value",
    ):
        return serialize_value(
            value.value
        )

    return value


def write_bridge_outputs(
    report: Mapping[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = json.dumps(
        dict(
            report
        ),
        indent=2,
        sort_keys=True,
        default=str,
    )

    temporary = (
        LATEST_REPORT_JSON
        .with_suffix(
            ".json.tmp"
        )
    )

    temporary.write_text(
        payload,
        encoding="utf-8",
    )

    temporary.replace(
        LATEST_REPORT_JSON
    )

    with HISTORY_JSONL.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "bridge_id": (
                        report.get(
                            "bridge_id",
                            "",
                        )
                    ),
                    "completed_at": (
                        report.get(
                            "completed_at",
                            "",
                        )
                    ),
                    "provider": (
                        report.get(
                            "provider",
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
                    "execution_blocked": bool(
                        report.get(
                            "execution_blocked",
                            False,
                        )
                    ),
                    "counts": dict(
                        report.get(
                            "counts",
                            {},
                        )
                    ),
                    "errors": list(
                        report.get(
                            "errors",
                            [],
                        )
                    ),
                },
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


__all__ = [
    "EXECUTION_BRIDGE_VERSION",
    "HISTORY_JSONL",
    "LATEST_REPORT_JSON",
    "build_bridge_id",
    "broker_request_from_intent",
    "execute_lyfe_instruction",
    "execute_with_paper_service",
    "execute_with_registered_broker",
    "order_intent_from_mapping",
    "write_bridge_outputs",
]
