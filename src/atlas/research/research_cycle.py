"""Atlas Research Cycle engine.

Runs a complete Atlas scientific research cycle from query to next questions.

The Research Cycle Engine orchestrates existing systems. It does not replace them.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.services.experiment_planner_service import build_experiment_plan_payload
from atlas.services.falsification_engine_service import build_falsification_payload
from atlas.services.hypothesis_engine_service import build_hypothesis_payload
from atlas.services.query_planner_service import build_query_plan_payload
from atlas.services.reasoning_service import build_reasoning_payload
from atlas.services.research_memory_service import build_research_memory_payload
from atlas.services.validation_domain_service import build_validation_domain_payload


RESEARCH_CYCLE_VERSION = "1.0"


def build_research_cycle_payload(
    query: str,
    *,
    include_memory: bool = True,
    include_validation: bool = True,
    validation_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Run complete Atlas research cycle."""
    planner_payload = safe_call("query_planner", lambda: build_query_plan_payload(query))
    reasoning_payload = safe_call("reasoning", lambda: build_reasoning_payload(query))
    hypothesis_payload = safe_call("hypothesis", lambda: build_hypothesis_payload(query))
    falsification_payload = safe_call(
        "falsification",
        lambda: build_falsification_payload(query),
    )
    experiment_payload = safe_call(
        "experiment_planner",
        lambda: build_experiment_plan_payload(query),
    )

    validation_payloads = build_validation_payloads(
        planner_payload=planner_payload,
        include_validation=include_validation,
        validation_domains=validation_domains,
    )

    memory_payload = {}
    if include_memory:
        memory_payload = safe_call(
            "research_memory",
            lambda: build_research_memory_payload(query),
        )

    cycle_model = build_research_cycle_model(
        query=query,
        planner_payload=planner_payload,
        reasoning_payload=reasoning_payload,
        hypothesis_payload=hypothesis_payload,
        falsification_payload=falsification_payload,
        experiment_payload=experiment_payload,
        validation_payloads=validation_payloads,
        memory_payload=memory_payload,
    )

    return {
        "success": cycle_model.get("success", False),
        "version": RESEARCH_CYCLE_VERSION,
        "query": query,
        "errors": collect_cycle_errors(cycle_model),
        "warnings": collect_cycle_warnings(cycle_model),
        "data": {
            "research_cycle": cycle_model,
        },
        "exports": {
            "research_cycle_json": cycle_model,
            "markdown": render_research_cycle_markdown(cycle_model),
        },
        "metrics": build_research_cycle_metrics(cycle_model),
    }


def build_validation_payloads(
    *,
    planner_payload: dict[str, Any],
    include_validation: bool,
    validation_domains: list[str] | None,
) -> dict[str, dict[str, Any]]:
    """Build validation payloads for planned profile targets."""
    if not include_validation:
        return {}

    plan = planner_payload.get("data", {}).get("plan", {})
    profiles = plan.get("profiles", [])
    scope = plan.get("scope")

    if scope != "profile":
        return {}

    validation_payloads = {}

    for profile_key in profiles:
        validation_payloads[profile_key] = safe_call(
            "validation_domain",
            lambda key=profile_key: build_validation_domain_payload(
                key,
                domains=validation_domains,
            ),
        )

    return validation_payloads


