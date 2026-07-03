"""Atlas question-answer service."""

from __future__ import annotations

from typing import Any

from atlas.ai import run_research_pipeline
from atlas.interpretation import synthesize_relationship_interpretation
from atlas.services.temporal_graph_synthesis_service import (
    build_temporal_graph_synthesis,
)


ATLAS_QA_SERVICE_VERSION = "3.0"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a user question with Atlas interpretation."""
    clean_question = question.strip()

    if not clean_question:
        return failure_payload(
            question=question,
            error="Question is required.",
            answer="Ask Atlas a question first.",
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
    evidence = collect_evidence(best_hypothesis, discoveries)

    temporal_graph = build_temporal_graph_synthesis(
        query_plan=query_plan,
        hypothesis_model=hypothesis_model,
        falsification_model=falsification_model,
        discovery_model=discovery_model,
    )

    relationship_synthesis: dict[str, Any] = {}
    profiles = query_plan.get("profiles", [])

    if query_plan.get("scope") == "relationship" and len(profiles) >= 2:
        relationship_synthesis = synthesize_relationship_interpretation(
            profile_a=profiles[0],
            profile_b=profiles[1],
            graph_pattern=temporal_graph.get("structural_pattern", ""),
            temporal_overlay=temporal_graph.get("temporal_overlay", ""),
            claim=extract_claim(best_hypothesis),
            evidence=evidence,
        )

    answer = build_answer(
        question=clean_question,
        query_plan=query_plan,
        best_hypothesis=best_hypothesis,
        hypotheses=hypotheses,
        falsification_cases=falsification_cases,
        experiments=experiments,
        discoveries=discoveries,
        runtime=runtime,
        temporal_graph=temporal_graph,
        relationship_synthesis=relationship_synthesis,
    )

    return {
        "success": runtime.success,
        "version": ATLAS_QA_SERVICE_VERSION,
        "question": clean_question,
        "answer": answer,
        "key_points": build_key_points(
            best_hypothesis=best_hypothesis,
            hypotheses=hypotheses,
            falsification_cases=falsification_cases,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "confidence": resolve_confidence(best_hypothesis),
        "evidence": evidence,
        "limitations": collect_limitations(falsification_cases, runtime),
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "temporal_graph": temporal_graph,
        "relationship_synthesis": relationship_synthesis,
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


def build_answer(
    *,
    question: str,
    query_plan: dict[str, Any],
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
    runtime: Any,
    temporal_graph: dict[str, Any],
    relationship_synthesis: dict[str, Any],
) -> str:
    """Build human-facing Atlas answer."""
    if not runtime.success:
        return (
            "Atlas could not complete the full research pipeline for this question. "
            "The result should be treated as incomplete until the failed stages are resolved."
        )

    intent = query_plan.get("intent", "interpretation")
    scope = query_plan.get("scope", "general")
    claim = extract_claim(best_hypothesis) or (
        "Atlas processed the question successfully, but did not identify one dominant "
        "interpretive claim. Treat this answer as provisional."
    )

    pressure_case = first(falsification_cases) or {}
    pressure_title = (
        pressure_case.get("hypothesis_title")
        or pressure_case.get("title")
        or "the strongest uncertainty"
    )

    comparison = is_relationship_scope(scope, query_plan)

    if comparison:
        middle = relationship_interpretation()
    else:
        middle = profile_or_general_interpretation()

    return f"""### Direct Answer

Atlas reads this as: **{claim}**

### Plain-English Meaning

{plain_meaning_for_claim(claim, comparison=comparison)}

### Comparative Atlas Profile

{format_relationship_synthesis(relationship_synthesis)}

### Temporal-Graph Overlay

{temporal_graph.get("human_interpretation", "")}

**Structural pattern:** {temporal_graph.get("structural_pattern", "")}

**Temporal overlay:** {temporal_graph.get("temporal_overlay", "")}

**Activation pressure:** {temporal_graph.get("activation_pressure", "")}

