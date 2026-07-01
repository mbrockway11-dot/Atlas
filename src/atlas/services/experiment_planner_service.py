"""Atlas Experiment Planner service.

Ranks the highest-value next research actions from falsification output.

Purpose:
- Convert falsification cases into executable research experiments.
- Estimate confidence gain.
- Estimate effort.
- Rank actions by value.
- Produce a research plan.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.falsification_engine_service import build_falsification_payload


EXPERIMENT_PLANNER_VERSION = "1.0"


def list_experiment_planner_profiles() -> list[str]:
    """Return profiles available for experiment planning."""
    return list_saved_profiles()


def build_experiment_plan_payload(query: str) -> dict[str, Any]:
    """Build experiment plan from a natural-language query."""
    falsification_payload = build_falsification_payload(query)

    if not falsification_payload.get("success"):
        return failure_payload(
            query=query,
            errors=falsification_payload.get("errors", []),
            warnings=falsification_payload.get("warnings", []),
        )

    falsification_model = falsification_payload.get("data", {}).get(
        "falsification_model",
        {},
    )

    experiment_model = build_experiment_model(
        query=query,
        falsification_model=falsification_model,
    )

    return {
        "success": True,
        "version": EXPERIMENT_PLANNER_VERSION,
        "query": query,
        "errors": falsification_payload.get("errors", []),
        "warnings": falsification_payload.get("warnings", []),
        "data": {
            "experiment_model": experiment_model,
            "falsification_summary": summarize_falsification_payload(
                falsification_payload,
            ),
        },
        "exports": {
            "experiment_json": experiment_model,
            "markdown": render_experiment_plan_markdown(experiment_model),
        },
        "metrics": build_experiment_metrics(
            experiment_model,
            falsification_payload,
        ),
    }


def build_experiment_model(
    *,
    query: str,
    falsification_model: dict[str, Any],
) -> dict[str, Any]:
    """Build experiment model."""
    cases = falsification_model.get("cases", [])

    experiments = []

    for case in cases:
        experiments.extend(build_experiments_from_case(case))

    ranked = rank_experiments(experiments)
    phases = build_experiment_phases(ranked)

    return {
        "version": EXPERIMENT_PLANNER_VERSION,
        "query": query,
        "subject": falsification_model.get("subject", "unknown"),
        "intent": falsification_model.get("intent", "unknown"),
        "scope": falsification_model.get("scope", "unknown"),
        "definition": (
            "Experiment plans rank the next best research actions by expected "
            "confidence gain, falsification value, and estimated effort."
        ),
        "experiments": ranked,
        "recommended_next_experiment": ranked[0] if ranked else {},
        "phases": phases,
        "summary": {
            "experiment_count": len(ranked),
            "phase_count": len(phases),
            "recommended_next_experiment": (
                ranked[0].get("title", "n/a") if ranked else "n/a"
            ),
            "highest_value_score": (
                ranked[0].get("value_score", {}).get("score", 0)
                if ranked
                else 0
            ),
        },
    }


def build_experiments_from_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Build experiments from one falsification case."""
    experiments = []

    hypothesis_title = case.get("hypothesis_title", "Untitled Hypothesis")
    pressure = case.get("falsification_pressure", {})
    observations = case.get("required_observations", [])
    repairs = case.get("repair_actions", [])
    signals = case.get("disconfirming_signals", [])

    source_items = observations or repairs

    for index, item in enumerate(source_items, start=1):
        experiment_type = classify_experiment_type(item)
        effort = estimate_effort(item, experiment_type)
        gain = estimate_confidence_gain(item, pressure, experiment_type)
        falsification_value = estimate_falsification_value(
            item=item,
            pressure=pressure,
            signals=signals,
        )

        experiments.append(
            {
                "id": build_experiment_id(hypothesis_title, index),
                "title": build_experiment_title(item, experiment_type),
                "hypothesis_title": hypothesis_title,
                "description": item,
                "experiment_type": experiment_type,
                "estimated_effort": effort,
                "expected_confidence_gain": gain,
                "falsification_value": falsification_value,
                "value_score": build_value_score(
                    gain=gain,
                    effort=effort,
                    falsification_value=falsification_value,
                ),
                "success_criteria": build_success_criteria(item, experiment_type),
                "failure_criteria": build_failure_criteria(item, experiment_type),
                "outputs": build_expected_outputs(item, experiment_type),
                "source_pressure": pressure,
                "status": "not_started",
            }
        )

    return dedupe_experiments(experiments)


