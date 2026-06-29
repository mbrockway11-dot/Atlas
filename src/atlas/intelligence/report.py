"""Atlas Report Engine.

Convert AtlasInterpretation objects into readable reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from atlas.intelligence.interpreter import (
    AtlasInterpretation,
    InterpretationSection,
    atlas_interpretation_to_dict,
)


REPORT_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class AtlasReport:
    """Rendered Atlas report."""

    version: str
    name: str
    title: str
    markdown: str
    summary: dict[str, Any]


def build_atlas_report(
    interpretation: AtlasInterpretation,
) -> AtlasReport:
    """Build Markdown Atlas report from interpretation."""

    title = f"Atlas Intelligence Report: {interpretation.name}"

    markdown = "\n".join(
        [
            f"# {title}",
            "",
            f"**Version:** {REPORT_ENGINE_VERSION}",
            "",
            render_report_summary(interpretation),
            "",
            *[
                render_section(section)
                for section in interpretation.sections
            ],
        ]
    )

    return AtlasReport(
        version=REPORT_ENGINE_VERSION,
        name=interpretation.name,
        title=title,
        markdown=markdown,
        summary={
            "section_count": len(interpretation.sections),
            "source_interpreter_version": interpretation.version,
        },
    )


def render_report_summary(
    interpretation: AtlasInterpretation,
) -> str:
    """Render report-level summary."""

    return "\n".join(
        [
            "## Executive Summary",
            "",
            f"- Identity: {interpretation.name}",
            f"- Sections: {len(interpretation.sections)}",
            f"- Temporal available: {interpretation.summary.get('has_temporal', False)}",
            f"- ACF available: {interpretation.summary.get('has_acf', False)}",
            f"- Intake available: {interpretation.summary.get('has_intake', False)}",
        ]
    )


def render_section(
    section: InterpretationSection,
) -> str:
    """Render one interpretation section."""

    lines = [
        f"## {section.title}",
        "",
        section.summary,
        "",
    ]

    for bullet in section.bullets:
        lines.append(f"- {bullet}")

    return "\n".join(lines)


def atlas_report_to_dict(
    report: AtlasReport,
) -> dict[str, Any]:
    """Convert AtlasReport to dictionary."""

    return asdict(report)


def export_atlas_report_markdown(
    report: AtlasReport,
    output_path: Path,
) -> None:
    """Export report as Markdown."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        report.markdown,
        encoding="utf-8",
    )


def export_atlas_report_json(
    report: AtlasReport,
    interpretation: AtlasInterpretation,
    output_path: Path,
) -> None:
    """Export report and source interpretation as JSON."""

    import json

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "report": atlas_report_to_dict(report),
        "interpretation": atlas_interpretation_to_dict(interpretation),
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )