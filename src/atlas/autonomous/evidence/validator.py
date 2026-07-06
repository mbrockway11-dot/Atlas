
"""Evidence validation."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = [
    "evidence_id",
    "source_engine",
    "question",
    "observation",
    "variables",
    "sample_size",
    "confidence",
    "effect_size",
    "status",
]


def validate_evidence_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one evidence record."""
    missing = [field for field in REQUIRED_FIELDS if field not in record]

    return {
        "success": not missing,
        "missing": missing,
        "evidence_id": record.get("evidence_id"),
    }


def validate_evidence_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate multiple evidence records."""
    results = [validate_evidence_record(record) for record in records]

    return {
        "success": all(item.get("success") for item in results),
        "record_count": len(records),
        "invalid_count": sum(1 for item in results if not item.get("success")),
        "results": results,
    }
