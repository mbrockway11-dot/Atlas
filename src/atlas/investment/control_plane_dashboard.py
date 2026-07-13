"""Read-only Atlas Control Plane dashboard view model.

This module adapts the canonical E.1-E.4 control-plane outputs for Atlas Studio.
It does not approve, dispatch, execute, mutate scheduler state, or expose signing
secrets.

The Streamlit page consumes only the normalized view model returned here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from atlas.investment.control_plane import (
    build_and_write_system_health,
)
from atlas.investment.control_plane_approval import (
    APPROVAL_JSON,
)
from atlas.investment.control_plane_remediation import (
    build_and_write_remediation_plan,
)
from atlas.investment.control_plane_operator_audit import (
    load_latest_operator_audit,
    read_operator_events,
    validate_operator_audit_chain,
)
from atlas.investment.dispatch_reconciliation import (
    RECONCILIATION_JSON,
    read_dispatch_receipts,
)
from atlas.investment.research_orchestrator.provenance import (
    load_latest_provenance,
    read_provenance_events,
)
from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


DASHBOARD_VERSION = "1.0.0"

SAFE_APPROVAL_FIELDS = (
    "approval_id",
    "plan_hash",
    "approved_by",
    "approved_at",
    "expires_at",
    "execution_mode",
    "approved_job_ids",
    "max_steps",
    "used",
    "used_at",
    "dispatch_run_id",
)


def build_control_plane_dashboard_model(
    *,
    refresh: bool = True,
) -> dict[str, Any]:
    """Build the complete read-only Atlas Studio control-plane model."""
    if refresh:
        health = (
            build_and_write_system_health()
        )

        remediation = (
            build_and_write_remediation_plan(
                health
            )
        )
    else:
        health = load_json_object(
            Path(
                "output/atlas_control_plane/"
                "system_health.json"
            )
        )

        remediation = load_json_object(
            Path(
                "output/atlas_control_plane/"
                "remediation_plan.json"
            )
        )

    scheduler_report = (
        build_research_scheduler_report()
    )

    schedule = read_csv_output(
        scheduler_report,
        "research_schedule_csv",
    )

    approval = safe_approval_summary(
        load_json_object(
            APPROVAL_JSON
        )
    )

    reconciliation = (
        load_json_object(
            RECONCILIATION_JSON
        )
    )

    provenance_events = (
        read_provenance_events()
    )

    latest_provenance = (
        load_latest_provenance()
    )

    dispatch_receipts = (
        read_dispatch_receipts()
    )

    operator_events = (
        read_operator_events()
    )

    operator_audit_latest = (
        load_latest_operator_audit()
    )

    operator_audit_validation = (
        validate_operator_audit_chain(
            operator_events
        )
    )

    components = normalize_components(
        health.get(
            "components",
            {},
        )
    )

    recommended_actions = normalize_rows(
        health.get(
            "recommended_actions",
            [],
        )
    )

    remediation_steps = normalize_rows(
        remediation.get(
            "execution_steps",
            [],
        )
    )

    return {
        "success": True,
        "version": DASHBOARD_VERSION,
        "read_only": True,
        "overall_status": str(
            health.get(
                "overall_status",
                "UNKNOWN",
            )
        ),
        "summary": str(
            health.get(
                "summary",
                "",
            )
        ),
        "generated_at": str(
            health.get(
                "generated_at",
                "",
            )
        ),
        "counts": dict(
            health.get(
                "counts",
                {},
            )
            or {}
        ),
        "components": components,
        "component_rows": (
            build_component_rows(
                components
            )
        ),
        "recommended_actions": (
            recommended_actions
        ),
        "remediation": {
            "plan_status": str(
                remediation.get(
                    "plan_status",
                    "UNKNOWN",
                )
            ),
            "summary": str(
                remediation.get(
                    "summary",
                    "",
                )
            ),
            "counts": dict(
                remediation.get(
                    "counts",
                    {},
                )
                or {}
            ),
            "execution": sanitize_execution(
                remediation.get(
                    "execution",
                    {},
                )
            ),
            "steps": remediation_steps,
            "manual_actions": normalize_rows(
                remediation.get(
                    "manual_actions",
                    [],
                )
            ),
            "informational_actions": (
                normalize_rows(
                    remediation.get(
                        "informational_actions",
                        [],
                    )
                )
            ),
        },
        "scheduler": {
            "counts": dict(
                scheduler_report.get(
                    "counts",
                    {},
                )
                or {}
            ),
            "rows": dataframe_records(
                schedule
            ),
        },
        "approval": approval,
        "reconciliation": (
            safe_reconciliation_summary(
                reconciliation
            )
        ),
        "dispatch_receipts": (
            normalize_rows(
                dispatch_receipts
            )
        ),
        "operator_audit": {
            "event_count": len(
                operator_events
            ),
            "chain_valid": bool(
                operator_audit_validation.get(
                    "valid",
                    False,
                )
            ),
            "chain_errors": list(
                operator_audit_validation.get(
                    "errors",
                    [],
                )
            ),
            "latest": dict(
                operator_audit_latest
            ),
            "events": [
                sanitize_operator_event(
                    event
                )
                for event
                in operator_events
            ],
        },
        "provenance": {
            "event_count": len(
                provenance_events
            ),
            "latest_index": (
                sanitize_provenance_latest(
                    latest_provenance
                )
            ),
            "events": [
                sanitize_provenance_event(
                    event
                )
                for event
                in provenance_events
            ],
        },
        "contract": {
            "read_only": True,
            "approval_actions_exposed": False,
            "dispatch_actions_exposed": False,
            "execution_actions_exposed": False,
            "signing_secret_exposed": False,
            "canonical_sources_only": True,
        },
    }


def normalize_components(
    components: Any,
) -> dict[str, dict[str, Any]]:
    if not isinstance(
        components,
        Mapping,
    ):
        return {}

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for name, source in components.items():
        if not isinstance(
            source,
            Mapping,
        ):
            continue

        result[str(name)] = {
            "status": str(
                source.get(
                    "status",
                    "UNKNOWN",
                )
            ),
            "summary": str(
                source.get(
                    "summary",
                    "",
                )
            ),
            "metrics": dict(
                source.get(
                    "metrics",
                    {},
                )
                or {}
            ),
            "issues": [
                str(value)
                for value
                in source.get(
                    "issues",
                    [],
                )
                or []
            ],
        }

    return result


def build_component_rows(
    components: Mapping[
        str,
        Mapping[str, Any],
    ],
) -> list[dict[str, Any]]:
    return [
        {
            "component": name,
            "status": str(
                value.get(
                    "status",
                    "UNKNOWN",
                )
            ),
            "issue_count": len(
                value.get(
                    "issues",
                    [],
                )
                or []
            ),
            "summary": str(
                value.get(
                    "summary",
                    "",
                )
            ),
            "metrics": dict(
                value.get(
                    "metrics",
                    {},
                )
                or {}
            ),
        }
        for name, value
        in components.items()
    ]


def safe_approval_summary(
    approval: Mapping[str, Any],
) -> dict[str, Any]:
    """Return approval metadata without the nonce or signature."""
    if not approval:
        return {
            "present": False,
            "approval_id": "",
            "used": False,
            "approved_job_ids": [],
        }

    result = {
        key: approval.get(key)
        for key in SAFE_APPROVAL_FIELDS
    }

    result["present"] = True

    result["approved_job_ids"] = [
        str(value)
        for value
        in approval.get(
            "approved_job_ids",
            [],
        )
        or []
    ]

    return result


def sanitize_execution(
    execution: Any,
) -> dict[str, Any]:
    if not isinstance(
        execution,
        Mapping,
    ):
        return {}

    return {
        "authorized": bool(
            execution.get(
                "authorized",
                False,
            )
        ),
        "executable": bool(
            execution.get(
                "executable",
                False,
            )
        ),
        "mode": str(
            execution.get(
                "mode",
                "NONE",
            )
        ),
        "recommended_command": str(
            execution.get(
                "recommended_command",
                "",
            )
        ),
        "blocked_reason": str(
            execution.get(
                "blocked_reason",
                "",
            )
        ),
        "resume_run_id": str(
            execution.get(
                "resume_run_id",
                "",
            )
        ),
    }


def safe_reconciliation_summary(
    reconciliation: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:
    if not reconciliation:
        return {
            "present": False,
            "outcome": "NONE",
            "summary": "",
        }

    receipt = reconciliation.get(
        "receipt",
        {},
    )

    if not isinstance(
        receipt,
        Mapping,
    ):
        receipt = {}

    return {
        "present": True,
        "outcome": str(
            reconciliation.get(
                "outcome",
                "UNKNOWN",
            )
        ),
        "summary": str(
            reconciliation.get(
                "summary",
                "",
            )
        ),
        "generated_at": str(
            reconciliation.get(
                "generated_at",
                "",
            )
        ),
        "approval_id": str(
            receipt.get(
                "approval_id",
                "",
            )
        ),
        "dispatch_run_id": str(
            receipt.get(
                "dispatch_run_id",
                "",
            )
        ),
        "scope_valid": bool(
            receipt.get(
                "scope_valid",
                False,
            )
        ),
        "plan_hash_matches": bool(
            receipt.get(
                "plan_hash_matches",
                False,
            )
        ),
        "approved_job_ids": [
            str(value)
            for value
            in receipt.get(
                "approved_job_ids",
                [],
            )
            or []
        ],
        "attempted_job_ids": [
            str(value)
            for value
            in receipt.get(
                "attempted_job_ids",
                [],
            )
            or []
        ],
        "repaired_job_ids": [
            str(value)
            for value
            in receipt.get(
                "repaired_job_ids",
                [],
            )
            or []
        ],
        "unapproved_job_ids": [
            str(value)
            for value
            in receipt.get(
                "unapproved_job_ids",
                [],
            )
            or []
        ],
        "delta": dict(
            receipt.get(
                "delta",
                {},
            )
            or {}
        ),
        "before": dict(
            receipt.get(
                "before",
                {},
            )
            or {}
        ),
        "after": dict(
            receipt.get(
                "after",
                {},
            )
            or {}
        ),
    }



def sanitize_operator_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Flatten safe operator-audit fields for dashboard display."""
    return {
        "event_id": str(
            event.get(
                "event_id",
                "",
            )
        ),
        "recorded_at": str(
            event.get(
                "recorded_at",
                "",
            )
        ),
        "action": str(
            event.get(
                "action",
                "",
            )
        ),
        "result": str(
            event.get(
                "result",
                "",
            )
        ),
        "operator_id": str(
            event.get(
                "operator_id",
                "",
            )
        ),
        "session_id": str(
            event.get(
                "session_id",
                "",
            )
        ),
        "reason": str(
            event.get(
                "reason",
                "",
            )
        ),
        "plan_hash": str(
            event.get(
                "plan_hash",
                "",
            )
        ),
        "approval_id": str(
            event.get(
                "approval_id",
                "",
            )
        ),
        "dispatch_run_id": str(
            event.get(
                "dispatch_run_id",
                "",
            )
        ),
        "job_ids": "|".join(
            str(value)
            for value in event.get(
                "job_ids",
                [],
            )
            or []
        ),
        "event_hash": str(
            event.get(
                "event_hash",
                "",
            )
        ),
        "previous_event_hash": str(
            event.get(
                "previous_event_hash",
                "",
            )
        ),
    }