def build_research_cycle_model(
    *,
    query: str,
    planner_payload: dict[str, Any],
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
    validation_payloads: dict[str, dict[str, Any]],
    memory_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build unified research cycle model."""
    stages = {
        "planner": compact_payload(planner_payload),
        "reasoning": compact_payload(reasoning_payload),
        "hypothesis": compact_payload(hypothesis_payload),
        "falsification": compact_payload(falsification_payload),
        "experiment": compact_payload(experiment_payload),
        "validation": {
            key: compact_payload(payload)
            for key, payload in validation_payloads.items()
        },
        "memory": compact_payload(memory_payload) if memory_payload else {},
    }

    next_questions = build_next_research_questions(
        reasoning_payload=reasoning_payload,
        hypothesis_payload=hypothesis_payload,
        falsification_payload=falsification_payload,
        experiment_payload=experiment_payload,
        validation_payloads=validation_payloads,
    )

    confidence = build_cycle_confidence(
        reasoning_payload=reasoning_payload,
        hypothesis_payload=hypothesis_payload,
        falsification_payload=falsification_payload,
        experiment_payload=experiment_payload,
        validation_payloads=validation_payloads,
    )

    return {
        "success": all_required_stages_successful(
            planner_payload=planner_payload,
            reasoning_payload=reasoning_payload,
            hypothesis_payload=hypothesis_payload,
            falsification_payload=falsification_payload,
            experiment_payload=experiment_payload,
        ),
        "version": RESEARCH_CYCLE_VERSION,
        "query": query,
        "state": "memorized" if memory_payload else "research_cycle_complete",
        "definition": (
            "A research cycle runs Atlas scientific cognition from query planning "
            "through reasoning, hypothesis generation, falsification, experiment "
            "planning, validation, and optional research memory."
        ),
        "stages": stages,
        "confidence": confidence,
        "next_research_questions": next_questions,
        "cycle_summary": build_cycle_summary(
            planner_payload=planner_payload,
            reasoning_payload=reasoning_payload,
            hypothesis_payload=hypothesis_payload,
            falsification_payload=falsification_payload,
            experiment_payload=experiment_payload,
            validation_payloads=validation_payloads,
            memory_payload=memory_payload,
            next_questions=next_questions,
        ),
    }


def all_required_stages_successful(
    *,
    planner_payload: dict[str, Any],
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
) -> bool:
    """Return whether required cycle stages succeeded."""
    return all(
        payload.get("success", False)
        for payload in [
            planner_payload,
            reasoning_payload,
            hypothesis_payload,
            falsification_payload,
            experiment_payload,
        ]
    )


def build_cycle_summary(
    *,
    planner_payload: dict[str, Any],
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
    validation_payloads: dict[str, dict[str, Any]],
    memory_payload: dict[str, Any],
    next_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build compact cycle summary."""
    plan = planner_payload.get("data", {}).get("plan", {})
    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})
    hypothesis = hypothesis_payload.get("data", {}).get("hypothesis_model", {})
    falsification = falsification_payload.get("data", {}).get("falsification_model", {})
    experiment = experiment_payload.get("data", {}).get("experiment_model", {})

    return {
        "intent": plan.get("intent"),
        "scope": plan.get("scope"),
        "profiles": plan.get("profiles", []),
        "final_answer_present": bool(reasoning.get("final_answer")),
        "best_hypothesis": hypothesis.get("best_supported_hypothesis", {}).get("title"),
        "highest_falsification_case": falsification.get("highest_priority_case", {}).get(
            "hypothesis_title"
        ),
        "recommended_experiment": experiment.get(
            "recommended_next_experiment",
            {},
        ).get("title"),
        "validation_profile_count": len(validation_payloads),
        "memory_recorded": bool(memory_payload),
        "next_question_count": len(next_questions),
    }


