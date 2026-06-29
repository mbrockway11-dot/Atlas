"""Atlas Research Session.

Orchestrate a complete Atlas research run for one profile.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from atlas.identity_bridge import (
    AtlasIdentity,
    atlas_identity_to_dict,
    build_atlas_identity,
)
from atlas.intelligence.interpreter import (
    AtlasInterpretation,
    atlas_interpretation_to_dict,
    interpret_identity,
)
from atlas.intelligence.report import (
    AtlasReport,
    atlas_report_to_dict,
    build_atlas_report,
)


RESEARCH_SESSION_VERSION = "1.0"


@dataclass(frozen=True)
class ResearchSession:
    """Complete Atlas research session."""

    version: str
    name: str
    profile_path: str
    transit_date: str | None
    identity: AtlasIdentity
    interpretation: AtlasInterpretation
    report: AtlasReport
    summary: dict[str, Any]


def build_research_session(
    profile_dir: Path,
    *,
    transit_date: str | None = None,
) -> ResearchSession:
    """Build complete research session for one profile."""

    identity = build_atlas_identity(
        profile_dir,
        transit_date=transit_date,
    )

    interpretation = interpret_identity(identity)

    report = build_atlas_report(interpretation)

    return ResearchSession(
        version=RESEARCH_SESSION_VERSION,
        name=identity.name,
        profile_path=str(profile_dir),
        transit_date=transit_date,
        identity=identity,
        interpretation=interpretation,
        report=report,
        summary={
            "name": identity.name,
            "has_identity": True,
            "has_interpretation": True,
            "has_report": True,
            "section_count": interpretation.summary.get("section_count", 0),
            "temporal_layers": identity.summary.get("temporal_layers", []),
        },
    )


def research_session_to_dict(
    session: ResearchSession,
) -> dict[str, Any]:
    """Convert ResearchSession to dictionary."""

    return {
        "version": session.version,
        "name": session.name,
        "profile_path": session.profile_path,
        "transit_date": session.transit_date,
        "identity": atlas_identity_to_dict(session.identity),
        "interpretation": atlas_interpretation_to_dict(session.interpretation),
        "report": atlas_report_to_dict(session.report),
        "summary": session.summary,
    }


def export_research_session_json(
    session: ResearchSession,
    output_path: Path,
) -> None:
    """Export complete research session as JSON."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            research_session_to_dict(session),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def export_research_session_markdown(
    session: ResearchSession,
    output_path: Path,
) -> None:
    """Export research session report as Markdown."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        session.report.markdown,
        encoding="utf-8",
    )