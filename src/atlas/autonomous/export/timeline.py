
"""Timeline export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.json_export import write_json
from atlas.autonomous.export.markdown import write_markdown


def build_timeline_markdown(timeline: dict[str, Any]) -> str:
    """Build timeline markdown."""
    summary = timeline.get("summary", {}) or {}

    lines = [
        "# Atlas Research Timeline",
        "",
        timeline.get("text_summary", "No timeline summary available."),
        "",
        f"- Event count: `{summary.get('event_count', 0)}`",
        f"- First event: `{summary.get('first_event')}`",
        f"- Last event: `{summary.get('last_event')}`",
        "",
        "## Event Types",
        "",
    ]

    for event_type, count in (summary.get("event_type_counts", {}) or {}).items():
        lines.append(f"- `{event_type}`: `{count}`")

    lines.extend(["", "## Events", ""])

    for event in timeline.get("events", []) or []:
        lines.extend([
            f"### {event.get('title')}",
            "",
            f"- Type: `{event.get('event_type')}`",
            f"- Source: `{event.get('source_id')}`",
            f"- Timestamp: `{event.get('timestamp')}`",
            "",
            event.get("summary", ""),
            "",
        ])

    return "\n".join(lines)


def export_timeline(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    """Export timeline report."""
    target = Path(output_dir)
    timeline = report.get("timeline", {}) or {}
    return {
        "timeline_json": write_json(target / "timeline_report.json", timeline),
        "timeline": write_markdown(target / "timeline_report.md", build_timeline_markdown(timeline)),
    }
