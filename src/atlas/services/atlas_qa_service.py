"""Atlas question-answer service.

Turns normal user questions into concise, descriptive Atlas interpretations.

Design goal:
- Answer the question first.
- Then explain structure, natal/temperamental influence, interaction dynamics,
  probable outcomes, evidence, and uncertainty.
- Do not bury the user in framework boilerplate.
"""

from __future__ import annotations

from typing import Any

from atlas.ai import run_research_pipeline
from atlas.services.temporal_graph_synthesis_service import build_temporal_graph_synthesis


ATLAS_QA_SERVICE_VERSION = "3.0"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a user question with a clear Atlas interpretation."""
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
    falsification_model = get_stage_model(
        runtime.stages,
        "falsification",
        "falsification_model",
    )
    experiment_model = get_stage_model(
        runtime.stages,
        "experiment_planner",
        "experiment_model",
    )
    discovery_model = get_stage_model(runtime.stages, "discovery", "discovery_model")
    memory_record = get_stage_model(runtime.stages, "research_memory", "memory_record")

    hypotheses = ensure_dict_list(hypothesis_model.get("hypotheses"))
    falsification_cases = ensure_dict_list(falsification_model.get("cases"))
    experiments = ensure_dict_list(experiment_model.get("experiments"))
    discoveries = ensure_dict_list(discovery_model.get("discoveries"))

    temporal_graph = build_temporal_graph_synthesis(
        query_plan=query_plan,
        hypothesis_model=hypothesis_model,
        falsification_model=falsification_model,
        discovery_model=discovery_model,
    )

    best_hypothesis = (
        hypothesis_model.get("best_supported_hypothesis")
        or first(hypotheses)
    )

    subject = (
        hypothesis_model.get("subject")
        or falsification_model.get("subject")
        or experiment_model.get("subject")
        or query_plan.get("profiles")
        or clean_question
    )

    answer = build_answer(
        question=clean_question,
        subject=subject,
        query_plan=query_plan,
        best_hypothesis=best_hypothesis,
        hypotheses=hypotheses,
        falsification_cases=falsification_cases,
        experiments=experiments,
        discoveries=discoveries,
        runtime=runtime,
        temporal_graph=temporal_graph,
    )

    evidence = collect_evidence(best_hypothesis, discoveries)
    limitations = collect_limitations(falsification_cases, runtime)

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
        "limitations": limitations,
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "temporal_graph": temporal_graph,
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
    subject: Any,
    query_plan: dict[str, Any],
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
    runtime: Any,
    temporal_graph: dict[str, Any],
) -> str:
    """Build the user-facing answer."""
    if not runtime.success:
        return (
            "Atlas could not complete the full research pipeline for this question. "
            "The result should be treated as incomplete until the failed stages are resolved."
        )

    intent = query_plan.get("intent", "interpretation")
    scope = query_plan.get("scope", "general")
    claim = extract_claim(best_hypothesis)

    if not claim:
        claim = (
            "Atlas processed the question successfully, but did not identify one dominant "
            "interpretive claim. The answer should be treated as provisional."
        )

    evidence = collect_evidence(best_hypothesis, discoveries)
    strongest_evidence = evidence[:5]

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

### Temporal-Graph Overlay

{temporal_graph.get("human_interpretation", "")}

**Structural pattern:** {temporal_graph.get("structural_pattern", "")}

**Temporal overlay:** {temporal_graph.get("temporal_overlay", "")}

**Activation pressure:** {temporal_graph.get("activation_pressure", "")}

{middle}

### Natal / Temperamental Influence

Natal influence should explain the *style* of expression, not replace the structural reading.

- Strong Mercury signatures usually show up as language, invention, pattern recognition, translation, and technical cognition.
- Strong Venus signatures shape taste, harmony, attraction, relational tone, and aesthetic refinement.
- Strong Mars signatures increase pressure, action, competition, rupture, and execution.
- Strong Jupiter signatures expand scale, belief, teaching, growth, and long-range vision.
- Strong Saturn signatures create discipline, structure, delay, mastery, responsibility, and constraint.
- Strong Uranus signatures intensify disruption, originality, independence, invention, and rebellion.
- Strong Neptune signatures bring imagination, symbolism, dreams, ambiguity, and idealization.
- Strong Pluto signatures bring depth pressure, transformation, obsession, power, and irreversible change.

When Atlas does not have exact natal placements available, it should speak in probabilities. When natal data is complete, this section should become more specific.

### Probable Outcomes

- **High alignment:** the pattern becomes productive. Each side strengthens what the other lacks.
- **Moderate stress:** differences in pace, communication, emotional need, control strategy, or recognition become visible.
- **Low alignment:** the same differences become conflict, competition, distance, or misunderstanding.
- **Growth path:** the best outcome comes when each role is named clearly and used intentionally.

### Evidence Atlas Used

{format_short_list(strongest_evidence)}

### Main Caution

The strongest uncertainty is: **{pressure_title}**.

Atlas should not overstate final judgment until graph overlap, temporal assumptions, natal data, and evidence strength are checked more deeply.

### Bottom Line

{bottom_line_for_claim(claim, comparison=comparison)}

### Runtime Summary

Atlas used {len(hypotheses)} hypotheses, {len(falsification_cases)} falsification checks, {len(experiments)} proposed experiments, and {len(discoveries)} discovery signals for this answer.

Detected intent: **{intent}**  
Detected scope: **{scope}**"""


