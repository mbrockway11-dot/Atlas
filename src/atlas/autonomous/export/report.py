
"""Autonomous export report service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.writer import export_autonomous_report


EXPORT_VERSION = "1.0.0"


def build_autonomous_export_report(
    autonomous_report: dict[str, Any],
    *,
    output_dir: str | Path = "output/autonomous",
) -> dict[str, Any]:
    """Build export report for autonomous outputs."""
    export = export_autonomous_report(
        autonomous_report,
        output_dir=output_dir,
    )

    return {
        "success": True,
        "version": EXPORT_VERSION,
        "export": export,
        "summary": (
            f"Autonomous export wrote {len(export.get('files', {}))} file(s) "
            f"to {export.get('output_dir')}."
        ),
    }
