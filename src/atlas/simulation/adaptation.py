
"""Adaptation modeling."""

from __future__ import annotations

from typing import Any


def build_adaptation_model(decisions: dict[str, Any], recovery: dict[str, Any]) -> dict[str, Any]:
    """Build adaptation model."""
    likely = decisions.get("likely_action") or {}

    return {
        "adaptation_target": likely.get("action", "unresolved"),
        "learning_loop": [
            "environmental pressure",
            "state activation",
            "decision response",
            "recovery path",
            "baseline update",
        ],
        "expected_adaptation": recovery.get("recovery_mode", "unresolved"),
    }
