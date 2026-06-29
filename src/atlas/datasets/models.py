"""Atlas Dataset Manager models."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


DATASET_MODEL_VERSION = "1.0"


@dataclass(frozen=True)
class IdentityRecord:
    """Normalized identity intake record."""

    name: str
    birth_date: str = ""
    birth_time: str = "Unknown"
    birth_place: str = ""
    source_file: str = ""
    row_number: int = 0


@dataclass(frozen=True)
class DatasetIssue:
    """Validation issue for one dataset row."""

    row_number: int
    severity: str
    code: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class DatasetLoadResult:
    """Result of loading and validating a dataset."""

    version: str
    source_file: str
    record_count: int
    valid_count: int
    invalid_count: int
    issue_count: int
    records: list[IdentityRecord]
    issues: list[DatasetIssue]


def identity_record_to_dict(
    record: IdentityRecord,
) -> dict[str, Any]:
    """Convert IdentityRecord to dictionary."""
    return asdict(record)


def dataset_issue_to_dict(
    issue: DatasetIssue,
) -> dict[str, Any]:
    """Convert DatasetIssue to dictionary."""
    return asdict(issue)


def dataset_load_result_to_dict(
    result: DatasetLoadResult,
) -> dict[str, Any]:
    """Convert DatasetLoadResult to dictionary."""
    return {
        "version": result.version,
        "source_file": result.source_file,
        "record_count": result.record_count,
        "valid_count": result.valid_count,
        "invalid_count": result.invalid_count,
        "issue_count": result.issue_count,
        "records": [
            identity_record_to_dict(record)
            for record in result.records
        ],
        "issues": [
            dataset_issue_to_dict(issue)
            for issue in result.issues
        ],
    }