def classify_experiment_type(text: str) -> str:
    """Classify experiment type."""
    lowered = text.lower()

    if contains_any(lowered, ["moon", "nakshatra", "birth", "dasha", "temporal", "transit"]):
        return "temporal_repair"

    if contains_any(lowered, ["graph", "topology", "motif", "node", "edge", "cig", "stg"]):
        return "graph_repair"

    if contains_any(lowered, ["evidence", "claim", "narrative", "support"]):
        return "evidence_audit"

    if contains_any(lowered, ["similarity", "relationship", "overlap", "morphology", "pair"]):
        return "relationship_validation"

    if contains_any(lowered, ["population", "neighbors", "baseline", "cluster", "cohort"]):
        return "population_baseline"

    return "general_research"


def estimate_effort(text: str, experiment_type: str) -> dict[str, Any]:
    """Estimate experiment effort."""
    base = {
        "temporal_repair": 0.70,
        "graph_repair": 0.60,
        "evidence_audit": 0.45,
        "relationship_validation": 0.50,
        "population_baseline": 0.65,
        "general_research": 0.50,
    }.get(experiment_type, 0.50)

    lowered = text.lower()

    if contains_any(lowered, ["inspect", "open", "check", "compare"]):
        base -= 0.15

    if contains_any(lowered, ["rebuild", "resolve", "verify", "recompute", "enrich"]):
        base += 0.15

    score = clamp(base)

    return {
        "score": round(score, 4),
        "label": effort_label(score),
    }


def estimate_confidence_gain(
    text: str,
    pressure: dict[str, Any],
    experiment_type: str,
) -> dict[str, Any]:
    """Estimate expected confidence gain."""
    pressure_score = safe_float(pressure.get("score"))

    base = {
        "temporal_repair": 0.18,
        "graph_repair": 0.15,
        "evidence_audit": 0.12,
        "relationship_validation": 0.13,
        "population_baseline": 0.14,
        "general_research": 0.08,
    }.get(experiment_type, 0.08)

    gain = clamp(base + pressure_score * 0.20)

    return {
        "score": round(gain, 4),
        "percent_points": round(gain * 100, 2),
        "label": gain_label(gain),
    }


def estimate_falsification_value(
    *,
    item: str,
    pressure: dict[str, Any],
    signals: list[str],
) -> dict[str, Any]:
    """Estimate falsification value."""
    pressure_score = safe_float(pressure.get("score"))
    signal_bonus = min(len(signals) * 0.025, 0.15)

    item_bonus = 0.0
    lowered = item.lower()

    if contains_any(lowered, ["resolve", "verify", "recompute", "compare before and after"]):
        item_bonus += 0.15

    if contains_any(lowered, ["directly", "evidence", "counts", "shared", "edge"]):
        item_bonus += 0.08

    score = clamp(pressure_score * 0.65 + signal_bonus + item_bonus)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": value_label(score),
    }


def build_value_score(
    *,
    gain: dict[str, Any],
    effort: dict[str, Any],
    falsification_value: dict[str, Any],
) -> dict[str, Any]:
    """Build final experiment value score."""
    gain_score = safe_float(gain.get("score"))
    effort_score = safe_float(effort.get("score"))
    falsification_score = safe_float(falsification_value.get("score"))

    score = clamp(
        gain_score * 0.45
        + falsification_score * 0.45
        + (1.0 - effort_score) * 0.10
    )

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": value_label(score),
    }


def build_experiment_title(item: str, experiment_type: str) -> str:
    """Build experiment title."""
    prefix = {
        "temporal_repair": "Temporal Repair",
        "graph_repair": "Graph Repair",
        "evidence_audit": "Evidence Audit",
        "relationship_validation": "Relationship Validation",
        "population_baseline": "Population Baseline",
        "general_research": "General Research",
    }.get(experiment_type, "Experiment")

    cleaned = item.replace("Perform observation:", "").replace("Run experiment:", "").strip()
    return f"{prefix}: {cleaned[:80]}"