def plain_meaning_for_claim(claim: str, *, comparison: bool) -> str:
    """Translate the best claim into simpler language."""
    lower = claim.lower()

    if comparison and ("limited" in lower or "low" in lower):
        return (
            "This does not mean the two subjects are irrelevant to each other. It means "
            "their relationship is probably not smooth similarity. Atlas is seeing contrast, "
            "friction, and transformation more than easy resonance."
        )

    if comparison and "transformation" in lower:
        return (
            "This comparison is best read as a change-producing relationship. The value is "
            "not simple compatibility; it is what each side forces the other to reveal, refine, "
            "resist, or become."
        )

    if "temporal" in lower or "birth" in lower or "nakshatra" in lower:
        return (
            "Atlas is warning that timing data may affect the interpretation. The structural "
            "reading can still be useful, but exact natal or transit conclusions should be "
            "treated carefully."
        )

    return (
        "Atlas found a meaningful interpretive pattern, but the result should be read as a "
        "probable synthesis rather than an absolute verdict."
    )


def relationship_interpretation() -> str:
    """Relationship-specific interpretive section."""
    return """### Interaction Dynamic

Atlas is comparing how two structures react against each other.

A strong relationship reading should not only say whether two profiles are similar. It should describe the feedback loop between them:

- One side may initiate movement while the other stabilizes it.
- One may amplify meaning while the other imposes structure.
- One may generate vision while the other demands proof, form, or control.
- One may expose unresolved pressure in the other.

When the relationship is healthy, contrast becomes productive. When it is strained, the same contrast becomes competition, misunderstanding, or resistance.

For a Tesla/Edison-style comparison, the likely archetypal tension is:

**vision versus execution, revelation versus control, invention versus institution, signal versus ownership.**

That kind of pairing can produce enormous historical force, but it is rarely emotionally simple."""


def profile_or_general_interpretation() -> str:
    """General interpretive section."""
    return """### Structural Dynamic

Atlas is identifying how the subject appears to organize reality.

The core question is not simply â€œwhat traits exist?â€ but:

- What initiates movement?
- What amplifies signal?
- What stabilizes the system?
- What creates stress or distortion?
- What pattern is likely to repeat?

A useful Atlas reading should describe the operating pattern beneath the behavior."""


def bottom_line_for_claim(claim: str, *, comparison: bool) -> str:
    """Build concise bottom line."""
    lower = claim.lower()

    if comparison and ("limited" in lower or "alignment" in lower):
        return (
            "This is not best understood as simple compatibility. It is better understood "
            "as two different kinds of power meeting in the same field. The probable outcome "
            "is creative friction, transformation, and contested influence rather than easy harmony."
        )

    if comparison and "transformation" in lower:
        return (
            "The relationship is valuable because it changes the field. The important question "
            "is not whether the two are alike, but what each one forces into motion in the other."
        )

    return (
        "Atlas sees a meaningful pattern, but the interpretation should stay tied to available "
        "evidence and should become more specific as more deterministic outputs are available."
    )


def build_key_points(
    *,
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Build concise key points."""
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
    """Collect limitations and caveats."""
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
    """Suggest useful follow-up questions."""
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
            f"What natal factors would refine this answer?",
            f"What Kamea outputs would increase confidence?",
        ]

    return dedupe(suggestions)[:6]


def resolve_confidence(best_hypothesis: dict[str, Any] | None) -> str:
    """Resolve readable confidence label."""
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
    """Extract the clearest claim text."""
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
    """Read a stage model from runtime stages."""
    stage = stages.get(stage_name)
    if not stage:
        return {}

    payload = getattr(stage, "payload", {}) or {}
    data = payload.get("data", {})

    model = data.get(model_key)
    return model if isinstance(model, dict) else {}


def is_relationship_scope(scope: str, query_plan: dict[str, Any]) -> bool:
    """Return whether the query is relationship/comparison oriented."""
    if scope == "relationship":
        return True

    intent = str(query_plan.get("intent", ""))
    return "relationship" in intent or "compare" in intent or "comparison" in intent


def ensure_dict_list(value: Any) -> list[dict[str, Any]]:
    """Normalize values to list of dictionaries."""
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        return [value]

    return []


def first(values: list[Any]) -> Any:
    """Return first item or None."""
    return values[0] if values else None


def format_short_list(items: list[str]) -> str:
    """Format a short markdown list."""
    if not items:
        return "- No direct evidence surfaced."

    return "\n".join(f"- {item}" for item in items)


def dedupe(values: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def failure_payload(*, question: str, error: str, answer: str) -> dict[str, Any]:
    """Build a failed QA payload."""
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
        "temporal_graph": temporal_graph,
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

