"""Atlas Cognition Kernel.

The cognition layer is the high-level "mind" of Atlas.

It coordinates:
- reasoning kernel
- semantic interpretation
- narrative interpretation
- temporal composite intelligence
- future graph / Kamea / market / civilization layers

This module should stay orchestration-focused.
"""

from __future__ import annotations

from typing import Any

from atlas.reasoning import answer_question as run_reasoning
from atlas.services.temporal_composite_intelligence_service import (
    build_temporal_composite_intelligence,
)


COGNITION_KERNEL_VERSION = "1.0"


def think(
    question: str,
    *,
    profiles: list[str] | None = None,
    date_window: str = "",
    graph_payload: dict[str, Any] | None = None,
    temporal_payloads: dict[str, dict[str, Any]] | None = None,
    natal_payloads: dict[str, dict[str, Any]] | None = None,
    relationship_payload: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Run Atlas cognition over a user question."""
    clean_question = question.strip()

    if not clean_question:
        return failure_payload(question=question, error="Question is required.")

    reasoning = run_reasoning(clean_question)

    resolved_profiles = profiles or reasoning.get("profiles", [])
    resolved_scope = reasoning.get("scope", "general")
    resolved_intent = reasoning.get("intent", "interpretation")

    temporal_composite: dict[str, Any] = {}

    if should_run_temporal_composite(
        question=clean_question,
        profiles=resolved_profiles,
        date_window=date_window,
        scope=resolved_scope,
    ):
        temporal_composite = build_temporal_composite_intelligence(
            profiles=resolved_profiles,
            date_window=date_window or infer_date_window(clean_question),
            graph_payload=graph_payload or {},
            temporal_payloads=temporal_payloads or {},
            natal_payloads=natal_payloads or {},
            relationship_payload=relationship_payload or {},
            evidence=evidence or reasoning.get("evidence", []),
        )

    answer = compose_cognitive_answer(
        reasoning=reasoning,
        temporal_composite=temporal_composite,
    )

    return {
        "success": reasoning.get("success", False),
        "version": COGNITION_KERNEL_VERSION,
        "question": clean_question,
        "answer": answer,
        "intent": resolved_intent,
        "scope": resolved_scope,
        "profiles": resolved_profiles,
        "reasoning": reasoning,
        "temporal_composite": temporal_composite,
        "confidence": resolve_confidence(reasoning, temporal_composite),
        "evidence": collect_evidence(reasoning, temporal_composite),
        "limitations": collect_limitations(reasoning, temporal_composite),
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            reasoning=reasoning,
            temporal_composite=temporal_composite,
        ),
        "metrics": {
            "reasoning_completed": bool(reasoning),
            "temporal_composite_completed": bool(temporal_composite),
            "reasoning_hypotheses": reasoning.get("metrics", {}).get("hypotheses", 0),
            "reasoning_experiments": reasoning.get("metrics", {}).get("experiments", 0),
            "reasoning_discoveries": reasoning.get("metrics", {}).get("discoveries", 0),
        },
        "warnings": reasoning.get("warnings", []),
        "errors": reasoning.get("errors", []),
    }


def should_run_temporal_composite(
    *,
    question: str,
    profiles: list[str],
    date_window: str,
    scope: str,
) -> bool:
    """Decide whether temporal composite intelligence should run."""
    text = question.lower()

    temporal_tokens = [
        "future",
        "next",
        "month",
        "year",
        "transit",
        "dasha",
        "timing",
        "window",
        "when",
        "forecast",
        "behave",
        "behavior",
        "composite",
    ]

    if date_window:
        return True

    if len(profiles) >= 2 and any(token in text for token in temporal_tokens):
        return True

    if scope in {"relationship", "group", "civilization"} and any(
        token in text for token in temporal_tokens
    ):
        return True

    return False


def infer_date_window(question: str) -> str:
    """Infer simple date window text from question."""
    text = question.lower()

    if "next 6 months" in text or "next six months" in text:
        return "next 6 months"

    if "next month" in text:
        return "next month"

    if "next year" in text:
        return "next year"

    if "this year" in text:
        return "this year"

    if "future" in text:
        return "future window"

    return "unspecified"


def compose_cognitive_answer(
    *,
    reasoning: dict[str, Any],
    temporal_composite: dict[str, Any],
) -> str:
    """Compose the final cognition-level answer."""
    base_answer = reasoning.get("answer", "")

    if not temporal_composite:
        return base_answer

    composite_summary = temporal_composite.get("human_summary", "")
    probable_outcomes = temporal_composite.get("probable_outcomes", [])
    stress_points = temporal_composite.get("stress_points", [])
    supportive_conditions = temporal_composite.get("supportive_conditions", [])
    timing_cautions = temporal_composite.get("timing_cautions", [])

    return f"""{base_answer}

### Temporal Composite Intelligence

{composite_summary}

### Future Behavioral Pattern

Atlas reads the future-facing layer as a timed activation of the existing structure. The baseline graph shows the recurring pattern; the Vedic/natal layer describes how each person behaves under pressure; the temporal layer describes when those behaviors become more visible.

### Probable Temporal Outcomes

{format_list(probable_outcomes)}

### Stress Points

{format_list(stress_points)}

### Supportive Conditions

{format_list(supportive_conditions)}

### Timing Cautions

{format_list(timing_cautions)}
"""


def resolve_confidence(
    reasoning: dict[str, Any],
    temporal_composite: dict[str, Any],
) -> str:
    """Resolve combined confidence."""
    if temporal_composite:
        return temporal_composite.get("confidence", reasoning.get("confidence", "unknown"))

    return reasoning.get("confidence", "unknown")


def collect_evidence(
    reasoning: dict[str, Any],
    temporal_composite: dict[str, Any],
) -> list[str]:
    """Collect combined evidence."""
    evidence: list[str] = []

    reasoning_evidence = reasoning.get("evidence", [])
    if isinstance(reasoning_evidence, list):
        evidence.extend(str(item) for item in reasoning_evidence)

    temporal_evidence = temporal_composite.get("evidence", [])
    if isinstance(temporal_evidence, list):
        evidence.extend(str(item) for item in temporal_evidence)

    return dedupe(evidence)[:12]


def collect_limitations(
    reasoning: dict[str, Any],
    temporal_composite: dict[str, Any],
) -> list[str]:
    """Collect combined limitations."""
    limitations: list[str] = []

    reasoning_limitations = reasoning.get("limitations", [])
    if isinstance(reasoning_limitations, list):
        limitations.extend(str(item) for item in reasoning_limitations)

    composite_missing = temporal_composite.get("missing_requirements", [])
    if isinstance(composite_missing, list):
        limitations.extend(f"Missing temporal composite requirement: {item}" for item in composite_missing)

    return dedupe(limitations)[:12]


def build_suggested_questions(
    *,
    question: str,
    reasoning: dict[str, Any],
    temporal_composite: dict[str, Any],
) -> list[str]:
    """Build cognition-level follow-up questions."""
    suggestions: list[str] = []

    existing = reasoning.get("suggested_next_questions", [])
    if isinstance(existing, list):
        suggestions.extend(str(item) for item in existing[:3])

    profiles = reasoning.get("profiles", [])
    if len(profiles) >= 2:
        a = humanize(profiles[0])
        b = humanize(profiles[1])
        suggestions.extend(
            [
                f"How do {a} and {b} behave over the next 6 months?",
                f"What timing window increases stress between {a} and {b}?",
                f"What would improve alignment between {a} and {b}?",
            ]
        )

    if temporal_composite:
        suggestions.append("Which transit or dasha factor is driving the strongest activation?")

    if not suggestions:
        suggestions.extend(
            [
                f"What evidence supports this answer to: {question}?",
                f"What would falsify this interpretation?",
                f"What temporal window should Atlas test next?",
            ]
        )

    return dedupe(suggestions)[:6]


def format_list(items: list[Any]) -> str:
    """Format a markdown list."""
    if not items:
        return "- No items generated."

    return "\n".join(f"- {item}" for item in items if item)


def dedupe(values: list[str]) -> list[str]:
    """Deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def humanize(value: str) -> str:
    """Humanize profile keys."""
    return str(value).replace("_", " ").title()


def failure_payload(*, question: str, error: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": COGNITION_KERNEL_VERSION,
        "question": question,
        "answer": "Ask Atlas a question first.",
        "intent": "none",
        "scope": "none",
        "profiles": [],
        "reasoning": {},
        "temporal_composite": {},
        "confidence": "none",
        "evidence": [],
        "limitations": [error],
        "suggested_next_questions": [],
        "metrics": {
            "reasoning_completed": False,
            "temporal_composite_completed": False,
            "reasoning_hypotheses": 0,
            "reasoning_experiments": 0,
            "reasoning_discoveries": 0,
        },
        "warnings": [],
        "errors": [error],
    }