def build_success_criteria(item: str, experiment_type: str) -> list[str]:
    """Build success criteria."""
    if experiment_type == "temporal_repair":
        return [
            "Temporal warning count decreases.",
            "Moon/Nakshatra, birth, dasha, or transit metrics become more complete.",
            "Reasoning confidence improves or limitations become more precise.",
        ]

    if experiment_type == "graph_repair":
        return [
            "Graph metrics become more complete.",
            "CIG/STG node or edge quality improves.",
            "Graph intelligence confidence changes in a measurable way.",
        ]

    if experiment_type == "evidence_audit":
        return [
            "Claim-level evidence becomes clearer.",
            "Unsupported claims are identified or removed.",
            "Evidence confidence becomes easier to justify.",
        ]

    if experiment_type == "relationship_validation":
        return [
            "Shared nodes and shared edges are inspected separately.",
            "Morphology interpretation becomes more precise.",
            "Relationship confidence changes based on evidence.",
        ]

    return [
        "The experiment produces a measurable change in confidence, warnings, or interpretation.",
    ]


def build_failure_criteria(item: str, experiment_type: str) -> list[str]:
    """Build failure criteria."""
    return [
        "No metric changes after the experiment.",
        "Warnings remain unchanged.",
        "The experiment produces no new evidence or disconfirming signal.",
    ]


def build_expected_outputs(item: str, experiment_type: str) -> list[str]:
    """Build expected outputs."""
    return [
        "Updated service metrics.",
        "Before/after confidence comparison.",
        "Updated limitations or falsification status.",
        "Decision on whether to preserve, lower, or raise hypothesis confidence.",
    ]


