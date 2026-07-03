"""Atlas question-answer service.

Turns user questions into readable Atlas answers using the AI runtime.
"""

from __future__ import annotations

from typing import Any

from atlas.ai import run_research_pipeline


ATLAS_QA_SERVICE_VERSION = "3.0"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a user question in clear language using Atlas research AI."""
    clean_question = question.strip()

    if not clean_question:
        return {
            "success": False,
            "version": ATLAS_QA_SERVICE_VERSION,
            "question": question,
            "answer": "Ask Atlas a question first.",
            "key_points": [],
            "confidence": "none",
            "evidence": [],
            "limitations": ["No question was provided."],
            "suggested_next_questions": [],
            "errors": ["Question is required."],
            "warnings": [],
            "raw_runtime": None,
        }

    runtime = run_research_pipeline(clean_question)

    integrated = runtime.integrated
    stages = runtime.stages

    hypothesis_model = get_nested(
        stages,
        "hypothesis",
        "payload",
        "data",
        "hypothesis_model",
    ) or {}

    falsification_model = get_nested(
        stages,
        "falsification",
        "payload",
        "data",
        "falsification_model",
    ) or {}

    experiment_model = get_nested(
        stages,
        "experiment_planner",
        "payload",
        "data",
        "experiment_model",
    ) or {}

    discovery_model = get_nested(
        stages,
        "discovery",
        "payload",
        "data",
        "discovery_model",
    ) or {}

    hypotheses = hypothesis_model.get("hypotheses", [])
    best_hypothesis = hypothesis_model.get("best_supported_hypothesis") or first(hypotheses)

    cases = falsification_model.get("cases", [])
    experiments = experiment_model.get("experiments", [])
    discoveries = discovery_model.get("discoveries", [])

    answer = build_plain_answer(
        question=clean_question,
        best_hypothesis=best_hypothesis,
        hypotheses=hypotheses,
        cases=cases,
        experiments=experiments,
        discoveries=discoveries,
        runtime=runtime,
    )

    return {
        "success": runtime.success,
        "version": ATLAS_QA_SERVICE_VERSION,
        "question": clean_question,
        "answer": answer,
        "key_points": build_key_points(
            best_hypothesis=best_hypothesis,
            hypotheses=hypotheses,
            cases=cases,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "confidence": resolve_confidence(best_hypothesis),
        "evidence": collect_evidence(best_hypothesis, discoveries),
        "limitations": collect_limitations(cases, runtime),
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "errors": runtime.errors,
        "warnings": runtime.warnings,
        "raw_runtime": runtime.to_dict(),
        "metrics": {
            "completed_stages": len(integrated.get("completed_stages", [])),
            "hypotheses": integrated.get("hypothesis_count", 0),
            "falsification_cases": integrated.get("falsification_count", 0),
            "experiments": integrated.get("experiment_count", 0),
            "discoveries": integrated.get("discovery_count", 0),
        },
    }


def build_plain_answer(
    *,
    question: str,
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
    runtime: Any,
) -> str:
    """Build a concise plain-English answer."""
    if not runtime.success:
        return (
            "Atlas could not fully answer that question yet. "
            "The research runtime started, but one or more stages failed."
        )

    if best_hypothesis:
        claim = (
            best_hypothesis.get("claim")
            or best_hypothesis.get("summary")
            or best_hypothesis.get("title")
            or "Atlas found a plausible interpretation."
        )

        return (
            f"Atlas' best current answer is: {claim} "
            f"This is based on {len(hypotheses)} generated hypotheses, "
            f"{len(cases)} falsification checks, "
            f"{len(experiments)} possible experiments, and "
            f"{len(discoveries)} discovery signals."
        )

    return (
        "Atlas processed the question successfully, but it did not find a strong "
        "specific hypothesis yet. Try asking with a clearer subject, profile name, "
        "relationship, pattern, or comparison target."
    )


def build_key_points(
    *,
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Build simple bullet points."""
    points: list[str] = []

    if best_hypothesis:
        title = best_hypothesis.get("title") or "Best hypothesis"
        points.append(f"Best hypothesis: {title}")

    points.append(f"Atlas generated {len(hypotheses)} hypotheses.")
    points.append(f"Atlas checked {len(cases)} ways the answer could be wrong.")
    points.append(f"Atlas suggested {len(experiments)} possible next experiments.")

    if discoveries:
        points.append(f"Atlas found {len(discoveries)} broader discovery signals.")

    return points


def resolve_confidence(best_hypothesis: dict[str, Any] | None) -> str:
    """Return a readable confidence label."""
    if not best_hypothesis:
        return "low"

    confidence = best_hypothesis.get("confidence")

    if isinstance(confidence, dict):
        return str(confidence.get("label") or confidence.get("score") or "unknown")

    if confidence:
        return str(confidence)

    return "unknown"


def collect_evidence(
    best_hypothesis: dict[str, Any] | None,
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Collect evidence snippets."""
    evidence: list[str] = []

    if best_hypothesis:
        for key in ("supporting_evidence", "evidence", "support"):
            value = best_hypothesis.get(key)
            if isinstance(value, list):
                evidence.extend(str(item) for item in value)
            elif value:
                evidence.append(str(value))

    for discovery in discoveries[:3]:
        summary = discovery.get("summary") or discovery.get("title")
        if summary:
            evidence.append(str(summary))

    return dedupe(evidence)[:8]


def collect_limitations(cases: list[dict[str, Any]], runtime: Any) -> list[str]:
    """Collect caveats and limitations."""
    limitations: list[str] = []

    for case in cases[:3]:
        title = case.get("title") or case.get("claim")
        pressure = case.get("pressure") or case.get("falsification_pressure")

        if title:
            limitations.append(f"Needs falsification check: {title}")

        if isinstance(pressure, dict) and pressure.get("label"):
            limitations.append(f"Falsification pressure: {pressure['label']}")

    limitations.extend(str(warning) for warning in runtime.warnings[:5])

    return dedupe(limitations)[:8]


def build_suggested_questions(
    *,
    question: str,
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Suggest next questions."""
    suggestions: list[str] = []

    for experiment in experiments[:3]:
        title = experiment.get("title")
        if title:
            suggestions.append(f"What would confirm or disprove: {title}?")

    for discovery in discoveries[:2]:
        title = discovery.get("title")
        if title:
            suggestions.append(f"What does this discovery imply: {title}?")

    if not suggestions:
        suggestions.extend(
            [
                f"What evidence supports this answer to: {question}?",
                f"What would falsify this answer to: {question}?",
                f"What should Atlas test next about: {question}?",
            ]
        )

    return dedupe(suggestions)[:5]


def get_nested(value: Any, *keys: str) -> Any:
    """Safely traverse nested objects and dictionaries."""
    current = value

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            continue

        current = getattr(current, key, None)

    return current


def first(values: list[Any]) -> Any:
    """Return first list item or None."""
    return values[0] if values else None


def dedupe(values: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result