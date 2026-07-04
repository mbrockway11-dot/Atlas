"""Atlas Reasoning Kernel.

Central orchestration layer for user questions.

The kernel coordinates:
- AI research runtime
- deterministic payload extraction
- semantic interpretation
- narrative composition
- final user-facing answer

It should become the single question-answer brain behind Atlas AI.
"""

from __future__ import annotations

from typing import Any

from atlas.ai import run_research_pipeline
from atlas.interpretation import (
    compose_interpretive_answer,
    compose_profile,
    compose_relationship,
    synthesize_profile,
    synthesize_relationship,
)


REASONING_KERNEL_VERSION = "1.0"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a user question through the Atlas reasoning kernel."""
    clean_question = question.strip()

    if not clean_question:
        return failure_payload(
            question=question,
            error="Question is required.",
        )

    runtime = run_research_pipeline(clean_question)

    query_plan = get_stage_model(runtime.stages, "query_planner", "plan")
    hypothesis_model = get_stage_model(runtime.stages, "hypothesis", "hypothesis_model")
    falsification_model = get_stage_model(runtime.stages, "falsification", "falsification_model")
    experiment_model = get_stage_model(runtime.stages, "experiment_planner", "experiment_model")
    discovery_model = get_stage_model(runtime.stages, "discovery", "discovery_model")
    memory_record = get_stage_model(runtime.stages, "research_memory", "memory_record")

    hypotheses = ensure_dict_list(hypothesis_model.get("hypotheses"))
    falsification_cases = ensure_dict_list(falsification_model.get("cases"))
    experiments = ensure_dict_list(experiment_model.get("experiments"))
    discoveries = ensure_dict_list(discovery_model.get("discoveries"))

    best_hypothesis = hypothesis_model.get("best_supported_hypothesis") or first(hypotheses)

    intent = query_plan.get("intent", "interpretation")
    scope = query_plan.get("scope", "general")
    profiles = ensure_string_list(query_plan.get("profiles"))

    evidence = collect_evidence(best_hypothesis, discoveries)
    claim = extract_claim(best_hypothesis)

    synthesis = build_synthesis(
        scope=scope,
        profiles=profiles,
        claim=claim,
        evidence=evidence,
    )

    answer = build_narrative_answer(
        question=clean_question,
        scope=scope,
        intent=intent,
        claim=claim,
        synthesis=synthesis,
        runtime=runtime,
        hypotheses=hypotheses,
        falsification_cases=falsification_cases,
        experiments=experiments,
        discoveries=discoveries,
    )

    return {
        "success": runtime.success,
        "version": REASONING_KERNEL_VERSION,
        "question": clean_question,
        "answer": answer,
        "intent": intent,
        "scope": scope,
        "profiles": profiles,
        "claim": claim,
        "confidence": resolve_confidence(best_hypothesis),
        "evidence": evidence,
        "limitations": collect_limitations(falsification_cases, runtime),
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "synthesis": synthesis,
        "metrics": {
            "completed_stages": len(runtime.integrated.get("completed_stages", [])),
            "failed_stages": len(runtime.integrated.get("failed_stages", [])),
            "hypotheses": len(hypotheses),
            "falsification_cases": len(falsification_cases),
            "experiments": len(experiments),
            "discoveries": len(discoveries),
            "has_research_memory": bool(memory_record),
        },
        "warnings": dedupe([str(item) for item in runtime.warnings]),
        "errors": runtime.errors,
        "raw": {
            "runtime": runtime.to_dict(),
            "query_plan": query_plan,
            "hypothesis_model": hypothesis_model,
            "falsification_model": falsification_model,
            "experiment_model": experiment_model,
            "discovery_model": discovery_model,
            "memory_record": memory_record,
        },
    }


def build_synthesis(
    *,
    scope: str,
    profiles: list[str],
    claim: str,
    evidence: list[str],
) -> dict[str, Any]:
    """Build semantic synthesis based on query scope."""
    graph_pattern = claim

    if scope == "relationship" and len(profiles) >= 2:
        return synthesize_relationship(
            profile_a=profiles[0],
            profile_b=profiles[1],
            graph_pattern=graph_pattern,
            temporal_overlay="Temporal activation should be evaluated from available temporal runtime outputs.",
            evidence=evidence,
        )

    if profiles:
        return synthesize_profile(
            profile_key=profiles[0],
            graph_pattern=graph_pattern,
            temporal_overlay="Temporal activation should be evaluated from available temporal runtime outputs.",
            evidence=evidence,
        )

    return {
        "success": True,
        "version": REASONING_KERNEL_VERSION,
        "kind": "general",
        "semantic": {},
        "summary": claim,
    }


def build_narrative_answer(
    *,
    question: str,
    scope: str,
    intent: str,
    claim: str,
    synthesis: dict[str, Any],
    runtime: Any,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> str:
    """Compose final user-facing answer."""
    if not runtime.success:
        return (
            "Atlas could not complete the full reasoning pipeline for this question. "
            "The answer should be treated as incomplete until failed stages are resolved."
        )

    composer_payload = {
        "scope": scope,
        "intent": intent,
        "claim": claim,
        "profiles": synthesis.get("profiles", []),
        "synthesis": synthesis,
        "metrics": {
            "hypotheses": len(hypotheses),
            "falsification_cases": len(falsification_cases),
            "experiments": len(experiments),
            "discoveries": len(discoveries),
        },
    }

    body = compose_interpretive_answer(composer_payload)

    return f"""{body}