def sanitize_provenance_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Flatten a provenance event for safe dashboard display."""
    cache = event.get(
        "cache",
        {},
    )

    if not isinstance(
        cache,
        Mapping,
    ):
        cache = {}

    verification = event.get(
        "verification",
        {},
    )

    if not isinstance(
        verification,
        Mapping,
    ):
        verification = {}

    return {
        "event_id": str(
            event.get(
                "event_id",
                "",
            )
        ),
        "recorded_at": str(
            event.get(
                "recorded_at",
                "",
            )
        ),
        "run_id": str(
            event.get(
                "run_id",
                "",
            )
        ),
        "job_id": str(
            event.get(
                "job_id",
                "",
            )
        ),
        "status": str(
            event.get(
                "status",
                "UNKNOWN",
            )
        ),
        "attempt": int(
            event.get(
                "attempt",
                0,
            )
            or 0
        ),
        "duration_seconds": float(
            event.get(
                "duration_seconds",
                0.0,
            )
            or 0.0
        ),
        "cache_hit": bool(
            cache.get(
                "hit",
                False,
            )
        ),
        "artifact_verified": bool(
            verification.get(
                "verified",
                False,
            )
        ),
        "artifact_healed": bool(
            verification.get(
                "healed",
                False,
            )
        ),
        "build_identity_hash": str(
            event.get(
                "build_identity_hash",
                "",
            )
        ),
    }


def sanitize_provenance_latest(
    latest: Mapping[str, Any],
) -> dict[str, Any]:
    if not latest:
        return {
            "event_count": 0,
            "status_counts": {},
            "indexed_jobs": 0,
        }

    jobs = latest.get(
        "jobs",
        {},
    )

    if not isinstance(
        jobs,
        Mapping,
    ):
        jobs = {}

    return {
        "updated_at": str(
            latest.get(
                "updated_at",
                "",
            )
        ),
        "event_count": int(
            latest.get(
                "event_count",
                0,
            )
            or 0
        ),
        "status_counts": dict(
            latest.get(
                "status_counts",
                {},
            )
            or {}
        ),
        "indexed_jobs": len(jobs),
    }


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

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )


def read_csv_output(
    report: Mapping[str, Any],
    output_key: str,
) -> pd.DataFrame:
    outputs = report.get(
        "outputs",
        {},
    )

    if not isinstance(
        outputs,
        Mapping,
    ):
        return pd.DataFrame()

    path_text = str(
        outputs.get(
            output_key,
            "",
        )
    )

    if not path_text:
        return pd.DataFrame()

    path = Path(path_text)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        OSError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        return pd.DataFrame()


def dataframe_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []

    cleaned = frame.astype(
        object
    ).where(
        pd.notna(frame),
        None,
    )

    return [
        {
            str(key): value
            for key, value
            in row.items()
        }
        for row
        in cleaned.to_dict(
            orient="records"
        )
    ]


def normalize_rows(
    rows: Any,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []

    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping)
    ]


__all__ = [
    "DASHBOARD_VERSION",
    "SAFE_APPROVAL_FIELDS",
    "build_component_rows",
    "build_control_plane_dashboard_model",
    "dataframe_records",
    "load_json_object",
    "normalize_components",
    "safe_approval_summary",
    "safe_reconciliation_summary",
    "sanitize_execution",
    "sanitize_provenance_event",
]