{middle}

### Natal / Temperamental Influence

Natal influence explains the *style* of expression.

- Mercury: cognition, language, invention, translation, and pattern recognition.
- Venus: values, aesthetic refinement, harmony, attraction, and relational tone.
- Mars: action, conflict style, pressure, rupture, and execution.
- Jupiter: growth, belief, scale, teaching, and long-range vision.
- Saturn: discipline, limits, responsibility, structure, and mastery.
- Uranus: originality, disruption, independence, rebellion, and innovation.
- Neptune: imagination, symbolism, ambiguity, dream, and idealization.
- Pluto: transformation, power, obsession, depth pressure, and irreversible change.

When exact natal placements are available, Atlas should become more specific. When they are incomplete, it should speak in probabilities.

### Probable Outcomes

- **High alignment:** the pattern becomes productive. Each side strengthens what the other lacks.
- **Moderate stress:** differences in pace, communication, emotional need, control strategy, or recognition become visible.
- **Low alignment:** the same differences become conflict, competition, distance, or misunderstanding.
- **Growth path:** the best outcome comes when each role is named clearly and used intentionally.

### Evidence Atlas Used

{format_short_list(collect_evidence(best_hypothesis, discoveries)[:5])}

### Main Caution

The strongest uncertainty is: **{pressure_title}**.

Atlas should not overstate final judgment until graph overlap, temporal assumptions, natal data, and evidence strength are checked more deeply.

### Bottom Line

{bottom_line_for_claim(claim, comparison=comparison)}

### Runtime Summary

Atlas used {len(hypotheses)} hypotheses, {len(falsification_cases)} falsification checks, {len(experiments)} proposed experiments, and {len(discoveries)} discovery signals for this answer.

Detected intent: **{intent}**  
Detected scope: **{scope}**"""


def format_relationship_synthesis(payload: dict[str, Any]) -> str:
    """Format relationship synthesis."""
    if not payload:
        return "No relationship synthesis was generated for this question."

    a = payload.get("profile_a", {})
    b = payload.get("profile_b", {})

    outcomes = payload.get("probable_outcomes", [])
    outcome_text = "\n".join(f"- {item}" for item in outcomes) if outcomes else "- No outcomes generated."

    return f"""**{a.get("name", "Profile A")}**

Working classification: **{a.get("working_classification", "unknown")}**

{a.get("structural_description", "")}

{a.get("likely_expression", "")}

Civilization role: **{a.get("civilization_role", "unknown")}**

**{b.get("name", "Profile B")}**

Working classification: **{b.get("working_classification", "unknown")}**

{b.get("structural_description", "")}

{b.get("likely_expression", "")}

Civilization role: **{b.get("civilization_role", "unknown")}**

**Structural Relationship**

{payload.get("structural_relationship", "")}

**Civilization Function**

{payload.get("civilization_function", "")}

**Probable Relationship Outcomes**

{outcome_text}
"""


def plain_meaning_for_claim(claim: str, *, comparison: bool) -> str:
    """Translate claim into simple language."""
    lower = claim.lower()

    if comparison and ("limited" in lower or "low" in lower):
        return (
            "This does not mean the subjects are irrelevant to each other. It means their "
            "relationship is probably not smooth similarity. Atlas is seeing contrast, "
            "friction, and transformation more than easy resonance."
        )

    if comparison and "transformation" in lower:
        return (
            "This comparison is best read as a change-producing relationship. The value is "
            "not simple compatibility; it is what each side forces the other to reveal, refine, "
            "resist, or become."
        )

    return (
        "Atlas found a meaningful interpretive pattern, but the result should be read as a "
        "probable synthesis rather than an absolute verdict."
    )


def relationship_interpretation() -> str:
    """Relationship-specific interpretation."""
    return """### Interaction Dynamic

Atlas is comparing how two structures react against each other.

A strong relationship reading should describe the feedback loop:

