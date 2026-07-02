"""Temporal runtime timeline evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from atlas.temporal_runtime.engine import (
    TemporalRuntimeEngine,
    TemporalRuntimeResult,
)


@dataclass(frozen=True)
class TemporalTimeline:
    """Timeline result for multiple runtime evaluations."""

    profile_key: str
    start_date: str
    end_date: str
    results: tuple[TemporalRuntimeResult, ...]
    metadata: dict[str, Any]

    @property
    def count(self) -> int:
        """Return number of timeline evaluations."""
        return len(self.results)

    def to_dict(self) -> dict[str, Any]:
        """Return serializable timeline payload."""
        return {
            "profile_key": self.profile_key,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "count": self.count,
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "metadata": self.metadata,
        }


def build_date_range(
    *,
    start_date: str,
    end_date: str,
) -> list[str]:
    """Build inclusive date range."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if end < start:
        raise ValueError("end_date must be greater than or equal to start_date")

    current = start
    dates: list[str] = []

    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    return dates


def evaluate_timeline(
    *,
    profile_key: str,
    css: dict[str, Any],
    start_date: str,
    end_date: str,
    engine: TemporalRuntimeEngine | None = None,
) -> TemporalTimeline:
    """Evaluate one compiled CSS over an inclusive date range."""
    runtime = engine or TemporalRuntimeEngine()

    dates = build_date_range(
        start_date=start_date,
        end_date=end_date,
    )

    results = tuple(
        runtime.evaluate(
            profile_key=profile_key,
            css=css,
            evaluation_date=evaluation_date,
        )
        for evaluation_date in dates
    )

    return TemporalTimeline(
        profile_key=profile_key,
        start_date=start_date,
        end_date=end_date,
        results=results,
        metadata={
            "runtime": "atlas.temporal_runtime.timeline",
            "timeline_version": "0.1",
        },
    )
