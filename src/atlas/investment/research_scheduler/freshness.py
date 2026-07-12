"""Atlas research artifact freshness inspection."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atlas.investment.research_scheduler.registry import (
    JOBS,
    ResearchJobSpec,
)


def inspect_all_artifacts(
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Inspect every registered job output."""
    reference_time = (
        now
        if now is not None
        else datetime.now(UTC)
    )

    return [
        inspect_artifact(
            job,
            now=reference_time,
        )
        for job in JOBS
    ]


def inspect_artifact(
    job: ResearchJobSpec,
    *,
    now: datetime,
) -> dict[str, Any]:
    """Inspect one artifact for existence, validity, and freshness."""
    path = job.output_path

    row = {
        "job_id": job.job_id,
        "title": job.title,
        "category": job.category,
        "output_path": str(path),
        "exists": False,
        "valid": False,
        "modified_at": "",
        "age_hours": None,
        "stale_after_hours": (
            job.stale_after_hours
        ),
        "fresh": False,
        "artifact_success": None,
        "artifact_version": "",
        "error": "",
    }

    if (
        not path.exists()
        or not path.is_file()
    ):
        row["error"] = "ARTIFACT_NOT_FOUND"
        return row

    row["exists"] = True

    try:
        modified_at = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=UTC,
        )

        age_hours = (
            now - modified_at
        ).total_seconds() / 3600.0

        row["modified_at"] = (
            modified_at.isoformat()
        )

        row["age_hours"] = round(
            max(
                0.0,
                age_hours,
            ),
            8,
        )

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            row["error"] = (
                "ARTIFACT_ROOT_NOT_OBJECT"
            )
            return row

        row["valid"] = True

        if "success" in payload:
            row["artifact_success"] = bool(
                payload.get("success")
            )

        row["artifact_version"] = str(
            payload.get(
                "version",
                "",
            )
        )

        row["fresh"] = (
            age_hours
            <= job.stale_after_hours
        )

        if (
            row["artifact_success"]
            is False
        ):
            row["error"] = (
                "ARTIFACT_REPORTS_FAILURE"
            )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
        ValueError,
    ) as error:
        row["error"] = (
            f"{type(error).__name__}: {error}"
        )

    return row


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )
