
"""Autonomous Scientific Research Director."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.director.checkpoints import build_checkpoint, checkpoint_status
from atlas.autonomous.director.lifecycle import run_director_lifecycle
from atlas.autonomous.director.state_machine import create_director_state, transition_state
from atlas.autonomous.director.watchdog import inspect_cycle_health


DIRECTOR_VERSION = "1.0.0"


def run_autonomous_director(
    records: list[dict[str, Any]],
    *,
    goal: str = "general_autonomous_research",
    max_schedule_items: int = 3,
    holdout_ratio: float = 0.20,
    export: bool = True,
) -> dict[str, Any]:
    """Run the Autonomous Director."""
    state = create_director_state()
    checkpoints = []

    state = transition_state(state, "observing", note="Loaded research records.")
    checkpoints.append(build_checkpoint("records_loaded", {"success": bool(records), "summary": f"{len(records)} records loaded."}))

    state = transition_state(state, "planning", note=f"Research goal: {goal}.")
    checkpoints.append(build_checkpoint("goal_registered", {"success": True, "summary": goal}))

    state = transition_state(state, "executing", note="Running autonomous lifecycle.")
    lifecycle = run_director_lifecycle(
        records,
        max_schedule_items=max_schedule_items,
        holdout_ratio=holdout_ratio,
        export=export,
    )
    checkpoints.append(build_checkpoint("lifecycle", lifecycle))

    state = transition_state(state, "evaluating", note="Inspecting cycle health.")
    health = inspect_cycle_health(lifecycle.get("cycle", {}))
    checkpoints.append(build_checkpoint("health", health))

    confidence = lifecycle.get("scientific_confidence", {})
    checkpoints.append(build_checkpoint("scientific_confidence", confidence))

    provenance = lifecycle.get("provenance", {})
    checkpoints.append(build_checkpoint("provenance", provenance))

    timeline = lifecycle.get("timeline", {})
    checkpoints.append(build_checkpoint("timeline", timeline))

    state = transition_state(state, "learning", note="Learning cycle completed.")
    learning = (lifecycle.get("cycle", {}) or {}).get("learning_update", {})
    checkpoints.append(build_checkpoint("learning", learning or {"success": False, "summary": "No learning update."}))

    state = transition_state(state, "persisting", note="Memory/export persistence completed.")
    checkpoints.append(build_checkpoint("memory_persistence", lifecycle.get("memory_persistence", {})))

    state = transition_state(state, "completed", note="Director run completed.")

    status = checkpoint_status(checkpoints)

    return {
        "success": True,
        "version": DIRECTOR_VERSION,
        "goal": goal,
        "state": state,
        "health": health,
        "scientific_confidence": lifecycle.get("scientific_confidence", {}),
        "provenance": lifecycle.get("provenance", {}),
        "timeline": lifecycle.get("timeline", {}),
        "checkpoints": status,
        "lifecycle": lifecycle,
        "summary": build_director_summary(goal, lifecycle, health),
    }


def build_director_summary(goal: str, lifecycle: dict[str, Any], health: dict[str, Any]) -> str:
    """Build Director summary."""
    health_label = "healthy" if health.get("healthy") else "warnings"
    return (
        f"Autonomous Director completed goal '{goal}' across "
        f"{lifecycle.get('record_count', 0)} record(s). "
        f"Cycle status: {health_label}. {lifecycle.get('summary', '')}"
    )
