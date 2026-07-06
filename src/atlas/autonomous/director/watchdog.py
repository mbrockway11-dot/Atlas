
"""Autonomous Director watchdog."""

from __future__ import annotations

from typing import Any


def inspect_cycle_health(cycle: dict[str, Any]) -> dict[str, Any]:
    """Inspect autonomous cycle health."""
    warnings = []

    learning = cycle.get("learning_update", {}) or {}
    prediction = cycle.get("prediction", {}) or {}
    theory = cycle.get("theory", {}) or {}

    if float(learning.get("learning_score") or 0.0) < 0.30:
        warnings.append("Learning score is weak.")

    if theory.get("promoted_count", 0) == 0:
        warnings.append("No theories were promoted.")

    if prediction and not prediction.get("success"):
        warnings.append("Prediction challenge did not run successfully.")

    return {
        "success": True,
        "healthy": not warnings,
        "warning_count": len(warnings),
        "warnings": warnings,
    }