def build_experiment_phases(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build phased experiment plan."""
    quick = []
    medium = []
    heavy = []

    for experiment in experiments:
        effort = safe_float(experiment.get("estimated_effort", {}).get("score"))

        if effort < 0.45:
            quick.append(experiment)
        elif effort < 0.70:
            medium.append(experiment)
        else:
            heavy.append(experiment)

    phases = []

    if quick:
        phases.append(
            {
                "phase": 1,
                "title": "Quick Wins",
                "description": "Low-effort checks that can quickly clarify the hypothesis.",
                "experiments": quick[:5],
            }
        )

    if medium:
        phases.append(
            {
                "phase": 2,
                "title": "Core Repairs",
                "description": "Medium-effort repairs likely to improve confidence meaningfully.",
                "experiments": medium[:5],
            }
        )

    if heavy:
        phases.append(
            {
                "phase": 3,
                "title": "Deep Repairs",
                "description": "Higher-effort corrections or rebuilds.",
                "experiments": heavy[:5],
            }
        )

    return phases


def rank_experiments(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank experiments by value score."""
    return sorted(
        experiments,
        key=lambda item: safe_float(item.get("value_score", {}).get("score")),
        reverse=True,
    )


def dedupe_experiments(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe experiments by description."""
    seen = set()
    result = []

    for experiment in experiments:
        key = experiment.get("description", "")
        if key not in seen:
            result.append(experiment)
            seen.add(key)

    return result


def build_experiment_id(hypothesis_title: str, index: int) -> str:
    """Build stable experiment id."""
    safe_title = "".join(
        char.lower() if char.isalnum() else "_"
        for char in hypothesis_title
    ).strip("_")

    while "__" in safe_title:
        safe_title = safe_title.replace("__", "_")

    return f"{safe_title}:experiment_{index}"


def build_experiment_metrics(
    model: dict[str, Any],
    falsification_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build experiment planner metrics."""
    experiments = model.get("experiments", [])
    markdown = render_experiment_plan_markdown(model)

    return {
        "experiment_count": len(experiments),
        "phase_count": len(model.get("phases", [])),
        "recommended_next_experiment": model.get(
            "recommended_next_experiment",
            {},
        ).get("title"),
        "highest_value_score": model.get("recommended_next_experiment", {})
        .get("value_score", {}),
        "average_expected_gain": average_score(
            experiments,
            "expected_confidence_gain",
            "score",
        ),
        "average_effort": average_score(
            experiments,
            "estimated_effort",
            "score",
        ),
        "word_count": len(markdown.split()),
        "source_case_count": falsification_payload.get("metrics", {}).get(
            "case_count",
            0,
        ),
        "source_warning_count": len(falsification_payload.get("warnings", [])),
        "source_error_count": len(falsification_payload.get("errors", [])),
    }


def render_experiment_plan_markdown(model: dict[str, Any]) -> str:
    """Render experiment plan Markdown."""
    lines = [
        f"# Atlas Experiment Planner: {model.get('subject', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', EXPERIMENT_PLANNER_VERSION)}",
        f"**Intent:** {model.get('intent', 'unknown')}",
        f"**Scope:** {model.get('scope', 'unknown')}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Recommended Next Experiment",
    ]

    recommended = model.get("recommended_next_experiment", {})
    if recommended:
        value = recommended.get("value_score", {})
        gain = recommended.get("expected_confidence_gain", {})
        effort = recommended.get("estimated_effort", {})

        lines.append(f"**{recommended.get('title', 'Untitled')}**")
        lines.append("")
        lines.append(recommended.get("description", ""))
        lines.append("")
        lines.append(f"Value: {value.get('percent', 0)}% {value.get('label', 'unknown')}")
        lines.append(f"Expected confidence gain: +{gain.get('percent_points', 0)} points")
        lines.append(f"Effort: {effort.get('label', 'unknown')}")

    lines.append("")
    lines.append("## Experiment Phases")

    for phase in model.get("phases", []):
        lines.append(f"### Phase {phase.get('phase')}: {phase.get('title')}")
        lines.append(phase.get("description", ""))

        for experiment in phase.get("experiments", []):
            value = experiment.get("value_score", {})
            gain = experiment.get("expected_confidence_gain", {})
            effort = experiment.get("estimated_effort", {})

            lines.append("")
            lines.append(f"#### {experiment.get('title', 'Untitled')}")
            lines.append(experiment.get("description", ""))
            lines.append(
                f"Value: {value.get('percent', 0)}% {value.get('label', 'unknown')}"
            )
            lines.append(
                f"Expected gain: +{gain.get('percent_points', 0)} points"
            )
            lines.append(f"Effort: {effort.get('label', 'unknown')}")

            criteria = experiment.get("success_criteria", [])
            if criteria:
                lines.append("Success criteria:")
                for item in criteria:
                    lines.append(f"- {item}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def summarize_falsification_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe falsification summary."""
    model = payload.get("data", {}).get("falsification_model", {})

    return {
        "success": payload.get("success"),
        "warnings": payload.get("warnings", []),
        "errors": payload.get("errors", []),
        "metrics": payload.get("metrics", {}),
        "subject": model.get("subject"),
        "case_count": len(model.get("cases", [])),
        "highest_priority_case": model.get("highest_priority_case", {}).get(
            "hypothesis_title"
        ),
    }


def average_score(
    items: list[dict[str, Any]],
    outer_key: str,
    inner_key: str,
) -> float:
    """Average nested score."""
    scores = [
        safe_float(item.get(outer_key, {}).get(inner_key))
        for item in items
    ]

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 4)


def contains_any(text: str, keywords: list[str]) -> bool:
    """Return whether text contains any keyword."""
    return any(keyword.lower() in text for keyword in keywords)


def effort_label(score: float) -> str:
    """Resolve effort label."""
    if score >= 0.70:
        return "high"
    if score >= 0.45:
        return "moderate"
    return "low"


def gain_label(score: float) -> str:
    """Resolve confidence-gain label."""
    if score >= 0.25:
        return "high"
    if score >= 0.15:
        return "moderate"
    if score >= 0.08:
        return "limited"
    return "low"


def value_label(score: float) -> str:
    """Resolve value label."""
    if score >= 0.70:
        return "high"
    if score >= 0.45:
        return "moderate"
    if score >= 0.25:
        return "limited"
    return "low"


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
    return max(0.0, min(1.0, value))


def failure_payload(
    *,
    query: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": EXPERIMENT_PLANNER_VERSION,
        "query": query,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    """Serialize experiment planner JSON."""
    return json.dumps(data, indent=2, sort_keys=True)