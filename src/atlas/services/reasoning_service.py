"""Atlas Reasoning service.

Cross-service deterministic reasoning layer.

The Reasoning service sits above:
- query_planner_service.py
- atlas_ai_service.py

It does not replace Atlas AI.
It interprets Atlas AI synthesis and service confidence into:
- conclusions
- supporting evidence
- conflicts / limitations
- final analyst summary
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.atlas_ai_service import (
    build_profile_ai_payload,
    build_relationship_ai_payload,
)
from atlas.services.query_planner_service import build_query_plan_payload


REASONING_VERSION = "1.0"


def list_reasoning_profiles() -> list[str]:
    """Return profiles available for reasoning."""
    return list_saved_profiles()


def build_reasoning_payload(query: str) -> dict[str, Any]:
    """Build an end-to-end reasoning payload from a natural-language query."""
    plan_payload = build_query_plan_payload(query)
    plan = plan_payload.get("data", {}).get("plan", {})

    execution_payload = execute_plan(plan)
    reasoning = build_reasoning_from_execution(
        query=query,
        plan=plan,
        execution_payload=execution_payload,
    )

    return {
        "success": reasoning.get("success", False),
        "version": REASONING_VERSION,
        "query": query,
        "errors": collect_errors(plan_payload, execution_payload),
        "warnings": collect_warnings(plan_payload, execution_payload, reasoning),
        "data": {
            "plan": plan,
            "execution": build_safe_execution_summary(execution_payload),
            "reasoning": reasoning,
        },
        "exports": {
            "reasoning_json": reasoning,
            "markdown": render_reasoning_markdown(reasoning),
        },
        "metrics": build_reasoning_metrics(reasoning, plan_payload, execution_payload),
    }


def execute_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Execute a query planner execution hint."""
    hint = plan.get("execution_hint", {})
    call = hint.get("call")
    args = hint.get("args", {})

    try:
        if call == "build_profile_ai_payload":
            return build_profile_ai_payload(
                args.get("profile_key", ""),
                services=args.get("services"),
            )

        if call == "build_relationship_ai_payload":
            return build_relationship_ai_payload(
                args.get("profile_a", ""),
                args.get("profile_b", ""),
                services=args.get("services"),
            )

        return {
            "success": False,
            "version": REASONING_VERSION,
            "scope": plan.get("scope", "unknown"),
            "errors": [f"Reasoning executor cannot run call: {call}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": REASONING_VERSION,
            "scope": plan.get("scope", "unknown"),
            "errors": [f"Reasoning execution failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def build_reasoning_from_execution(
    *,
    query: str,
    plan: dict[str, Any],
    execution_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build final reasoning from query plan and Atlas AI execution."""
    synthesis = execution_payload.get("data", {}).get("synthesis", {})
    scope = plan.get("scope", "unknown")
    confidence = build_reasoning_confidence(plan, execution_payload, synthesis)

    conclusions = build_conclusions(plan, execution_payload, synthesis, confidence)
    limitations = build_limitations(plan, execution_payload, synthesis)
    conflicts = build_conflicts(execution_payload, synthesis)
    recommendations = build_recommendations(plan, execution_payload, synthesis)

    return {
        "success": execution_payload.get("success", False),
        "version": REASONING_VERSION,
        "query": query,
        "intent": plan.get("intent"),
        "scope": scope,
        "subject": synthesis.get("subject", resolve_subject_from_plan(plan)),
        "confidence": confidence,
        "final_answer": build_final_answer(
            query=query,
            plan=plan,
            synthesis=synthesis,
            conclusions=conclusions,
            limitations=limitations,
            confidence=confidence,
        ),
        "conclusions": conclusions,
        "limitations": limitations,
        "conflicts": conflicts,
        "recommendations": recommendations,
        "source_summary": {
            "planner": {
                "intent": plan.get("intent"),
                "scope": plan.get("scope"),
                "profiles": plan.get("profiles", []),
                "services": plan.get("services", []),
                "confidence": plan.get("confidence", {}),
            },
            "atlas_ai": {
                "success": execution_payload.get("success", False),
                "metrics": execution_payload.get("metrics", {}),
                "warnings": execution_payload.get("warnings", []),
                "errors": execution_payload.get("errors", []),
            },
        },
    }


def build_conclusions(
    plan: dict[str, Any],
    execution_payload: dict[str, Any],
    synthesis: dict[str, Any],
    confidence: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build evidence-bounded conclusions."""
    conclusions: list[dict[str, Any]] = []

    strengths = synthesis.get("strengths", [])
    risks = synthesis.get("risks", [])
    priorities = synthesis.get("research_priorities", [])

    conclusions.append(
        conclusion(
            text=resolve_primary_conclusion(plan, synthesis, confidence),
            confidence=confidence.get("overall", {}),
            evidence=[
                synthesis.get("executive_summary", ""),
                f"Atlas AI confidence: {format_confidence(synthesis.get('confidence', {}).get('overall', {}))}",
                f"Planner intent: {plan.get('intent')}",
                f"Services: {', '.join(plan.get('services', []))}",
            ],
        )
    )

    if strengths:
        conclusions.append(
            conclusion(
                text="The strongest support comes from the service strengths surfaced by Atlas AI.",
                confidence=confidence.get("support", {}),
                evidence=strengths,
            )
        )

    if risks:
        conclusions.append(
            conclusion(
                text="The interpretation should be bounded by the surfaced risks and warnings.",
                confidence=confidence.get("risk_awareness", {}),
                evidence=risks,
            )
        )

    if priorities:
        conclusions.append(
            conclusion(
                text="The next best research moves are visible from Atlas AI priorities.",
                confidence=confidence.get("priority", {}),
                evidence=priorities,
            )
        )

    return conclusions


def resolve_primary_conclusion(
    plan: dict[str, Any],
    synthesis: dict[str, Any],
    confidence: dict[str, Any],
) -> str:
    """Resolve primary conclusion text."""
    subject = synthesis.get("subject", resolve_subject_from_plan(plan))
    scope = plan.get("scope", "unknown")
    label = confidence.get("overall", {}).get("label", "unknown")

    if scope == "profile":
        return (
            f"{subject} can be analyzed through Atlas with {label} reasoning confidence. "
            "The result should be read as an evidence-bounded profile synthesis."
        )

    if scope == "relationship":
        return (
            f"{subject} can be analyzed through Atlas with {label} reasoning confidence. "
            "The result should be read as a relationship transformation analysis, not a simple compatibility score."
        )

    if scope == "population":
        return (
            f"{subject} requires population-level execution. The current planner identified the intent, "
            "but reasoning v1 does not yet execute population services."
        )

    return (
        "Atlas could not fully resolve the query into an executable reasoning scope."
    )


def build_limitations(
    plan: dict[str, Any],
    execution_payload: dict[str, Any],
    synthesis: dict[str, Any],
) -> list[str]:
    """Build limitations."""
    limitations: list[str] = []

    for warning in execution_payload.get("warnings", []):
        if isinstance(warning, dict):
            limitations.append(str(warning))
        else:
            limitations.append(warning)

    for risk in synthesis.get("risks", []):
        if risk not in limitations:
            limitations.append(risk)

    if execution_payload.get("metrics", {}).get("failed_services", 0) > 0:
        limitations.append("One or more Atlas AI services failed.")

    if plan.get("scope") == "population":
        limitations.append("Population execution is planned but not yet implemented in reasoning v1.")

    if not limitations:
        limitations.append("No major limitations were surfaced by reasoning v1.")

    return dedupe(limitations)


def build_conflicts(
    execution_payload: dict[str, Any],
    synthesis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build deterministic conflict checks."""
    conflicts: list[dict[str, Any]] = []

    metrics = execution_payload.get("metrics", {})
    confidence = metrics.get("overall_confidence", {})
    warning_count = metrics.get("warning_count", 0)
    risk_count = metrics.get("risk_count", 0)

    if confidence.get("label") == "high" and warning_count >= 5:
        conflicts.append(
            {
                "type": "confidence_warning_tension",
                "summary": "High confidence is paired with many warnings.",
                "evidence": [
                    f"Confidence: {format_confidence(confidence)}",
                    f"Warnings: {warning_count}",
                ],
            }
        )

    if confidence.get("label") in {"high", "moderate"} and risk_count >= 5:
        conflicts.append(
            {
                "type": "confidence_risk_tension",
                "summary": "Confidence is moderate/high while many risks are present.",
                "evidence": [
                    f"Confidence: {format_confidence(confidence)}",
                    f"Risks: {risk_count}",
                ],
            }
        )

    if not conflicts:
        conflicts.append(
            {
                "type": "none_detected",
                "summary": "No major deterministic cross-service conflicts were detected.",
                "evidence": [],
            }
        )

    return conflicts


def build_recommendations(
    plan: dict[str, Any],
    execution_payload: dict[str, Any],
    synthesis: dict[str, Any],
) -> list[str]:
    """Build reasoning recommendations."""
    recommendations = list(synthesis.get("research_priorities", []))

    if plan.get("scope") == "profile":
        recommendations.append("Use Evidence Explorer to inspect claim-level support.")
        recommendations.append("Use Graph Explorer to inspect structural assumptions.")

    if plan.get("scope") == "relationship":
        recommendations.append("Inspect relationship evidence before treating the result as compatibility.")
        recommendations.append("Compare graph similarity and mutation separately.")

    if execution_payload.get("metrics", {}).get("warning_count", 0) > 0:
        recommendations.append("Resolve warnings before using strong language in final interpretation.")

    return dedupe(recommendations)


def build_reasoning_confidence(
    plan: dict[str, Any],
    execution_payload: dict[str, Any],
    synthesis: dict[str, Any],
) -> dict[str, Any]:
    """Build reasoning confidence from planner and Atlas AI confidence."""
    planner_score = safe_float(plan.get("confidence", {}).get("score"))
    atlas_score = safe_float(
        execution_payload.get("metrics", {}).get("overall_confidence", {}).get("score")
    )

    warning_count = safe_int(execution_payload.get("metrics", {}).get("warning_count"))
    error_count = safe_int(execution_payload.get("metrics", {}).get("error_count"))
    failed_count = safe_int(execution_payload.get("metrics", {}).get("failed_services"))

    warning_penalty = min(warning_count * 0.015, 0.15)
    error_penalty = min(error_count * 0.08, 0.32)
    failure_penalty = min(failed_count * 0.12, 0.36)

    base_score = (
        planner_score * 0.30
        + atlas_score * 0.70
    )

    overall_score = clamp(
        base_score
        - warning_penalty
        - error_penalty
        - failure_penalty
    )

    support_score = clamp(overall_score + 0.05)
    risk_awareness_score = clamp(overall_score)
    priority_score = clamp(overall_score + 0.03)

    return {
        "overall": confidence_record(overall_score),
        "base": confidence_record(base_score),
        "planner": confidence_record(planner_score),
        "atlas_ai": confidence_record(atlas_score),
        "support": confidence_record(support_score),
        "risk_awareness": confidence_record(risk_awareness_score),
        "priority": confidence_record(priority_score),
        "penalties": {
            "warnings": {
                "count": warning_count,
                "penalty": round(warning_penalty, 4),
            },
            "errors": {
                "count": error_count,
                "penalty": round(error_penalty, 4),
            },
            "failures": {
                "count": failed_count,
                "penalty": round(failure_penalty, 4),
            },
        },
    }


def build_final_answer(
    *,
    query: str,
    plan: dict[str, Any],
    synthesis: dict[str, Any],
    conclusions: list[dict[str, Any]],
    limitations: list[str],
    confidence: dict[str, Any],
) -> str:
    """Build final answer text."""
    subject = synthesis.get("subject", resolve_subject_from_plan(plan))
    confidence_text = format_confidence(confidence.get("overall", {}))

    primary = conclusions[0].get("conclusion", "") if conclusions else ""

    lines = [
        f"Atlas Reasoning analyzed **{subject}** for the query: “{query}”.",
        "",
        primary,
        "",
        f"Overall reasoning confidence: **{confidence_text}**.",
    ]

    if limitations:
        lines.append("")
        lines.append("Primary limitations:")
        for item in limitations[:5]:
            lines.append(f"- {item}")

    recommendations = synthesis.get("research_priorities", [])
    if recommendations:
        lines.append("")
        lines.append("Next research priorities:")
        for item in recommendations[:5]:
            lines.append(f"- {item}")

    return "\n".join(lines).strip()


def build_reasoning_metrics(
    reasoning: dict[str, Any],
    plan_payload: dict[str, Any],
    execution_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build reasoning metrics."""
    markdown = render_reasoning_markdown(reasoning)

    return {
        "intent": reasoning.get("intent"),
        "scope": reasoning.get("scope"),
        "conclusion_count": len(reasoning.get("conclusions", [])),
        "limitation_count": len(reasoning.get("limitations", [])),
        "conflict_count": len(reasoning.get("conflicts", [])),
        "recommendation_count": len(reasoning.get("recommendations", [])),
        "word_count": len(markdown.split()),
        "overall_confidence": reasoning.get("confidence", {}).get("overall", {}),
        "planner_confidence": reasoning.get("confidence", {}).get("planner", {}),
        "atlas_ai_confidence": reasoning.get("confidence", {}).get("atlas_ai", {}),
        "source_warning_count": len(collect_warnings(plan_payload, execution_payload, reasoning)),
        "source_error_count": len(collect_errors(plan_payload, execution_payload)),
    }


def render_reasoning_markdown(reasoning: dict[str, Any]) -> str:
    """Render reasoning as Markdown."""
    lines = [
        f"# Atlas Reasoning: {reasoning.get('subject', 'Unknown')}",
        "",
        f"**Version:** {reasoning.get('version', REASONING_VERSION)}",
        f"**Intent:** {reasoning.get('intent', 'unknown')}",
        f"**Scope:** {reasoning.get('scope', 'unknown')}",
        "",
        "## Final Answer",
        reasoning.get("final_answer", ""),
        "",
        "## Confidence",
    ]

    confidence = reasoning.get("confidence", {})
    for key, record in confidence.items():
        if isinstance(record, dict) and "percent" in record:
            lines.append(
                f"- {key.replace('_', ' ').title()}: "
                f"{record.get('label', 'unknown')} ({record.get('percent', 0)}%)"
            )

    lines.append("")
    lines.append("## Conclusions")
    for item in reasoning.get("conclusions", []):
        item_confidence = item.get("confidence", {})
        lines.append(
            f"- {item.get('conclusion', '')} "
            f"[{item_confidence.get('label', 'unknown')}, "
            f"{item_confidence.get('percent', 0)}%]"
        )

        for evidence in item.get("evidence", []):
            lines.append(f"  - Evidence: {evidence}")

    lines.append("")
    lines.append("## Limitations")
    for item in reasoning.get("limitations", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Conflicts")
    for item in reasoning.get("conflicts", []):
        lines.append(f"- {item.get('summary', '')}")

    lines.append("")
    lines.append("## Recommendations")
    for item in reasoning.get("recommendations", []):
        lines.append(f"- {item}")

    return "\n".join(lines).strip() + "\n"


def conclusion(
    *,
    text: str,
    confidence: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build conclusion."""
    return {
        "conclusion": text,
        "confidence": confidence,
        "evidence": [item for item in evidence if item],
    }


def build_safe_execution_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe execution summary."""
    return {
        "success": payload.get("success", False),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "profile_key": payload.get("profile_key"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "synthesis": payload.get("data", {}).get("synthesis", {}),
    }


def resolve_subject_from_plan(plan: dict[str, Any]) -> str:
    """Resolve subject label from plan."""
    profiles = plan.get("profiles", [])

    if len(profiles) >= 2:
        return f"{profiles[0]} ↔ {profiles[1]}"

    if len(profiles) == 1:
        return profiles[0]

    return plan.get("query", "Unknown")


def collect_errors(
    plan_payload: dict[str, Any],
    execution_payload: dict[str, Any],
) -> list[Any]:
    """Collect errors."""
    errors = []

    for error in plan_payload.get("errors", []):
        errors.append({"source": "query_planner", "error": error})

    for error in execution_payload.get("errors", []):
        errors.append({"source": "atlas_ai", "error": error})

    return errors


def collect_warnings(
    plan_payload: dict[str, Any],
    execution_payload: dict[str, Any],
    reasoning: dict[str, Any] | None = None,
) -> list[str]:
    """Collect warnings."""
    warnings: list[str] = []

    for warning in plan_payload.get("warnings", []):
        warnings.append(f"query_planner: {warning}")

    for warning in execution_payload.get("warnings", []):
        warnings.append(f"atlas_ai: {warning}")

    if reasoning:
        for limitation in reasoning.get("limitations", []):
            if limitation != "No major limitations were surfaced by reasoning v1.":
                warnings.append(f"reasoning: {limitation}")

    return dedupe(warnings)


def format_confidence(record: dict[str, Any]) -> str:
    """Format confidence record."""
    if not isinstance(record, dict):
        return "n/a"

    return f"{record.get('percent', 0)}% {record.get('label', 'unknown')}"


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
    if score >= 0.85:
        return "high"

    if score >= 0.65:
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


def safe_int(value: Any) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def dedupe(values: list[str]) -> list[str]:
    """Dedupe values while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def json_export(data: Any) -> str:
    """Serialize reasoning JSON."""
    return json.dumps(data, indent=2, sort_keys=True)