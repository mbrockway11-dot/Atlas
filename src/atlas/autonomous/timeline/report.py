
"""Research Timeline report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.timeline.builder import (
    build_timeline_from_campaign,
    build_timeline_from_director,
)
from atlas.autonomous.timeline.export import export_timeline_report
from atlas.autonomous.timeline.summary import summarize_timeline


TIMELINE_VERSION = "1.0.0"


def build_research_timeline_report(
    source_report: dict[str, Any],
    *,
    source_type: str = "director",
    export: bool = False,
) -> dict[str, Any]:
    """Build research timeline report."""
    if source_type == "campaign":
        events = build_timeline_from_campaign(source_report)
    else:
        events = build_timeline_from_director(source_report)

    summary = summarize_timeline(events)

    report = {
        "success": True,
        "version": TIMELINE_VERSION,
        "source_type": source_type,
        "events": events,
        "summary": summary,
        "text_summary": (
            f"Research Timeline contains {summary.get('event_count', 0)} event(s) "
            f"across {len(summary.get('event_type_counts', {}) or {})} event type(s)."
        ),
    }

    if export:
        report["export"] = export_timeline_report(report)

    return report
