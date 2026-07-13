"""Unified Atlas investment-system control plane.

The control plane is a read-oriented aggregation layer over canonical systems:

- architecture registry audit;
- artifact producer/output contracts;
- artifact input lineage;
- dependency-aware research scheduler;
- deterministic build cache;
- resumable/self-healing execution state;
- immutable execution provenance.

It owns no execution order, artifact registry, dependency graph, or business
logic. Its responsibility is to answer:

    What is healthy?
    What is degraded?
    What is blocked?
    Why?
    What should happen next?
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from atlas.investment.artifact_contracts import (
    build_contract_audit,
)
from atlas.investment.artifact_lineage import (
    build_lineage_audit,
)
from atlas.investment.research_orchestrator.build_cache import (
    load_build_cache,
)
from atlas.investment.research_orchestrator.provenance import (
    load_latest_provenance,
    read_provenance_events,
)
from atlas.investment.research_orchestrator.resume import (
    load_resume_state,
)
from atlas.investment.research_scheduler import (
    build_research_scheduler_report,
)


CONTROL_PLANE_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/atlas_control_plane"
)

SYSTEM_HEALTH_JSON = (
    OUTPUT_DIR
    / "system_health.json"
)

SYSTEM_HEALTH_CSV = (
    OUTPUT_DIR
    / "system_health.csv"
)

RECOMMENDED_ACTIONS_CSV = (
    OUTPUT_DIR
    / "recommended_actions.csv"
)

SYSTEM_HEALTH_MD = (
    OUTPUT_DIR
    / "system_health.md"
)


SEVERITY_RANK = {
    "INFO": 1,
    "LOW": 2,
    "MEDIUM": 3,
    "HIGH": 4,
    "CRITICAL": 5,
}

HEALTH_RANK = {
    "HEALTHY": 1,
    "DEGRADED": 2,
    "CRITICAL": 3,
}


def build_system_health() -> dict[str, Any]:
    """Build one authoritative Atlas system-health snapshot."""
    generated_at = (
        datetime.now(UTC).isoformat()
    )

    scheduler_report = (
        build_research_scheduler_report()
    )

    schedule = read_schedule(
        scheduler_report
    )

    contract_audit = (
        build_contract_audit()
    )

    lineage_audit = (
        build_lineage_audit()
    )

    cache_state = load_build_cache()
    provenance_events = (
        read_provenance_events()
    )
    provenance_latest = (
        load_latest_provenance()
    )
    execution_state = (
        load_resume_state()
    )

    architecture = build_architecture_health(
        contract_audit=contract_audit,
        lineage_audit=lineage_audit,
    )

    scheduler = build_scheduler_health(
        scheduler_report=scheduler_report,
        schedule=schedule,
    )

    contracts = build_contract_health(
        contract_audit
    )

    lineage = build_lineage_health(
        lineage_audit
    )

    cache = build_cache_health(
        cache_state
    )

    provenance = build_provenance_health(
        events=provenance_events,
        latest=provenance_latest,
    )

    execution = build_execution_health(
        execution_state
    )

    components = {
        "architecture": architecture,
        "artifact_contracts": contracts,
        "artifact_lineage": lineage,
        "scheduler": scheduler,
        "build_cache": cache,
        "execution": execution,
        "provenance": provenance,
    }

    actions = build_recommended_actions(
        components=components,
        schedule=schedule,
        contract_audit=contract_audit,
        lineage_audit=lineage_audit,
        execution_state=execution_state,
    )

    overall_status = derive_overall_status(
        components
    )

    component_rows = build_component_rows(
        components
    )

    counts = {
        "components": len(components),
        "healthy_components": sum(
            1
            for component in components.values()
            if component["status"]
            == "HEALTHY"
        ),
        "degraded_components": sum(
            1
            for component in components.values()
            if component["status"]
            == "DEGRADED"
        ),
        "critical_components": sum(
            1
            for component in components.values()
            if component["status"]
            == "CRITICAL"
        ),
        "recommended_actions": len(
            actions
        ),
        "critical_actions": sum(
            1
            for action in actions
            if action["severity"]
            == "CRITICAL"
        ),
        "high_priority_actions": sum(
            1
            for action in actions
            if action["severity"]
            == "HIGH"
        ),
    }

    return {
        "success": overall_status
        != "CRITICAL",
        "version": CONTROL_PLANE_VERSION,
        "generated_at": generated_at,
        "overall_status": overall_status,
        "summary": build_summary(
            overall_status=overall_status,
            components=components,
            actions=actions,
        ),
        "counts": counts,
        "components": components,
        "component_rows": component_rows,
        "recommended_actions": actions,
        "contract": {
            "read_oriented": True,
            "owns_scheduler": False,
            "owns_artifact_registry": False,
            "owns_dependency_graph": False,
            "owns_execution": False,
            "canonical_sources_only": True,
            "recommended_actions_are_advisory": True,
        },
        "outputs": {
            "system_health_json": str(
                SYSTEM_HEALTH_JSON
            ),
            "system_health_csv": str(
                SYSTEM_HEALTH_CSV
            ),
            "recommended_actions_csv": str(
                RECOMMENDED_ACTIONS_CSV
            ),
            "system_health_markdown": str(
                SYSTEM_HEALTH_MD
            ),
        },
    }


def build_architecture_health(
    *,
    contract_audit: Mapping[str, Any],
    lineage_audit: Mapping[str, Any],
) -> dict[str, Any]:
    contract_errors = list(
        contract_audit.get(
            "registry_errors",
            [],
        )
    )

    lineage_errors = list(
        lineage_audit.get(
            "registry_errors",
            [],
        )
    )

    errors = [
        *contract_errors,
        *lineage_errors,
    ]

    status = (
        "CRITICAL"
        if errors
        else "HEALTHY"
    )

    return component(
        status=status,
        summary=(
            "Canonical registries and structural "
            "contracts are valid."
            if not errors
            else (
                f"{len(errors)} structural "
                "architecture error(s) detected."
            )
        ),
        metrics={
            "registered_jobs": int(
                contract_audit.get(
                    "registered_job_count",
                    0,
                )
            ),
            "registered_artifacts": int(
                contract_audit.get(
                    "registered_artifact_count",
                    0,
                )
            ),
            "artifact_contracts": int(
                contract_audit.get(
                    "contract_count",
                    0,
                )
            ),
            "input_contracts": int(
                lineage_audit.get(
                    "input_contract_count",
                    0,
                )
            ),
            "structural_errors": len(
                errors
            ),
        },
        issues=errors,
    )


def build_contract_health(
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    failed_jobs = list(
        audit.get(
            "failed_job_contracts",
            [],
        )
    )

    structural_errors = list(
        audit.get(
            "registry_errors",
            [],
        )
    )

    if structural_errors:
        status = "CRITICAL"
    elif failed_jobs:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    return component(
        status=status,
        summary=(
            "All required job-output contracts "
            "are currently complete."
            if not failed_jobs
            else (
                f"{len(failed_jobs)} job output "
                "contract(s) are incomplete."
            )
        ),
        metrics={
            "contracts": int(
                audit.get(
                    "contract_count",
                    0,
                )
            ),
            "assigned_artifacts": int(
                audit.get(
                    "assigned_artifact_count",
                    0,
                )
            ),
            "unassigned_artifacts": int(
                audit.get(
                    "unassigned_artifact_count",
                    0,
                )
            ),
            "failed_contracts": len(
                failed_jobs
            ),
        },
        issues=failed_jobs,
    )


def build_lineage_health(
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    incomplete = list(
        audit.get(
            "incomplete_job_inputs",
            [],
        )
    )

    structural_errors = list(
        audit.get(
            "registry_errors",
            [],
        )
    )

    if structural_errors:
        status = "CRITICAL"
    elif incomplete:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    return component(
        status=status,
        summary=(
            "All declared required inputs are "
            "available and structurally valid."
            if not incomplete
            else (
                f"{len(incomplete)} job input "
                "contract(s) are incomplete."
            )
        ),
        metrics={
            "input_contracts": int(
                audit.get(
                    "input_contract_count",
                    0,
                )
            ),
            "lineage_edges": int(
                audit.get(
                    "lineage_edge_count",
                    0,
                )
            ),
            "explicit_inputs": int(
                audit.get(
                    "explicit_input_artifact_count",
                    0,
                )
            ),
            "incomplete_inputs": len(
                incomplete
            ),
        },
        issues=incomplete,
    )


def build_scheduler_health(
    *,
    scheduler_report: Mapping[str, Any],
    schedule: pd.DataFrame,
) -> dict[str, Any]:
    counts = dict(
        scheduler_report.get(
            "counts",
            {},
        )
    )

    failed = safe_int(
        counts.get(
            "failed_jobs",
            0,
        )
    )
    blocked = safe_int(
        counts.get(
            "blocked_jobs",
            0,
        )
    )
    ready = safe_int(
        counts.get(
            "ready_jobs",
            0,
        )
    )
    dirty = safe_int(
        counts.get(
            "dirty_jobs",
            0,
        )
    )

    if failed:
        status = "CRITICAL"
    elif blocked or ready or dirty:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    blocked_jobs = select_job_ids(
        schedule,
        "BLOCKED",
    )

    ready_jobs = select_job_ids(
        schedule,
        "READY",
    )

    return component(
        status=status,
        summary=(
            "All registered research jobs are current."
            if status == "HEALTHY"
            else (
                f"{ready} ready, {blocked} blocked, "
                f"{dirty} dirty, and {failed} failed "
                "job(s) require attention."
            )
        ),
        metrics={
            "total_jobs": safe_int(
                counts.get(
                    "total_jobs",
                    len(schedule),
                )
            ),
            "current_jobs": safe_int(
                counts.get(
                    "current_jobs",
                    0,
                )
            ),
            "ready_jobs": ready,
            "blocked_jobs": blocked,
            "failed_jobs": failed,
            "dirty_jobs": dirty,
            "directly_dirty_jobs": safe_int(
                counts.get(
                    "directly_dirty_jobs",
                    0,
                )
            ),
            "propagated_dirty_jobs": safe_int(
                counts.get(
                    "propagated_dirty_jobs",
                    0,
                )
            ),
            "maximum_dirty_depth": safe_int(
                counts.get(
                    "maximum_dirty_depth",
                    0,
                )
            ),
        },
        issues=[
            *(
                f"READY:{job_id}"
                for job_id in ready_jobs
            ),
            *(
                f"BLOCKED:{job_id}"
                for job_id in blocked_jobs
            ),
        ],
    )


def build_cache_health(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    entries = state.get(
        "entries",
        {},
    )

    if not isinstance(entries, dict):
        entries = {}

    entry_count = len(entries)

    return component(
        status="HEALTHY",
        summary=(
            f"{entry_count} validated build cache "
            "entr"
            + (
                "y is available."
                if entry_count == 1
                else "ies are available."
            )
        ),
        metrics={
            "cache_entries": entry_count,
            "schema_version": str(
                state.get(
                    "schema_version",
                    "",
                )
            ),
            "hash_algorithm": str(
                state.get(
                    "hash_algorithm",
                    "",
                )
            ),
        },
        issues=[],
    )


def build_execution_health(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    if not state:
        return component(
            status="HEALTHY",
            summary=(
                "No incomplete execution checkpoint "
                "is currently present."
            ),
            metrics={
                "checkpoint_present": False,
                "completed_jobs": 0,
                "failed_results": 0,
            },
            issues=[],
        )

    run_status = str(
        state.get(
            "status",
            "UNKNOWN",
        )
    )

    results = state.get(
        "results",
        [],
    )

    if not isinstance(results, list):
        results = []

    failed_results = [
        result
        for result in results
        if isinstance(result, dict)
        and str(
            result.get(
                "status",
                "",
            )
        )
        in {
            "FAILED",
            "TIMED_OUT",
            "RECOVERY_FAILED",
        }
    ]

    resumable = bool(
        state.get(
            "resumable",
            False,
        )
    )

    if run_status in {
        "FAILED",
        "INTERRUPTED",
    }:
        status = "CRITICAL"
    elif resumable or run_status == "RUNNING":
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    issues = []

    if resumable:
        issues.append(
            "RESUMABLE_EXECUTION_PRESENT"
        )

    issues.extend(
        "FAILED_RESULT:"
        + str(
            result.get(
                "job_id",
                "unknown",
            )
        )
        for result in failed_results
    )

    return component(
        status=status,
        summary=(
            f"Latest execution state is {run_status}."
        ),
        metrics={
            "checkpoint_present": True,
            "run_id": str(
                state.get(
                    "run_id",
                    "",
                )
            ),
            "run_status": run_status,
            "resumable": resumable,
            "completed_jobs": len(
                state.get(
                    "completed_job_ids",
                    [],
                )
                or []
            ),
            "failed_results": len(
                failed_results
            ),
        },
        issues=issues,
    )


def build_provenance_health(
    *,
    events: list[dict[str, Any]],
    latest: Mapping[str, Any],
) -> dict[str, Any]:
    event_ids = [
        str(
            event.get(
                "event_id",
                "",
            )
        )
        for event in events
        if isinstance(event, dict)
    ]

    duplicate_count = (
        len(event_ids)
        - len(set(event_ids))
    )

    indexed_count = safe_int(
        latest.get(
            "event_count",
            0,
        )
    )

    malformed = [
        index
        for index, event in enumerate(
            events,
            start=1,
        )
        if not all(
            key in event
            for key in (
                "event_id",
                "run_id",
                "job_id",
                "status",
                "build_identity_hash",
                "required_input_manifest",
                "required_output_manifest",
            )
        )
    ]

    issues = []

    if duplicate_count:
        issues.append(
            "DUPLICATE_EVENT_IDS"
        )

    if malformed:
        issues.append(
            "MALFORMED_EVENTS"
        )

    if indexed_count != len(events):
        issues.append(
            "LATEST_INDEX_COUNT_MISMATCH"
        )

    status = (
        "CRITICAL"
        if issues
        else "HEALTHY"
    )

    return component(
        status=status,
        summary=(
            "Execution provenance ledger and latest "
            "index are internally consistent."
            if not issues
            else (
                "Execution provenance integrity "
                "problems were detected."
            )
        ),
        metrics={
            "events": len(events),
            "indexed_events": indexed_count,
            "indexed_jobs": len(
                latest.get(
                    "jobs",
                    {},
                )
                or {}
            ),
            "duplicate_event_ids": (
                duplicate_count
            ),
            "malformed_events": len(
                malformed
            ),
        },
        issues=issues,
    )


def build_recommended_actions(
    *,
    components: Mapping[
        str,
        Mapping[str, Any],
    ],
    schedule: pd.DataFrame,
    contract_audit: Mapping[str, Any],
    lineage_audit: Mapping[str, Any],
    execution_state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build deterministic advisory actions from canonical health state."""
    actions: list[
        dict[str, Any]
    ] = []

    for error in components[
        "architecture"
    ][
        "issues"
    ]:
        actions.append(
            action(
                severity="CRITICAL",
                category="architecture",
                action_type=(
                    "REPAIR_STRUCTURAL_CONTRACT"
                ),
                target=str(error),
                reason=(
                    "Canonical architecture validation "
                    "reported a structural error."
                ),
                recommended_command=(
                    "python scripts/"
                    "audit_architecture_consolidation.py"
                ),
            )
        )

    failed_contracts = list(
        contract_audit.get(
            "failed_job_contracts",
            [],
        )
    )

    for job_id in failed_contracts:
        actions.append(
            action(
                severity="HIGH",
                category="artifact_contract",
                action_type=(
                    "REBUILD_REQUIRED_OUTPUTS"
                ),
                target=str(job_id),
                reason=(
                    "One or more required output "
                    "artifacts are missing or invalid."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py --execute"
                ),
            )
        )

    incomplete_inputs = list(
        lineage_audit.get(
            "incomplete_job_inputs",
            [],
        )
    )

    for job_id in incomplete_inputs:
        actions.append(
            action(
                severity="HIGH",
                category="artifact_lineage",
                action_type=(
                    "RESTORE_REQUIRED_INPUTS"
                ),
                target=str(job_id),
                reason=(
                    "One or more required input "
                    "artifacts are missing or invalid."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py --execute"
                ),
            )
        )

    for job_id in select_job_ids(
        schedule,
        "READY",
    ):
        actions.append(
            action(
                severity="MEDIUM",
                category="scheduler",
                action_type="EXECUTE_READY_JOB",
                target=job_id,
                reason=(
                    "The canonical scheduler marked "
                    "this job ready."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py --execute"
                ),
            )
        )

    for job_id in select_job_ids(
        schedule,
        "BLOCKED",
    ):
        row = schedule[
            schedule[
                "job_id"
            ].astype(str).eq(job_id)
        ].iloc[0]

        blockers = str(
            row.get(
                "blocking_dependencies",
                "",
            )
        )

        actions.append(
            action(
                severity="MEDIUM",
                category="scheduler",
                action_type=(
                    "RESOLVE_BLOCKING_DEPENDENCIES"
                ),
                target=job_id,
                reason=(
                    "Job is blocked by canonical "
                    f"dependencies: {blockers or 'unknown'}."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py --execute"
                ),
            )
        )

    if bool(
        execution_state.get(
            "resumable",
            False,
        )
    ):
        actions.append(
            action(
                severity="HIGH",
                category="execution",
                action_type=(
                    "RESUME_INTERRUPTED_CYCLE"
                ),
                target=str(
                    execution_state.get(
                        "run_id",
                        "",
                    )
                ),
                reason=(
                    "An incomplete executable cycle "
                    "has a resumable checkpoint."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py "
                    "--execute --resume"
                ),
            )
        )

    if (
        components[
            "build_cache"
        ][
            "metrics"
        ][
            "cache_entries"
        ]
        == 0
    ):
        actions.append(
            action(
                severity="INFO",
                category="build_cache",
                action_type=(
                    "ESTABLISH_BUILD_CACHE"
                ),
                target="build_cache",
                reason=(
                    "No verified successful builds "
                    "are currently cached."
                ),
                recommended_command=(
                    "python scripts/"
                    "run_research_cycle.py --execute"
                ),
            )
        )

    if not actions:
        actions.append(
            action(
                severity="INFO",
                category="system",
                action_type=(
                    "NO_ACTION_REQUIRED"
                ),
                target="atlas",
                reason=(
                    "All monitored control-plane "
                    "components are healthy."
                ),
                recommended_command="",
            )
        )

    actions = deduplicate_actions(
        actions
    )

    actions.sort(
        key=lambda item: (
            -SEVERITY_RANK[
                item["severity"]
            ],
            item["category"],
            item["target"],
            item["action_type"],
        )
    )

    for rank, item in enumerate(
        actions,
        start=1,
    ):
        item["action_rank"] = rank

    return actions


