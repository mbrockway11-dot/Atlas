
"""Autonomous scheduler executor.

This module converts scheduled experiment questions into Discovery-compatible
extra question payloads. Full execution is delegated to the Discovery Engine
or Research Orchestrator.
"""

from __future__ import annotations

from typing import Any

from atlas.discovery import build_discovery_report


def execute_scheduled_questions(
    records: list[dict[str, Any]],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    """Execute scheduled questions through Discovery Engine."""
    questions = []

    for item in schedule.get("scheduled_items", []) or []:
        questions.append(
            {
                "question_id": item.get("question_id"),
                "question": item.get("question"),
                "x_field": item.get("x_field"),
                "y_field": item.get("y_field"),
                "kind": item.get("kind", "numeric_correlation"),
            }
        )

    report = build_discovery_report(
        records,
        extra_questions=questions,
    )

    return {
        "success": True,
        "scheduled_count": len(questions),
        "discovery": report,
        "summary": f"Executed {len(questions)} scheduled question(s) through Discovery Engine.",
    }
