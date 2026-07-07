
"""Autonomous export coordinator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.export.confidence import export_confidence
from atlas.autonomous.export.prediction import export_prediction
from atlas.autonomous.export.provenance import export_provenance
from atlas.autonomous.export.summary import export_summary
from atlas.autonomous.export.theory import export_theory
from atlas.autonomous.export.timeline import export_timeline


DEFAULT_EXPORT_DIR = Path("output/autonomous")


def export_autonomous_report(
    report: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    """Export autonomous report package."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    files = {}
    files.update(export_summary(report, target))
    files.update(export_theory(report, target))
    files.update(export_prediction(report, target))
    files.update(export_confidence(report, target))
    files.update(export_provenance(report, target))
    files.update(export_timeline(report, target))

    return {
        "success": True,
        "output_dir": str(target),
        "files": files,
    }