def derive_overall_status(
    components: Mapping[
        str,
        Mapping[str, Any],
    ],
) -> str:
    statuses = [
        str(
            component.get(
                "status",
                "CRITICAL",
            )
        )
        for component in components.values()
    ]

    return max(
        statuses,
        key=lambda value: (
            HEALTH_RANK.get(
                value,
                HEALTH_RANK["CRITICAL"],
            )
        ),
    )


def build_component_rows(
    components: Mapping[
        str,
        Mapping[str, Any],
    ],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for name, value in components.items():
        rows.append({
            "component": name,
            "status": str(
                value.get(
                    "status",
                    "",
                )
            ),
            "summary": str(
                value.get(
                    "summary",
                    "",
                )
            ),
            "issue_count": len(
                value.get(
                    "issues",
                    [],
                )
                or []
            ),
            "metrics_json": json.dumps(
                value.get(
                    "metrics",
                    {},
                ),
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            ),
        })

    return rows


def write_system_health_outputs(
    report: Mapping[str, Any],
) -> None:
    """Write JSON, CSV, and Markdown control-plane outputs."""
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SYSTEM_HEALTH_JSON.write_text(
        json.dumps(
            dict(report),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        report.get(
            "component_rows",
            [],
        )
    ).to_csv(
        SYSTEM_HEALTH_CSV,
        index=False,
    )

    pd.DataFrame(
        report.get(
            "recommended_actions",
            [],
        )
    ).to_csv(
        RECOMMENDED_ACTIONS_CSV,
        index=False,
    )

    SYSTEM_HEALTH_MD.write_text(
        render_system_health_markdown(
            report
        ),
        encoding="utf-8",
    )


def build_and_write_system_health() -> dict[str, Any]:
    report = build_system_health()
    write_system_health_outputs(
        report
    )
    return report


def render_system_health_markdown(
    report: Mapping[str, Any],
) -> str:
    lines = [
        "# Atlas Control Plane",
        "",
        (
            f"- Overall status: "
            f"`{report['overall_status']}`"
        ),
        (
            f"- Generated at: "
            f"`{report['generated_at']}`"
        ),
        (
            f"- Recommended actions: "
            f"`{report['counts']['recommended_actions']}`"
        ),
        "",
        "## Components",
        "",
        "| Component | Status | Issues | Summary |",
        "|---|---:|---:|---|",
    ]

    for row in report.get(
        "component_rows",
        [],
    ):
        lines.append(
            "| "
            + str(row["component"])
            + " | "
            + str(row["status"])
            + " | "
            + str(row["issue_count"])
            + " | "
            + str(row["summary"]).replace(
                "|",
                "/",
            )
            + " |"
        )

    lines.extend([
        "",
        "## Recommended Actions",
        "",
        "| Rank | Severity | Category | Target | Action |",
        "|---:|---:|---|---|---|",
    ])

    for item in report.get(
        "recommended_actions",
        [],
    ):
        lines.append(
            "| "
            + str(item["action_rank"])
            + " | "
            + str(item["severity"])
            + " | "
            + str(item["category"])
            + " | "
            + str(item["target"]).replace(
                "|",
                "/",
            )
            + " | "
            + str(item["action_type"])
            + " |"
        )

    lines.append("")

    return "\n".join(lines)


def read_schedule(
    scheduler_report: Mapping[str, Any],
) -> pd.DataFrame:
    path = (
        scheduler_report.get(
            "outputs",
            {},
        )
        or {}
    ).get(
        "research_schedule_csv",
        "",
    )

    if not path:
        return pd.DataFrame()

    schedule_path = Path(
        str(path)
    )

    if not schedule_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            schedule_path
        )
    except (
        OSError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        return pd.DataFrame()


def select_job_ids(
    schedule: pd.DataFrame,
    status: str,
) -> list[str]:
    if (
        schedule is None
        or schedule.empty
        or "status" not in schedule.columns
        or "job_id" not in schedule.columns
    ):
        return []

    return schedule[
        schedule[
            "status"
        ].astype(str).eq(
            status
        )
    ][
        "job_id"
    ].astype(str).tolist()


def component(
    *,
    status: str,
    summary: str,
    metrics: Mapping[str, Any],
    issues: list[Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "metrics": dict(metrics),
        "issues": list(issues),
    }


def action(
    *,
    severity: str,
    category: str,
    action_type: str,
    target: str,
    reason: str,
    recommended_command: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "action_type": action_type,
        "target": target,
        "reason": reason,
        "recommended_command": (
            recommended_command
        ),
    }


def deduplicate_actions(
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[
        tuple[str, str, str, str]
    ] = set()

    result: list[
        dict[str, Any]
    ] = []

    for item in actions:
        identity = (
            str(item["severity"]),
            str(item["category"]),
            str(item["action_type"]),
            str(item["target"]),
        )

        if identity in seen:
            continue

        seen.add(identity)
        result.append(dict(item))

    return result


def build_summary(
    *,
    overall_status: str,
    components: Mapping[
        str,
        Mapping[str, Any],
    ],
    actions: list[dict[str, Any]],
) -> str:
    degraded = sum(
        1
        for component in components.values()
        if component["status"]
        == "DEGRADED"
    )

    critical = sum(
        1
        for component in components.values()
        if component["status"]
        == "CRITICAL"
    )

    return (
        "Atlas Control Plane evaluated "
        f"{len(components)} component(s): "
        f"{critical} critical, "
        f"{degraded} degraded, and "
        f"{len(actions)} recommended action(s). "
        f"Overall status: {overall_status}."
    )


def safe_int(
    value: Any,
) -> int:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0


__all__ = [
    "CONTROL_PLANE_VERSION",
    "OUTPUT_DIR",
    "RECOMMENDED_ACTIONS_CSV",
    "SYSTEM_HEALTH_CSV",
    "SYSTEM_HEALTH_JSON",
    "SYSTEM_HEALTH_MD",
    "build_and_write_system_health",
    "build_component_rows",
    "build_recommended_actions",
    "build_system_health",
    "derive_overall_status",
    "render_system_health_markdown",
    "write_system_health_outputs",
]
