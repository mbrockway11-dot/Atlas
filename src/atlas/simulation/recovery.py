
"""Recovery path modeling."""

from __future__ import annotations

from typing import Any


def build_recovery_path(decisions: dict[str, Any]) -> dict[str, Any]:
    """Build recovery path from likely action."""
    likely = decisions.get("likely_action") or {}
    action = likely.get("action", "")

    if action in {"structure_plan", "protect_continuity", "sequence_work"}:
        path = ["restore scope", "sequence actions", "rebuild continuity", "return to stable builder"]
    elif action in {"explain_publicly", "teach_framework", "publish_artifact"}:
        path = ["clarify message", "deliver artifact", "collect feedback", "reintegrate into structure"]
    elif action in {"compress_into_model", "build_symbolic_artifact", "name_the_pattern"}:
        path = ["externalize pattern", "simplify symbols", "test against reality", "ground model"]
    else:
        path = ["reduce noise", "identify active pressure", "choose next stabilizing action"]

    return {
        "recovery_path": path,
        "recovery_mode": path[-1],
    }
