
"""Read sigil-engine market outputs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


DEFAULT_SIGNAL_PATHS = [
    Path("output/live_signal_v5.csv"),
    Path("output/backfilled_live_signals_v5.csv"),
    Path("output/v32_ab_live_signal_snapshot.csv"),
    Path("output/v32_ab_live_execution.csv"),
]


def find_signal_file(paths: list[str | Path] | None = None) -> Path | None:
    """Find first existing signal file."""
    candidates = [Path(p) for p in (paths or DEFAULT_SIGNAL_PATHS)]
    for path in candidates:
        if path.exists():
            return path
    return None


def read_latest_signal(path: str | Path | None = None) -> dict[str, Any]:
    """Read latest sigil-engine CSV signal."""
    signal_path = Path(path) if path else find_signal_file()

    if signal_path is None or not signal_path.exists():
        return {
            "success": False,
            "error": "No sigil-engine signal file found.",
            "path": str(signal_path) if signal_path else "",
        }

    with signal_path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return {
            "success": False,
            "error": "Signal file is empty.",
            "path": str(signal_path),
        }

    latest = rows[-1]
    latest["_source_path"] = str(signal_path)

    return {
        "success": True,
        "path": str(signal_path),
        "row_count": len(rows),
        "signal": latest,
    }
