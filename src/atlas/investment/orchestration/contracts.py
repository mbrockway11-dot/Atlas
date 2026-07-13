"""Canonical contracts for autonomous Atlas paper orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


ORCHESTRATION_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True)
class ApprovedCommand:
    """One statically approved command template."""

    job_name: str
    argv_prefix: tuple[str, ...]
    timeout_seconds: int
    paper_only: bool = True
    allow_additional_arguments: bool = False

    def __post_init__(self) -> None:
        job_name = str(
            self.job_name
        ).strip().upper()

        argv_prefix = tuple(
            str(value)
            for value
            in self.argv_prefix
        )

        timeout_seconds = int(
            self.timeout_seconds
        )

        if not job_name:
            raise ValueError(
                "APPROVED_COMMAND_JOB_REQUIRED"
            )

        if not argv_prefix:
            raise ValueError(
                "APPROVED_COMMAND_ARGV_REQUIRED"
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "APPROVED_COMMAND_TIMEOUT_INVALID"
            )

        object.__setattr__(
            self,
            "job_name",
            job_name,
        )

        object.__setattr__(
            self,
            "argv_prefix",
            argv_prefix,
        )

        object.__setattr__(
            self,
            "timeout_seconds",
            timeout_seconds,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JobExecutionResult:
    """Normalized result for one orchestration job."""

    job_name: str
    status: str
    success: bool
    started_at: str
    completed_at: str
    elapsed_ms: float
    return_code: int | None
    stdout: str
    stderr: str
    error: str
    command: tuple[str, ...]
    result_id: str
    blocked_by: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)

        payload["command"] = list(
            self.command
        )

        payload["blocked_by"] = list(
            self.blocked_by
        )

        return payload


@dataclass(frozen=True)
class OrchestrationPolicy:
    """Safety and runtime policy for one orchestration cycle."""

    fail_fast: bool = True
    maximum_jobs: int = 20
    maximum_output_characters: int = 20_000
    require_scheduler_contract: bool = True
    require_paper_only: bool = True

    def __post_init__(self) -> None:
        if int(
            self.maximum_jobs
        ) <= 0:
            raise ValueError(
                "ORCHESTRATION_MAXIMUM_JOBS_INVALID"
            )

        if int(
            self.maximum_output_characters
        ) <= 0:
            raise ValueError(
                "ORCHESTRATION_OUTPUT_LIMIT_INVALID"
            )


@dataclass(frozen=True)
class OrchestrationReport:
    """Complete result of one autonomous paper orchestration cycle."""

    success: bool
    version: str
    run_id: str
    decision_id: str
    started_at: str
    completed_at: str
    status: str
    counts: Mapping[str, int]
    results: tuple[Mapping[str, Any], ...]
    errors: tuple[str, ...] = ()
    contract: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "version": self.version,
            "run_id": self.run_id,
            "decision_id": self.decision_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "counts": dict(
                self.counts
            ),
            "results": [
                dict(result)
                for result in self.results
            ],
            "errors": list(
                self.errors
            ),
            "contract": dict(
                self.contract
            ),
        }


__all__ = [
    "ApprovedCommand",
    "JobExecutionResult",
    "ORCHESTRATION_CONTRACT_VERSION",
    "OrchestrationPolicy",
    "OrchestrationReport",
]
