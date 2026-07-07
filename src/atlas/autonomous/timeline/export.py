
"""Research timeline export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_TIMELINE_DIR = Path("output/timeline")


def export_timeline_report(
    timeline_report: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_TIMELINE_DIR,
    filename: str = "research_timeline",
) -> dict[str, Any]:
    """Export timeline as JSON and markdown."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    json_path = target / f"{filename}.json"
    md_path = target / f"{filename}.md"

    json_path.write_text(
        json.dumps(timeline_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md_path.write_text(
        build_timeline_markdown(timeline_report),
        encoding="utf-8",
    )

    return {
        "success": True,
        "files": {
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }


def build_timeline_markdown(timeline_report: dict[str, Any]) -> str:
    """Build timeline markdown."""
    summary = timeline_report.get("summary", {}) or {}

    lines = [
        "# Atlas Research Timeline",
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

    for event in timeline_report.get("events", []) or []:
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

    return "\n".join(lines).strip() + "\n"
