"""Observability services for G.17 Section 3 investment orchestration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "g17.orchestration.observability.v1"


class ObservabilityError(RuntimeError):
    """Raised when orchestration observability artifacts are invalid."""


@dataclass(frozen=True)
class OrchestrationCycleSummary:
    run_id: str
    decision_id: str
    status: str
    dry_run: bool
    started_at: str
    finished_at: str
    elapsed_ms: int
    job_count: int
    successful_jobs: int
    failed_jobs: int
    blocked_jobs: int
    timed_out_jobs: int
    record_hash: str


@dataclass(frozen=True)
class OrchestrationDashboardSnapshot:
    schema_version: str
    scheduler_decision: dict[str, Any] | None
    latest_report: dict[str, Any] | None
    checkpoint: dict[str, Any] | None
    latest_successful_cycle: dict[str, Any] | None
    latest_failed_cycle: dict[str, Any] | None
    history_chain_valid: bool
    duplicate_prevention_enabled: bool
    dependency_chain_valid: bool
    stale_scheduler_decision: bool
    missing_artifacts: list[str]
    warnings: list[str]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_record_hash(record: Mapping[str, Any]) -> str:
    material = dict(record)
    material.pop("record_hash", None)
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def read_json(path: Path, *, required: bool = False) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise ObservabilityError(f"Required artifact missing: {path}")
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ObservabilityError(f"Malformed JSON artifact: {path}") from exc

    if not isinstance(payload, dict):
        raise ObservabilityError(f"Artifact must contain a JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ObservabilityError(
                f"Malformed JSONL record at {path}:{line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise ObservabilityError(
                f"JSONL record must be an object at {path}:{line_number}"
            )
        records.append(record)
    return records


def validate_history_chain(records: Sequence[Mapping[str, Any]]) -> None:
    previous_hash = ""
    for index, record in enumerate(records):
        if record.get("previous_record_hash", "") != previous_hash:
            raise ObservabilityError(f"History chain mismatch at record {index}")
        expected_hash = compute_record_hash(record)
        if record.get("record_hash") != expected_hash:
            raise ObservabilityError(f"History hash mismatch at record {index}")
        previous_hash = expected_hash


def validate_dependency_order(jobs: Sequence[Mapping[str, Any]]) -> None:
    completed: set[str] = set()
    seen: set[str] = set()

    for index, job in enumerate(jobs):
        job_id = str(job.get("job_id", "")).strip()
        if not job_id:
            raise ObservabilityError(f"Missing job_id at result index {index}")
        if job_id in seen:
            raise ObservabilityError(f"Duplicate job result: {job_id}")

        dependencies = job.get("depends_on", [])
        if not isinstance(dependencies, list):
            raise ObservabilityError(f"depends_on must be a list for {job_id}")

        unknown_or_late = [item for item in dependencies if item not in completed]
        if unknown_or_late:
            raise ObservabilityError(
                f"Out-of-order dependency for {job_id}: {unknown_or_late}"
            )

        seen.add(job_id)
        completed.add(job_id)


def summarize_cycle(record: Mapping[str, Any]) -> OrchestrationCycleSummary:
    jobs = record.get("jobs", [])
    if not isinstance(jobs, list):
        raise ObservabilityError("Cycle jobs must be a list")

    counts = {
        "SUCCEEDED": 0,
        "DRY_RUN": 0,
        "FAILED": 0,
        "BLOCKED": 0,
        "TIMED_OUT": 0,
    }
    for job in jobs:
        if isinstance(job, dict):
            status = str(job.get("status", ""))
            if status in counts:
                counts[status] += 1

    return OrchestrationCycleSummary(
        run_id=str(record.get("run_id", "")),
        decision_id=str(record.get("decision_id", "")),
        status=str(record.get("status", "")),
        dry_run=bool(record.get("dry_run", True)),
        started_at=str(record.get("started_at", "")),
        finished_at=str(record.get("finished_at", "")),
        elapsed_ms=int(record.get("elapsed_ms", 0)),
        job_count=len(jobs),
        successful_jobs=counts["SUCCEEDED"] + counts["DRY_RUN"],
        failed_jobs=counts["FAILED"],
        blocked_jobs=counts["BLOCKED"],
        timed_out_jobs=counts["TIMED_OUT"],
        record_hash=str(record.get("record_hash", "")),
    )


def latest_cycle_by_status(
    records: Sequence[Mapping[str, Any]],
    status: str,
) -> dict[str, Any] | None:
    for record in reversed(records):
        if record.get("status") == status:
            return asdict(summarize_cycle(record))
    return None


def build_dashboard_snapshot(
    *,
    scheduler_decision_path: Path,
    latest_report_path: Path,
    checkpoint_path: Path,
    history_path: Path,
) -> OrchestrationDashboardSnapshot:
    missing: list[str] = []
    warnings: list[str] = []

    scheduler_decision = read_json(scheduler_decision_path)
    latest_report = read_json(latest_report_path)
    checkpoint = read_json(checkpoint_path)
    history = read_jsonl(history_path)

    for label, value in (
        ("scheduler_decision", scheduler_decision),
        ("latest_report", latest_report),
        ("checkpoint", checkpoint),
    ):
        if value is None:
            missing.append(label)

    history_chain_valid = True
    try:
        validate_history_chain(history)
    except ObservabilityError as exc:
        history_chain_valid = False
        warnings.append(str(exc))

    dependency_chain_valid = True
    if latest_report is not None:
        try:
            jobs = latest_report.get("jobs", [])
            if not isinstance(jobs, list):
                raise ObservabilityError("Latest report jobs must be a list")
            validate_dependency_order(jobs)
        except ObservabilityError as exc:
            dependency_chain_valid = False
            warnings.append(str(exc))

    duplicate_prevention_enabled = bool(
        latest_report
        and isinstance(latest_report.get("duplicate_prevention"), dict)
        and latest_report["duplicate_prevention"].get("enabled") is True
    )

    stale_scheduler_decision = False
    if scheduler_decision is not None and latest_report is not None:
        scheduler_id = str(
            scheduler_decision.get("decision_id")
            or scheduler_decision.get("scheduler_decision_id")
            or ""
        )
        report_id = str(latest_report.get("decision_id", ""))
        stale_scheduler_decision = bool(scheduler_id and scheduler_id != report_id)
        if stale_scheduler_decision:
            warnings.append(
                "Scheduler decision does not match the latest orchestration report"
            )

    return OrchestrationDashboardSnapshot(
        schema_version=SCHEMA_VERSION,
        scheduler_decision=scheduler_decision,
        latest_report=latest_report,
        checkpoint=checkpoint,
        latest_successful_cycle=latest_cycle_by_status(history, "SUCCEEDED"),
        latest_failed_cycle=latest_cycle_by_status(history, "FAILED"),
        history_chain_valid=history_chain_valid,
        duplicate_prevention_enabled=duplicate_prevention_enabled,
        dependency_chain_valid=dependency_chain_valid,
        stale_scheduler_decision=stale_scheduler_decision,
        missing_artifacts=missing,
        warnings=warnings,
    )


__all__ = [
    "ObservabilityError",
    "OrchestrationCycleSummary",
    "OrchestrationDashboardSnapshot",
    "build_dashboard_snapshot",
    "compute_record_hash",
    "latest_cycle_by_status",
    "read_json",
    "read_jsonl",
    "summarize_cycle",
    "validate_dependency_order",
    "validate_history_chain",
]
