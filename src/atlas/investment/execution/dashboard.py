"""Read-only dashboard model for the Atlas paper execution plane."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from atlas.investment.execution.lifecycle import (
    ORDER_STATE_JSON,
    ORDER_TRANSITIONS_JSONL,
    PaperOrderLifecycleStore,
)
from atlas.investment.execution.portfolio_bridge import (
    LATEST_INTENT_PLAN_JSON,
)
from atlas.investment.execution.service import (
    EXECUTION_LEDGER_JSONL,
    LATEST_REPORT_JSON,
)


PAPER_DASHBOARD_VERSION = "1.0.0"

FORBIDDEN_KEYS = {
    "secret",
    "signature",
    "nonce",
    "api_key",
    "api_secret",
    "access_token",
    "refresh_token",
    "private_key",
    "credentials",
}


def build_paper_execution_dashboard_model(
    *,
    intent_plan_path: Path = (
        LATEST_INTENT_PLAN_JSON
    ),
    execution_report_path: Path = (
        LATEST_REPORT_JSON
    ),
    execution_ledger_path: Path = (
        EXECUTION_LEDGER_JSONL
    ),
    lifecycle_state_path: Path = (
        ORDER_STATE_JSON
    ),
    lifecycle_transitions_path: Path = (
        ORDER_TRANSITIONS_JSONL
    ),
) -> dict[str, Any]:
    """Load and sanitize the latest paper-execution state."""
    intent_plan = load_json_object(
        intent_plan_path
    )

    execution_report = load_json_object(
        execution_report_path
    )

    execution_events = load_jsonl(
        execution_ledger_path
    )

    lifecycle = PaperOrderLifecycleStore(
        state_path=(
            lifecycle_state_path
        ),
        transitions_path=(
            lifecycle_transitions_path
        ),
    )

    lifecycle_records = (
        lifecycle.load_records()
    )

    lifecycle_transitions = (
        lifecycle.read_transitions()
    )

    transition_validation = (
        lifecycle.validate_transition_chain()
    )

    targets = dataframe_records(
        pd.DataFrame(
            intent_plan.get(
                "targets",
                [],
            )
            or []
        )
    )

    rebalance_lines = (
        dataframe_records(
            pd.DataFrame(
                intent_plan.get(
                    "rebalance_lines",
                    [],
                )
                or []
            )
        )
    )

    intents = dataframe_records(
        pd.DataFrame(
            intent_plan.get(
                "intents",
                [],
            )
            or []
        )
    )

    fills = dataframe_records(
        pd.DataFrame(
            execution_report.get(
                "fills",
                [],
            )
            or []
        )
    )

    positions = normalize_positions(
        execution_report.get(
            "account_after",
            {},
        )
    )

    lifecycle_rows = [
        sanitize_mapping(
            record.to_dict()
        )
        for record
        in lifecycle_records.values()
    ]

    transition_rows = [
        sanitize_mapping(
            transition.to_dict()
        )
        for transition
        in lifecycle_transitions
    ]

    current_order = sanitize_mapping(
        execution_report.get(
            "order",
            {},
        )
    )

    current_risk = sanitize_mapping(
        execution_report.get(
            "risk",
            {},
        )
    )

    account_before = sanitize_mapping(
        execution_report.get(
            "account_before",
            {},
        )
    )

    account_after = sanitize_mapping(
        execution_report.get(
            "account_after",
            {},
        )
    )

    open_records = [
        row
        for row in lifecycle_rows
        if bool(
            row.get(
                "open",
                False,
            )
        )
    ]

    terminal_records = [
        row
        for row in lifecycle_rows
        if bool(
            row.get(
                "terminal",
                False,
            )
        )
    ]

    report_contract = (
        execution_report.get(
            "contract",
            {},
        )
    )

    plan_contract = intent_plan.get(
        "contract",
        {},
    )

    safety = {
        "paper_only": bool(
            report_contract.get(
                "paper_only",
                True,
            )
        ),
        "live_execution": bool(
            execution_report.get(
                "live_execution",
                False,
            )
        ),
        "live_credentials_used": bool(
            report_contract.get(
                "live_credentials_used",
                False,
            )
            or plan_contract.get(
                "live_credentials_used",
                False,
            )
        ),
        "intent_generation_only": bool(
            plan_contract.get(
                "intent_generation_only",
                False,
            )
        ),
        "submits_orders": bool(
            plan_contract.get(
                "submits_orders",
                False,
            )
        ),
        "mutates_account": bool(
            plan_contract.get(
                "mutates_account",
                False,
            )
        ),
        "broker_neutral": bool(
            report_contract.get(
                "broker_neutral",
                True,
            )
            and plan_contract.get(
                "broker_neutral",
                True,
            )
        ),
    }

    status = derive_dashboard_status(
        safety=safety,
        transition_validation=(
            transition_validation
        ),
        execution_report=(
            execution_report
        ),
    )

    return {
        "success": True,
        "version": (
            PAPER_DASHBOARD_VERSION
        ),
        "status": status,
        "summary": build_summary(
            status=status,
            intent_count=len(
                intents
            ),
            fill_count=len(
                fills
            ),
            open_order_count=len(
                open_records
            ),
            lifecycle_count=len(
                lifecycle_rows
            ),
        ),
        "intent_plan": {
            "exists": bool(
                intent_plan
            ),
            "plan_id": str(
                intent_plan.get(
                    "plan_id",
                    "",
                )
            ),
            "generated_at": str(
                intent_plan.get(
                    "generated_at",
                    "",
                )
            ),
            "strategy_id": str(
                intent_plan.get(
                    "strategy_id",
                    "",
                )
            ),
            "evidence_id": str(
                intent_plan.get(
                    "evidence_id",
                    "",
                )
            ),
            "account_equity": safe_float(
                intent_plan.get(
                    "account_equity",
                    0.0,
                )
            ),
            "target_weight_total": safe_float(
                intent_plan.get(
                    "target_weight_total",
                    0.0,
                )
            ),
            "minimum_cash_weight": safe_float(
                intent_plan.get(
                    "minimum_cash_weight",
                    0.0,
                )
            ),
            "total_turnover_notional": safe_float(
                intent_plan.get(
                    "total_turnover_notional",
                    0.0,
                )
            ),
            "total_turnover_weight": safe_float(
                intent_plan.get(
                    "total_turnover_weight",
                    0.0,
                )
            ),
            "counts": sanitize_mapping(
                intent_plan.get(
                    "counts",
                    {},
                )
            ),
            "targets": targets,
            "rebalance_lines": (
                rebalance_lines
            ),
            "intents": intents,
        },
        "latest_execution": {
            "exists": bool(
                execution_report
            ),
            "success": bool(
                execution_report.get(
                    "success",
                    False,
                )
            ),
            "mode": str(
                execution_report.get(
                    "mode",
                    "PAPER",
                )
            ),
            "intent": sanitize_mapping(
                execution_report.get(
                    "intent",
                    {},
                )
            ),
            "risk": current_risk,
            "order": current_order,
            "fills": fills,
            "account_before": (
                account_before
            ),
            "account_after": (
                account_after
            ),
            "positions": positions,
        },
        "execution_history": {
            "event_count": len(
                execution_events
            ),
            "events": [
                sanitize_mapping(
                    event
                )
                for event
                in execution_events
            ],
        },
        "lifecycle": {
            "record_count": len(
                lifecycle_rows
            ),
            "open_order_count": len(
                open_records
            ),
            "terminal_order_count": len(
                terminal_records
            ),
            "records": lifecycle_rows,
            "open_orders": open_records,
            "transitions": transition_rows,
            "transition_count": int(
                transition_validation.get(
                    "transition_count",
                    0,
                )
            ),
            "chain_valid": bool(
                transition_validation.get(
                    "valid",
                    False,
                )
            ),
            "chain_errors": list(
                transition_validation.get(
                    "errors",
                    [],
                )
            ),
            "latest_event_hash": str(
                transition_validation.get(
                    "latest_event_hash",
                    "",
                )
            ),
        },
        "safety": safety,
        "paths": {
            "intent_plan_json": str(
                intent_plan_path
            ),
            "execution_report_json": str(
                execution_report_path
            ),
            "execution_ledger_jsonl": str(
                execution_ledger_path
            ),
            "lifecycle_state_json": str(
                lifecycle_state_path
            ),
            "lifecycle_transitions_jsonl": str(
                lifecycle_transitions_path
            ),
        },
    }


def derive_dashboard_status(
    *,
    safety: Mapping[str, Any],
    transition_validation: Mapping[
        str,
        Any,
    ],
    execution_report: Mapping[
        str,
        Any,
    ],
) -> str:
    if bool(
        safety.get(
            "live_execution",
            False,
        )
    ):
        return "CRITICAL"

    if bool(
        safety.get(
            "live_credentials_used",
            False,
        )
    ):
        return "CRITICAL"

    if not bool(
        transition_validation.get(
            "valid",
            False,
        )
    ):
        return "DEGRADED"

    if (
        execution_report
        and not bool(
            execution_report.get(
                "success",
                False,
            )
        )
    ):
        return "ATTENTION"

    return "HEALTHY"


def build_summary(
    *,
    status: str,
    intent_count: int,
    fill_count: int,
    open_order_count: int,
    lifecycle_count: int,
) -> str:
    return (
        "Atlas Paper Execution Dashboard is "
        f"{status}: {intent_count} generated intent(s), "
        f"{fill_count} latest fill(s), "
        f"{open_order_count} open lifecycle order(s), "
        f"and {lifecycle_count} tracked lifecycle record(s)."
    )


def normalize_positions(
    account_payload: Any,
) -> list[dict[str, Any]]:
    if not isinstance(
        account_payload,
        Mapping,
    ):
        return []

    positions = account_payload.get(
        "positions",
        {},
    )

    if not isinstance(
        positions,
        Mapping,
    ):
        return []

    rows = []

    for asset, payload in sorted(
        positions.items()
    ):
        if not isinstance(
            payload,
            Mapping,
        ):
            continue

        row = {
            "asset": str(asset),
            **sanitize_mapping(
                payload
            ),
        }

        rows.append(row)

    return rows


def load_json_object(
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

    if not isinstance(
        payload,
        dict,
    ):
        return {}

    return sanitize_mapping(
        payload
    )


def load_jsonl(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows = []

    try:
        handle = path.open(
            "r",
            encoding="utf-8",
        )
    except OSError:
        return []

    with handle:
        for line in handle:
            text = line.strip()

            if not text:
                continue

            try:
                payload = json.loads(
                    text
                )
            except json.JSONDecodeError:
                continue

            if isinstance(
                payload,
                Mapping,
            ):
                rows.append(
                    sanitize_mapping(
                        payload
                    )
                )

    return rows


def dataframe_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    cleaned = frame.astype(
        object
    ).where(
        pd.notna(frame),
        None,
    )

    return [
        sanitize_mapping(
            row
        )
        for row in cleaned.to_dict(
            orient="records"
        )
    ]


def sanitize_mapping(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Mapping,
    ):
        result = {}

        for key, item in value.items():
            key_text = str(key)

            if (
                key_text.lower()
                in FORBIDDEN_KEYS
            ):
                continue

            result[key_text] = (
                sanitize_mapping(
                    item
                )
            )

        return result

    if isinstance(
        value,
        list,
    ):
        return [
            sanitize_mapping(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            sanitize_mapping(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        float,
    ) and not math.isfinite(
        value
    ):
        return None

    return value


def safe_float(
    value: Any,
) -> float:
    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return (
        number
        if math.isfinite(number)
        else 0.0
    )


__all__ = [
    "FORBIDDEN_KEYS",
    "PAPER_DASHBOARD_VERSION",
    "build_paper_execution_dashboard_model",
    "dataframe_records",
    "derive_dashboard_status",
    "load_json_object",
    "load_jsonl",
    "sanitize_mapping",
]
