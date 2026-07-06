
"""Autonomous research queue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def create_research_queue() -> dict[str, Any]:
    """Create empty research queue."""
    return {
        "success": True,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "items": [],
    }


def enqueue_question(
    queue: dict[str, Any],
    question: dict[str, Any],
    *,
    priority: float | None = None,
) -> dict[str, Any]:
    """Add question to queue."""
    item = {
        "queue_id": f"queue::{question.get('question_id')}",
        "question_id": question.get("question_id"),
        "question": question.get("question"),
        "x_field": question.get("x_field"),
        "y_field": question.get("y_field"),
        "kind": question.get("kind"),
        "priority": float(priority if priority is not None else question.get("rank_score", 0.0)),
        "status": "queued",
        "created_at": utc_now(),
    }

    queue.setdefault("items", []).append(item)
    queue["updated_at"] = utc_now()
    return queue


def enqueue_many(queue: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    """Add many questions to queue."""
    for question in questions:
        queue = enqueue_question(queue, question)
    return queue


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