def build_cycle_confidence(
    *,
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
    validation_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build aggregate research-cycle confidence."""
    scores = []

    reasoning_confidence = reasoning_payload.get("metrics", {}).get("overall_confidence", {})
    if "score" in reasoning_confidence:
        scores.append(safe_float(reasoning_confidence.get("score")))

    hypothesis_confidence = hypothesis_payload.get("metrics", {}).get("best_confidence", {})
    if "score" in hypothesis_confidence:
        scores.append(safe_float(hypothesis_confidence.get("score")))

    falsification_pressure = falsification_payload.get("metrics", {}).get(
        "highest_pressure",
        {},
    )
    if "score" in falsification_pressure:
        # Falsification pressure is inverted because high pressure reduces certainty.
        scores.append(1.0 - safe_float(falsification_pressure.get("score")))

    experiment_value = experiment_payload.get("metrics", {}).get("highest_value_score", {})
    if "score" in experiment_value:
        scores.append(safe_float(experiment_value.get("score")))

    for validation_payload in validation_payloads.values():
        validation_confidence = validation_payload.get("metrics", {}).get(
            "scientific_confidence",
            {},
        )
        if "score" in validation_confidence:
            scores.append(safe_float(validation_confidence.get("score")))

    score = sum(scores) / len(scores) if scores else 0.0

    return {
        "overall": confidence_record(score),
        "component_scores": [round(item, 4) for item in scores],
        "component_count": len(scores),
    }


def build_next_research_questions(
    *,
    reasoning_payload: dict[str, Any],
    hypothesis_payload: dict[str, Any],
    falsification_payload: dict[str, Any],
    experiment_payload: dict[str, Any],
    validation_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build next research questions from cycle outputs."""
    questions = []

    questions.extend(questions_from_reasoning(reasoning_payload))
    questions.extend(questions_from_hypothesis(hypothesis_payload))
    questions.extend(questions_from_falsification(falsification_payload))
    questions.extend(questions_from_experiment(experiment_payload))
    questions.extend(questions_from_validation(validation_payloads))

    return dedupe_questions(questions)[:20]


def questions_from_reasoning(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Build questions from reasoning recommendations."""
    reasoning = payload.get("data", {}).get("reasoning", {})
    recommendations = reasoning.get("recommendations", [])

    return [
        {
            "question": f"What changes if Atlas follows this recommendation: {item}",
            "source": "reasoning",
            "priority": "moderate",
        }
        for item in recommendations[:5]
    ]


def questions_from_hypothesis(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Build questions from hypotheses."""
    model = payload.get("data", {}).get("hypothesis_model", {})
    hypotheses = model.get("hypotheses", [])

    return [
        {
            "question": f"What evidence would strengthen or weaken: {item.get('title', 'untitled hypothesis')}?",
            "source": "hypothesis",
            "priority": "moderate",
        }
        for item in hypotheses[:5]
    ]


def questions_from_falsification(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Build questions from falsification cases."""
    model = payload.get("data", {}).get("falsification_model", {})
    cases = model.get("cases", [])

    return [
        {
            "question": f"What repair would reduce falsification pressure on: {item.get('hypothesis_title', 'untitled case')}?",
            "source": "falsification",
            "priority": "high",
        }
        for item in cases[:5]
    ]


def questions_from_experiment(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Build questions from experiment plans."""
    model = payload.get("data", {}).get("experiment_model", {})
    experiments = model.get("experiments", [])

    return [
        {
            "question": f"What happens after executing experiment: {item.get('title', 'untitled experiment')}?",
            "source": "experiment",
            "priority": "high",
        }
        for item in experiments[:5]
    ]


def questions_from_validation(
    validation_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build questions from validation-domain outputs."""
    questions = []

    for profile_key, payload in validation_payloads.items():
        metrics = payload.get("metrics", {})
        confidence = metrics.get("scientific_confidence", {})
        tension = metrics.get("tension_label")

        if tension in {"moderate", "high"}:
            questions.append(
                {
                    "question": (
                        f"Which validation signals explain cross-domain tension for "
                        f"{profile_key}?"
                    ),
                    "source": "validation",
                    "priority": "high",
                }
            )

        if confidence.get("label") in {"limited", "low"}:
            questions.append(
                {
                    "question": (
                        f"What missing validation evidence would improve scientific "
                        f"confidence for {profile_key}?"
                    ),
                    "source": "validation",
                    "priority": "moderate",
                }
            )

    return questions


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build compact payload summary."""
    return {
        "success": payload.get("success", False),
        "version": payload.get("version"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
    }


def build_research_cycle_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build research cycle metrics."""
    markdown = render_research_cycle_markdown(model)
    summary = model.get("cycle_summary", {})

    return {
        "state": model.get("state"),
        "intent": summary.get("intent"),
        "scope": summary.get("scope"),
        "profile_count": len(summary.get("profiles", [])),
        "validation_profile_count": summary.get("validation_profile_count", 0),
        "memory_recorded": summary.get("memory_recorded", False),
        "next_question_count": summary.get("next_question_count", 0),
        "overall_confidence": model.get("confidence", {}).get("overall", {}),
        "word_count": len(markdown.split()),
    }


def render_research_cycle_markdown(model: dict[str, Any]) -> str:
    """Render research cycle as Markdown."""
    confidence = model.get("confidence", {}).get("overall", {})
    summary = model.get("cycle_summary", {})

    lines = [
        "# Atlas Research Cycle",
        "",
        f"**Version:** {model.get('version', RESEARCH_CYCLE_VERSION)}",
        f"**State:** {model.get('state', 'unknown')}",
        f"**Query:** {model.get('query', '')}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Summary",
        f"- Intent: {summary.get('intent')}",
        f"- Scope: {summary.get('scope')}",
        f"- Profiles: {summary.get('profiles', [])}",
        f"- Best hypothesis: {summary.get('best_hypothesis')}",
        f"- Highest falsification case: {summary.get('highest_falsification_case')}",
        f"- Recommended experiment: {summary.get('recommended_experiment')}",
        f"- Validation profiles: {summary.get('validation_profile_count')}",
        f"- Memory recorded: {summary.get('memory_recorded')}",
        "",
        "## Confidence",
        f"- Overall: {confidence.get('percent', 0)}% {confidence.get('label', 'unknown')}",
        "",
        "## Next Research Questions",
    ]

    for question in model.get("next_research_questions", []):
        lines.append(
            f"- [{question.get('priority', 'unknown')}] "
            f"{question.get('question', '')}"
        )

    return "\n".join(lines).strip() + "\n"


def collect_cycle_errors(model: dict[str, Any]) -> list[Any]:
    """Collect errors from cycle stages."""
    errors = []

    for name, payload in model.get("stages", {}).items():
        if isinstance(payload, dict) and "errors" in payload:
            for error in payload.get("errors", []):
                errors.append({"stage": name, "error": error})

    return errors


def collect_cycle_warnings(model: dict[str, Any]) -> list[str]:
    """Collect warnings from cycle stages."""
    warnings = []

    for name, payload in model.get("stages", {}).items():
        if isinstance(payload, dict) and "warnings" in payload:
            for warning in payload.get("warnings", []):
                text = f"{name}: {warning}"
                if text not in warnings:
                    warnings.append(text)

    return warnings


def safe_call(name: str, fn) -> dict[str, Any]:
    """Safely call a service."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": RESEARCH_CYCLE_VERSION,
            "errors": [f"{name} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Resolve confidence label."""
    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "moderate"

    if score >= 0.40:
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


def dedupe_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe questions while preserving order."""
    seen = set()
    result = []

    for item in questions:
        question = item.get("question", "")
        if question not in seen:
            result.append(item)
            seen.add(question)

    return result


def json_export(data: Any) -> str:
    """Serialize research cycle JSON."""
    return json.dumps(data, indent=2, sort_keys=True)