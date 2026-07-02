"""Temporal runtime forecast helpers."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from atlas.temporal_runtime.timeline import TemporalTimeline, evaluate_timeline


def evaluate_forecast(
    *,
    profile_key: str,
    css: dict[str, Any],
    start_date: str,
    days: int,
) -> TemporalTimeline:
    """Evaluate a forward forecast window."""
    if days <= 0:
        raise ValueError("days must be greater than zero")

    start = date.fromisoformat(start_date)
    end = start + timedelta(days=days - 1)

    return evaluate_timeline(
        profile_key=profile_key,
        css=css,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
