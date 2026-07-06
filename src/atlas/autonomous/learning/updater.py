
"""Autonomous learning updater."""

from __future__ import annotations

from typing import Any


def build_learning_update(
    *,
    evidence: dict[str, Any] | None = None,
    memory: dict[str, Any] | None = None,
    experiment_plan: dict[str, Any] | None = None,
    scheduler_report: dict[str, Any] | None = None,
    theory_report: dict[str, Any] | None = None,
    falsification_report: dict[str, Any] | None = None,
    prediction_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build learning update from autonomous research outputs."""
    signals = []

    if evidence:
        signals.append({
            "source": "evidence",
            "signal": "evidence_integrated",
            "strength": evidence_strength(evidence),
        })

    if memory:
        signals.append({
            "source": "memory",
            "signal": "research_memory_updated",
            "strength": memory_strength(memory),
        })

    if experiment_plan:
        signals.append({
            "source": "experiment_generator",
            "signal": "new_questions_generated",
            "strength": experiment_strength(experiment_plan),
        })

    if scheduler_report:
        signals.append({
            "source": "scheduler",
            "signal": "questions_scheduled",
            "strength": scheduler_strength(scheduler_report),
        })

    if theory_report:
        signals.append({
            "source": "theory",
            "signal": "theory_candidates_updated",
            "strength": theory_strength(theory_report),
        })

    if falsification_report:
        signals.append({
            "source": "falsification",
            "signal": "theories_challenged",
            "strength": falsification_strength(falsification_report),
        })

    if prediction_report:
        signals.append({
            "source": "prediction",
            "signal": "prediction_accuracy_measured",
            "strength": prediction_strength(prediction_report),
        })

    mean_strength = (
        sum(item["strength"] for item in signals) / len(signals)
        if signals else 0.0
    )

    return {
        "success": True,
        "signal_count": len(signals),
        "signals": signals,
        "learning_score": round(mean_strength, 6),
        "learning_label": learning_label(mean_strength),
        "summary": build_summary(signals, mean_strength),
    }


def evidence_strength(evidence: dict[str, Any]) -> float:
    """Score evidence contribution."""
    records = evidence.get("records", {}) if isinstance(evidence.get("records"), dict) else {}
    count = len(records) if records else int(evidence.get("record_count") or 0)
    return min(1.0, count / 20)


def memory_strength(memory: dict[str, Any]) -> float:
    """Score memory contribution."""
    count = (
        len(memory.get("experiments", {}) or {})
        + len(memory.get("evidence", {}) or {})
        + len(memory.get("hypotheses", {}) or {})
    )
    return min(1.0, count / 25)


def experiment_strength(plan: dict[str, Any]) -> float:
    """Score experiment generation."""
    return min(1.0, int(plan.get("selected_count") or 0) / 10)


def scheduler_strength(report: dict[str, Any]) -> float:
    """Score scheduled execution."""
    schedule = report.get("schedule", {}) or {}
    return min(1.0, int(schedule.get("scheduled_count") or 0) / 5)


def theory_strength(report: dict[str, Any]) -> float:
    """Score theory formation."""
    promoted = int(report.get("promoted_count") or 0)
    candidates = int(report.get("candidate_count") or 0)
    return min(1.0, promoted * 0.35 + candidates * 0.10)


def falsification_strength(report: dict[str, Any]) -> float:
    """Score falsification activity."""
    challenged = int(report.get("challenge_count") or 0)
    return min(1.0, challenged / 5)


def prediction_strength(report: dict[str, Any]) -> float:
    """Score prediction validation."""
    if not report.get("success"):
        return 0.0

    scores = ((report.get("benchmark", {}) or {}).get("scores", {}) or {})
    label = scores.get("accuracy_label")

    return {
        "high_accuracy": 1.0,
        "moderate_accuracy": 0.75,
        "low_accuracy": 0.45,
        "poor_accuracy": 0.20,
    }.get(label, 0.30)


def learning_label(score: float) -> str:
    """Label learning state."""
    if score >= 0.80:
        return "strong_learning_cycle"
    if score >= 0.55:
        return "active_learning_cycle"
    if score >= 0.30:
        return "partial_learning_cycle"
    return "weak_learning_cycle"


def build_summary(signals: list[dict[str, Any]], score: float) -> str:
    """Build learning summary."""
    return (
        f"Autonomous Learning integrated {len(signals)} signal(s). "
        f"Learning score: {score:.3f} ({learning_label(score)})."
    )