### Evidence

{format_short_list(collect_evidence_from_synthesis(synthesis))}

### Runtime Summary

Atlas used {len(hypotheses)} hypotheses, {len(falsification_cases)} falsification checks, {len(experiments)} proposed experiments, and {len(discoveries)} discovery signals.

Detected intent: **{intent}**  
Detected scope: **{scope}**"""


def collect_evidence_from_synthesis(synthesis: dict[str, Any]) -> list[str]:
    """Collect evidence from synthesis payload."""
    evidence: list[str] = []

    for key in ("evidence",):
        value = synthesis.get(key)
        if isinstance(value, list):
            evidence.extend(str(item) for item in value)

    relationship = synthesis.get("relationship", {})
    if isinstance(relationship, dict):
        rel_evidence = relationship.get("evidence", [])
        if isinstance(rel_evidence, list):
            evidence.extend(str(item) for item in rel_evidence)

    semantic = synthesis.get("semantic", {})
    if isinstance(semantic, dict):
        sem_evidence = semantic.get("evidence", [])
        if isinstance(sem_evidence, list):
            evidence.extend(str(item) for item in sem_evidence)

    return dedupe(evidence)[:10]


def get_stage_model(
    stages: dict[str, Any],
    stage_name: str,
    model_key: str,
) -> dict[str, Any]:
    """Read a model from runtime stage payload."""
    stage = stages.get(stage_name)
    if not stage:
        return {}

    payload = getattr(stage, "payload", {}) or {}
    data = payload.get("data", {})
    model = data.get(model_key)

    return model if isinstance(model, dict) else {}


def ensure_dict_list(value: Any) -> list[dict[str, Any]]:
    """Normalize value into list of dicts."""
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        return [value]

    return []


def ensure_string_list(value: Any) -> list[str]:
    """Normalize value into list of strings."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    return [str(value)]


def first(values: list[Any]) -> Any:
    """Return first list item or None."""
    return values[0] if values else None


def extract_claim(best_hypothesis: dict[str, Any] | None) -> str:
    """Extract clearest hypothesis claim."""
    if not best_hypothesis:
        return ""

    for key in ("claim", "summary", "title"):
        value = best_hypothesis.get(key)
        if value:
            return str(value)

    return ""


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

    return dedupe(evidence)[:10]


def collect_limitations(
    falsification_cases: list[dict[str, Any]],
    runtime: Any,
) -> list[str]:
    """Collect limitations."""
    limitations: list[str] = []

    for case in falsification_cases[:4]:
        title = case.get("hypothesis_title") or case.get("title") or case.get("claim")
        if title:
            limitations.append(f"Needs falsification check: {title}")

        pressure = case.get("falsification_pressure") or case.get("pressure")
        if isinstance(pressure, dict) and pressure.get("label"):
            limitations.append(f"Falsification pressure: {pressure['label']}")

    limitations.extend(str(warning) for warning in runtime.warnings[:5])

    if not limitations:
        limitations.append(
            "Confidence depends on complete profile, natal, graph, temporal, and Kamea data."
        )

    return dedupe(limitations)[:10]


def build_suggested_questions(
    *,
    question: str,
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Build follow-up questions."""
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
        suggestions = [
            f"What evidence supports this answer to: {question}?",
            f"What would falsify this answer to: {question}?",
            "What temporal factors would refine this answer?",
            "What graph outputs would increase confidence?",
        ]

    return dedupe(suggestions)[:6]


def resolve_confidence(best_hypothesis: dict[str, Any] | None) -> str:
    """Resolve readable confidence."""
    if not best_hypothesis:
        return "provisional"

    confidence = best_hypothesis.get("confidence")

    if isinstance(confidence, dict):
        percent = confidence.get("percent")
        label = confidence.get("label", "unknown")
        if percent is not None:
            return f"{percent}% {label}"
        return str(label)

    if confidence:
        return str(confidence)

    return "unknown"


def format_short_list(items: list[str]) -> str:
    """Format markdown list."""
    if not items:
        return "- No direct evidence surfaced."

    return "\n".join(f"- {item}" for item in items)


def dedupe(values: list[str]) -> list[str]:
    """Deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def failure_payload(*, question: str, error: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": REASONING_KERNEL_VERSION,
        "question": question,
        "answer": "Ask Atlas a question first.",
        "intent": "none",
        "scope": "none",
        "profiles": [],
        "claim": "",
        "confidence": "none",
        "evidence": [],
        "limitations": [error],
        "suggested_next_questions": [],
        "synthesis": {},
        "metrics": {
            "completed_stages": 0,
            "failed_stages": 0,
            "hypotheses": 0,
            "falsification_cases": 0,
            "experiments": 0,
            "discoveries": 0,
            "has_research_memory": False,
        },
        "warnings": [],
        "errors": [error],
        "raw": {},
    }