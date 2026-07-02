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
    summary: dict[str, Any]
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
            "summary": self.summary,
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


def build_timeline_summary(
    results: tuple[TemporalRuntimeResult, ...],
) -> dict[str, Any]:
    """Build summary statistics for a temporal timeline."""
    if not results:
        return {
            "count": 0,
            "min_score": 0.0,
            "max_score": 0.0,
            "average_score": 0.0,
            "peak_date": None,
            "summary_status": "empty",
        }

    scored = [
        (
            result.evaluation_date,
            float(result.scoring.get("activation_score", 0.0)),
        )
        for result in results
    ]

    scores = [
        score
        for _date, score in scored
    ]

    peak_date, max_score = max(
        scored,
        key=lambda item: item[1],
    )

    return {
        "count": len(results),
        "min_score": min(scores),
        "max_score": max_score,
        "average_score": sum(scores) / len(scores),
        "peak_date": peak_date,
        "summary_status": "computed",
    }


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
        summary=build_timeline_summary(results),
        metadata={
            "runtime": "atlas.temporal_runtime.timeline",
            "timeline_version": "0.1",
        },
    )