- One side may initiate movement while the other stabilizes it.
- One may amplify meaning while the other imposes structure.
- One may generate vision while the other demands proof, form, or control.
- One may expose unresolved pressure in the other.

When the relationship is healthy, contrast becomes productive. When strained, the same contrast becomes competition, misunderstanding, or resistance."""


def profile_or_general_interpretation() -> str:
    """General interpretation."""
    return """### Structural Dynamic

Atlas is identifying how the subject organizes reality.

The core question is not simply “what traits exist?” but:

- What initiates movement?
- What amplifies signal?
- What stabilizes the system?
- What creates stress or distortion?
- What pattern is likely to repeat?"""


def bottom_line_for_claim(claim: str, *, comparison: bool) -> str:
    """Build bottom line."""
    lower = claim.lower()

    if comparison and ("limited" in lower or "alignment" in lower):
        return (
            "This is not best understood as simple compatibility. It is better understood "
            "as two different kinds of power meeting in the same field. The probable outcome "
            "is creative friction, transformation, and contested influence rather than easy harmony."
        )

    if comparison and "transformation" in lower:
        return (
            "The relationship is valuable because it changes the field. The key question is "
            "not whether the two are alike, but what each forces into motion in the other."
        )

    return (
        "Atlas sees a meaningful pattern, but the interpretation should stay tied to available "
        "evidence and become more specific as deterministic outputs become more complete."
    )


def build_key_points(
    *,
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Build key points."""
    points: list[str] = []

    if best_hypothesis:
        title = best_hypothesis.get("title") or "Best supported hypothesis"
        points.append(f"Best hypothesis: {title}")

    claim = extract_claim(best_hypothesis)
    if claim:
        points.append(claim)

    points.append(f"Atlas generated {len(hypotheses)} hypotheses.")
    points.append(f"Atlas checked {len(falsification_cases)} ways the interpretation could be wrong.")
    points.append(f"Atlas proposed {len(experiments)} next research actions.")

    if discoveries:
        points.append(f"Atlas found {len(discoveries)} broader discovery signals.")

    return dedupe(points)


def collect_evidence(
    best_hypothesis: dict[str, Any] | None,
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Collect evidence."""
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
    """Suggest follow-up questions."""
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
            "What natal factors would refine this answer?",
            "What Kamea outputs would increase confidence?",
        ]

    return dedupe(suggestions)[:6]


def resolve_confidence(best_hypothesis: dict[str, Any] | None) -> str:
    """Resolve confidence."""
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


def extract_claim(best_hypothesis: dict[str, Any] | None) -> str:
    """Extract claim."""
    if not best_hypothesis:
        return ""

    for key in ("claim", "summary", "title"):
        value = best_hypothesis.get(key)
        if value:
            return str(value)

    return ""


def get_stage_model(
    stages: dict[str, Any],
    stage_name: str,
    model_key: str,
) -> dict[str, Any]:
    """Read stage model."""
    stage = stages.get(stage_name)
    if not stage:
        return {}

    payload = getattr(stage, "payload", {}) or {}
    data = payload.get("data", {})

    model = data.get(model_key)
    return model if isinstance(model, dict) else {}


def is_relationship_scope(scope: str, query_plan: dict[str, Any]) -> bool:
    """Check relationship scope."""
    if scope == "relationship":
        return True

    intent = str(query_plan.get("intent", ""))
    return "relationship" in intent or "compare" in intent or "comparison" in intent


def ensure_dict_list(value: Any) -> list[dict[str, Any]]:
    """Normalize to list of dicts."""
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        return [value]

    return []


def first(values: list[Any]) -> Any:
    """Return first item."""
    return values[0] if values else None


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


def failure_payload(*, question: str, error: str, answer: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": ATLAS_QA_SERVICE_VERSION,
        "question": question,
        "answer": answer,
        "key_points": [],
        "confidence": "none",
        "evidence": [],
        "limitations": [error],
        "suggested_next_questions": [],
        "temporal_graph": {},
        "relationship_synthesis": {},
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