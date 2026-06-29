"""Atlas Dataset Manager.

Loads TXT and CSV identity intake files into normalized records.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from atlas.datasets.models import (
    DATASET_MODEL_VERSION,
    DatasetIssue,
    DatasetLoadResult,
    IdentityRecord,
)


REQUIRED_CSV_COLUMNS = {
    "name",
}

SUPPORTED_CSV_COLUMNS = {
    "name",
    "birth_date",
    "birth_time",
    "birth_place",
}


def load_dataset(
    path: Path,
) -> DatasetLoadResult:
    """Load a TXT or CSV dataset."""
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return load_txt_dataset(path)

    if suffix == ".csv":
        return load_csv_dataset(path)

    return DatasetLoadResult(
        version=DATASET_MODEL_VERSION,
        source_file=str(path),
        record_count=0,
        valid_count=0,
        invalid_count=1,
        issue_count=1,
        records=[],
        issues=[
            DatasetIssue(
                row_number=0,
                severity="error",
                code="unsupported_file_type",
                message="Dataset file type is not supported.",
                details={
                    "suffix": suffix,
                    "supported": [".txt", ".csv"],
                },
            )
        ],
    )


def load_txt_dataset(
    path: Path,
) -> DatasetLoadResult:
    """Load one-name-per-line TXT dataset."""
    records: list[IdentityRecord] = []
    issues: list[DatasetIssue] = []

    if not path.exists():
        return missing_file_result(path)

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    for index, line in enumerate(lines, start=1):
        name = normalize_text(line)

        if not name:
            issues.append(
                DatasetIssue(
                    row_number=index,
                    severity="warning",
                    code="empty_name",
                    message="TXT row has no usable name.",
                    details={},
                )
            )
            continue

        records.append(
            IdentityRecord(
                name=name,
                source_file=str(path),
                row_number=index,
            )
        )

    return build_result(
        path=path,
        records=records,
        issues=issues,
    )


def load_csv_dataset(
    path: Path,
) -> DatasetLoadResult:
    """Load CSV identity dataset."""
    records: list[IdentityRecord] = []
    issues: list[DatasetIssue] = []

    if not path.exists():
        return missing_file_result(path)

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        fieldnames = set(reader.fieldnames or [])

        missing_columns = REQUIRED_CSV_COLUMNS - fieldnames

        if missing_columns:
            return DatasetLoadResult(
                version=DATASET_MODEL_VERSION,
                source_file=str(path),
                record_count=0,
                valid_count=0,
                invalid_count=1,
                issue_count=1,
                records=[],
                issues=[
                    DatasetIssue(
                        row_number=0,
                        severity="error",
                        code="missing_required_columns",
                        message="CSV dataset is missing required columns.",
                        details={
                            "missing_columns": sorted(missing_columns),
                            "required_columns": sorted(REQUIRED_CSV_COLUMNS),
                            "found_columns": sorted(fieldnames),
                        },
                    )
                ],
            )

        unsupported_columns = fieldnames - SUPPORTED_CSV_COLUMNS

        if unsupported_columns:
            issues.append(
                DatasetIssue(
                    row_number=0,
                    severity="warning",
                    code="unsupported_columns",
                    message="CSV dataset contains unsupported columns.",
                    details={
                        "unsupported_columns": sorted(unsupported_columns),
                    },
                )
            )

        for index, row in enumerate(reader, start=2):
            record = build_record_from_csv_row(
                row=row,
                path=path,
                row_number=index,
            )

            row_issues = validate_record(record)

            issues.extend(row_issues)

            if has_error(row_issues):
                continue

            records.append(record)

    return build_result(
        path=path,
        records=records,
        issues=issues,
    )


def build_record_from_csv_row(
    *,
    row: dict[str, Any],
    path: Path,
    row_number: int,
) -> IdentityRecord:
    """Build normalized IdentityRecord from CSV row."""
    return IdentityRecord(
        name=normalize_text(row.get("name", "")),
        birth_date=normalize_text(row.get("birth_date", "")),
        birth_time=normalize_birth_time(row.get("birth_time", "")),
        birth_place=normalize_text(row.get("birth_place", "")),
        source_file=str(path),
        row_number=row_number,
    )


def validate_record(
    record: IdentityRecord,
) -> list[DatasetIssue]:
    """Validate one normalized identity record."""
    issues: list[DatasetIssue] = []

    if not record.name:
        issues.append(
            DatasetIssue(
                row_number=record.row_number,
                severity="error",
                code="empty_name",
                message="Identity record has no usable name.",
                details={},
            )
        )

    if record.birth_time.lower() in {"unknown", ""}:
        issues.append(
            DatasetIssue(
                row_number=record.row_number,
                severity="info",
                code="unknown_birth_time",
                message="Birth time is unknown.",
                details={
                    "name": record.name,
                },
            )
        )

    return issues


def build_result(
    *,
    path: Path,
    records: list[IdentityRecord],
    issues: list[DatasetIssue],
) -> DatasetLoadResult:
    """Build dataset load result."""
    error_count = len(
        [
            issue
            for issue in issues
            if issue.severity == "error"
        ]
    )

    return DatasetLoadResult(
        version=DATASET_MODEL_VERSION,
        source_file=str(path),
        record_count=len(records),
        valid_count=len(records),
        invalid_count=error_count,
        issue_count=len(issues),
        records=records,
        issues=issues,
    )


def missing_file_result(
    path: Path,
) -> DatasetLoadResult:
    """Return load result for missing file."""
    return DatasetLoadResult(
        version=DATASET_MODEL_VERSION,
        source_file=str(path),
        record_count=0,
        valid_count=0,
        invalid_count=1,
        issue_count=1,
        records=[],
        issues=[
            DatasetIssue(
                row_number=0,
                severity="error",
                code="missing_file",
                message="Dataset file does not exist.",
                details={
                    "path": str(path),
                },
            )
        ],
    )


def has_error(
    issues: list[DatasetIssue],
) -> bool:
    """Return True if issue list contains an error."""
    return any(
        issue.severity == "error"
        for issue in issues
    )


def normalize_text(
    value: Any,
) -> str:
    """Normalize text input."""
    if value is None:
        return ""

    return str(value).strip()


def normalize_birth_time(
    value: Any,
) -> str:
    """Normalize birth time field."""
    text = normalize_text(value)

    if not text:
        return "Unknown"

    if text.lower() in {"unknown", "unk", "n/a", "na", "none"}:
        return "Unknown"

    return text