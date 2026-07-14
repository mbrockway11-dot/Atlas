"""Scheduler-to-orchestration reconciliation for G.17 Section 3."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "g17.orchestration.reconciliation.v1"


class ReconciliationError(RuntimeError):
    """Raised when scheduler or orchestration artifacts are malformed."""


@dataclass(frozen=True)
class ReconciliationIssue:
    code: str
    severity: str
    message: str
    job_id: str | None = None


@dataclass(frozen=True)
class ReconciliationReport:
    schema_version: str
    scheduler_decision_id: str
    orchestration_decision_id: str
    status: str
    expected_job_count: int
    actual_job_count: int
    matched_job_count: int
    missing_jobs: list[str]
    duplicate_jobs: list[str]
    unexpected_jobs: list[str]
    out_of_order_jobs: list[str]
    incomplete_dependencies: list[str]
    issues: list[dict[str, Any]]
    paper_only: bool
    live_execution: bool


def _decision_id(payload: Mapping[str, Any]) -> str:
    return str(
        payload.get("decision_id")
        or payload.get("scheduler_decision_id")
        or payload.get("id")
        or ""
    )


def _scheduler_jobs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = (
        payload.get("jobs"),
        payload.get("execution_plan"),
        payload.get("materialized_jobs"),
    )
    jobs = next((item for item in candidates if isinstance(item, list)), [])
    normalized: list[dict[str, Any]] = []

    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise ReconciliationError(f"Scheduler job at index {index} is not an object")
        job_id = str(job.get("job_id") or job.get("id") or "").strip()
        if not job_id:
            raise ReconciliationError(f"Scheduler job at index {index} has no job_id")
        dependencies = job.get("depends_on", [])
        if dependencies is None:
            dependencies = []
        if not isinstance(dependencies, list):
            raise ReconciliationError(f"Scheduler dependencies must be a list: {job_id}")
        normalized.append(
            {
                "job_id": job_id,
                "script": str(job.get("script", "")),
                "depends_on": [str(item) for item in dependencies],
            }
        )
    return normalized


def _orchestration_jobs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    jobs = payload.get("jobs", [])
    if not isinstance(jobs, list):
        raise ReconciliationError("Orchestration jobs must be a list")

    normalized: list[dict[str, Any]] = []
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            raise ReconciliationError(
                f"Orchestration job at index {index} is not an object"
            )
        job_id = str(job.get("job_id", "")).strip()
        if not job_id:
            raise ReconciliationError(
                f"Orchestration job at index {index} has no job_id"
            )
        dependencies = job.get("depends_on", [])
        if not isinstance(dependencies, list):
            raise ReconciliationError(
                f"Orchestration dependencies must be a list: {job_id}"
            )
        normalized.append(
            {
                "job_id": job_id,
                "script": str(job.get("script", "")),
                "depends_on": [str(item) for item in dependencies],
                "status": str(job.get("status", "")),
            }
        )
    return normalized


def _duplicates(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def reconcile(
    scheduler_decision: Mapping[str, Any],
    orchestration_report: Mapping[str, Any],
) -> ReconciliationReport:
    scheduler_id = _decision_id(scheduler_decision)
    orchestration_id = _decision_id(orchestration_report)

    if not scheduler_id:
        raise ReconciliationError("Scheduler decision ID is missing")
    if not orchestration_id:
        raise ReconciliationError("Orchestration decision ID is missing")

    expected_jobs = _scheduler_jobs(scheduler_decision)
    actual_jobs = _orchestration_jobs(orchestration_report)

    expected_ids = [job["job_id"] for job in expected_jobs]
    actual_ids = [job["job_id"] for job in actual_jobs]

    duplicate_jobs = sorted(set(_duplicates(expected_ids) + _duplicates(actual_ids)))
    missing_jobs = sorted(set(expected_ids) - set(actual_ids))
    unexpected_jobs = sorted(set(actual_ids) - set(expected_ids))

    expected_by_id = {job["job_id"]: job for job in expected_jobs}
    actual_by_id = {job["job_id"]: job for job in actual_jobs}

    matched = sorted(set(expected_by_id) & set(actual_by_id))
    incomplete_dependencies: list[str] = []
    out_of_order_jobs: list[str] = []
    completed: set[str] = set()

    for job in actual_jobs:
        job_id = job["job_id"]
        expected = expected_by_id.get(job_id)
        if expected is not None:
            if set(expected["depends_on"]) != set(job["depends_on"]):
                incomplete_dependencies.append(job_id)

        if any(dependency not in completed for dependency in job["depends_on"]):
            out_of_order_jobs.append(job_id)
        completed.add(job_id)

    issues: list[ReconciliationIssue] = []

    if scheduler_id != orchestration_id:
        issues.append(
            ReconciliationIssue(
                code="DECISION_ID_MISMATCH",
                severity="ERROR",
                message="Scheduler and orchestration decision IDs differ",
            )
        )
    for job_id in missing_jobs:
        issues.append(
            ReconciliationIssue(
                code="MISSING_JOB",
                severity="ERROR",
                message="Expected scheduler job is missing from orchestration",
                job_id=job_id,
            )
        )
    for job_id in duplicate_jobs:
        issues.append(
            ReconciliationIssue(
                code="DUPLICATE_JOB",
                severity="ERROR",
                message="Duplicate job ID detected",
                job_id=job_id,
            )
        )
    for job_id in unexpected_jobs:
        issues.append(
            ReconciliationIssue(
                code="UNEXPECTED_JOB",
                severity="ERROR",
                message="Orchestration contains a job not present in scheduler output",
                job_id=job_id,
            )
        )
    for job_id in incomplete_dependencies:
        issues.append(
            ReconciliationIssue(
                code="DEPENDENCY_MISMATCH",
                severity="ERROR",
                message="Scheduler and orchestration dependencies differ",
                job_id=job_id,
            )
        )
    for job_id in out_of_order_jobs:
        issues.append(
            ReconciliationIssue(
                code="OUT_OF_ORDER_EXECUTION",
                severity="ERROR",
                message="Job appears before one or more dependencies",
                job_id=job_id,
            )
        )

    safety = orchestration_report.get("safety", {})
    paper_only = bool(isinstance(safety, dict) and safety.get("paper_only") is True)
    live_execution = bool(
        isinstance(safety, dict) and safety.get("live_execution") is True
    )

    if not paper_only or live_execution:
        issues.append(
            ReconciliationIssue(
                code="SAFETY_BOUNDARY_VIOLATION",
                severity="CRITICAL",
                message="Orchestration report violates the paper-only boundary",
            )
        )

    status = "PASS" if not issues else "FAIL"

    return ReconciliationReport(
        schema_version=SCHEMA_VERSION,
        scheduler_decision_id=scheduler_id,
        orchestration_decision_id=orchestration_id,
        status=status,
        expected_job_count=len(expected_jobs),
        actual_job_count=len(actual_jobs),
        matched_job_count=len(matched),
        missing_jobs=missing_jobs,
        duplicate_jobs=duplicate_jobs,
        unexpected_jobs=unexpected_jobs,
        out_of_order_jobs=sorted(set(out_of_order_jobs)),
        incomplete_dependencies=sorted(set(incomplete_dependencies)),
        issues=[asdict(issue) for issue in issues],
        paper_only=paper_only,
        live_execution=live_execution,
    )


__all__ = [
    "ReconciliationError",
    "ReconciliationIssue",
    "ReconciliationReport",
    "reconcile",
]
