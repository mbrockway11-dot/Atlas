"""Atlas Query Planner service.

Deterministic intent planner for Atlas AI.

The planner turns a natural-language user request into:
- intent
- scope
- selected services
- confidence
- extracted profile keys when possible

This service does not call the underlying analysis services.
It only plans which services should be called next.
"""

from __future__ import annotations

import json
import re
from typing import Any

from atlas.library.profile_library import list_saved_profiles


QUERY_PLANNER_VERSION = "1.0"


PROFILE_INTENTS = {
    "profile_analysis",
    "narrative_analysis",
    "graph_analysis",
    "temporal_analysis",
    "evidence_analysis",
}

RELATIONSHIP_INTENTS = {
    "relationship_analysis",
    "compatibility_analysis",
    "comparison_analysis",
}

POPULATION_INTENTS = {
    "population_search",
    "nearest_neighbors",
    "cluster_analysis",
    "outlier_analysis",
}

DEFAULT_PROFILE_SERVICES = [
    "profile_report",
    "narrative",
    "evidence",
    "graph_intelligence",
    "temporal",
]

DEFAULT_RELATIONSHIP_SERVICES = [
    "relationship_report",
    "relationship_evidence",
    "relationship_graph_intelligence",
]

DEFAULT_POPULATION_SERVICES = [
    "population_intelligence",
    "population_observatory",
    "population_topology",
]


def list_query_planner_profiles() -> list[str]:
    """Return profiles available to the query planner."""
    return list_saved_profiles()


def build_query_plan_payload(
    query: str,
    *,
    available_profiles: list[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic query plan."""
    profiles = available_profiles or list_query_planner_profiles()
    normalized_query = normalize_text(query)

    extracted_profiles = extract_profile_keys(
        query=query,
        profiles=profiles,
    )

    intent = classify_intent(
        normalized_query=normalized_query,
        extracted_profiles=extracted_profiles,
    )

    scope = resolve_scope(intent, extracted_profiles)
    services = resolve_services(intent, scope)
    confidence = build_planner_confidence(
        query=query,
        intent=intent,
        scope=scope,
        extracted_profiles=extracted_profiles,
        services=services,
    )

    warnings = build_plan_warnings(
        query=query,
        scope=scope,
        extracted_profiles=extracted_profiles,
    )

    plan = {
        "version": QUERY_PLANNER_VERSION,
        "query": query,
        "normalized_query": normalized_query,
        "intent": intent,
        "scope": scope,
        "profiles": extracted_profiles,
        "services": services,
        "confidence": confidence,
        "warnings": warnings,
        "execution_hint": build_execution_hint(scope, extracted_profiles, services),
    }

    return {
        "success": True,
        "version": QUERY_PLANNER_VERSION,
        "query": query,
        "errors": [],
        "warnings": warnings,
        "data": {
            "plan": plan,
            "available_profile_count": len(profiles),
        },
        "exports": {
            "plan_json": plan,
            "markdown": render_query_plan_markdown(plan),
        },
        "metrics": build_plan_metrics(plan),
    }


def classify_intent(
    *,
    normalized_query: str,
    extracted_profiles: list[str],
) -> str:
    """Classify query intent deterministically."""
    if contains_any(
        normalized_query,
        [
            "compare",
            "relationship",
            "compatibility",
            "versus",
            " vs ",
            "between",
            "pair",
            "interaction",
            "dynamic",
            "dynamics",
        ],
    ):
        return "relationship_analysis"

    if contains_any(
        normalized_query,
        [
            "nearest",
            "closest",
            "similar",
            "neighbors",
            "cluster",
            "cohort",
            "population",
            "outlier",
            "group",
            "archetype",
        ],
    ):
        return "population_search"

    if contains_any(
        normalized_query,
        [
            "graph",
            "topology",
            "morphology",
            "nodes",
            "edges",
            "motif",
            "resonance",
            "structure",
        ],
    ):
        return "graph_analysis"

    if contains_any(
        normalized_query,
        [
            "temporal",
            "transit",
            "dasha",
            "natal",
            "birth chart",
            "timing",
            "timeline",
            "forecast",
        ],
    ):
        return "temporal_analysis"

    if contains_any(
        normalized_query,
        [
            "evidence",
            "claim",
            "claims",
            "prove",
            "support",
            "source",
            "why",
            "confidence",
        ],
    ):
        return "evidence_analysis"

    if contains_any(
        normalized_query,
        [
            "narrative",
            "story",
            "interpret",
            "explain",
            "summary",
            "synthesize",
            "analyze",
            "profile",
            "who is",
            "what is",
        ],
    ):
        return "profile_analysis"

    if len(extracted_profiles) >= 2:
        return "relationship_analysis"

    if len(extracted_profiles) == 1:
        return "profile_analysis"

    return "general_atlas_query"


def resolve_scope(
    intent: str,
    extracted_profiles: list[str],
) -> str:
    """Resolve query scope."""
    if intent in RELATIONSHIP_INTENTS or len(extracted_profiles) >= 2:
        return "relationship"

    if intent in POPULATION_INTENTS:
        return "population"

    if intent in PROFILE_INTENTS or len(extracted_profiles) == 1:
        return "profile"

    return "general"


def resolve_services(
    intent: str,
    scope: str,
) -> list[str]:
    """Resolve services to execute."""
    if scope == "relationship":
        services = list(DEFAULT_RELATIONSHIP_SERVICES)

        if intent == "comparison_analysis":
            services.append("profile_report")

        return services

    if scope == "population":
        return list(DEFAULT_POPULATION_SERVICES)

    if scope == "profile":
        if intent == "graph_analysis":
            return [
                "profile_report",
                "graph_intelligence",
                "evidence",
            ]

        if intent == "temporal_analysis":
            return [
                "profile_report",
                "temporal",
                "narrative",
                "evidence",
            ]

        if intent == "evidence_analysis":
            return [
                "profile_report",
                "evidence",
                "narrative",
            ]

        if intent == "narrative_analysis":
            return [
                "profile_report",
                "narrative",
                "evidence",
            ]

        return list(DEFAULT_PROFILE_SERVICES)

    return [
        "atlas_ai",
        "query_planner",
    ]


def extract_profile_keys(
    *,
    query: str,
    profiles: list[str],
) -> list[str]:
    """Extract likely profile keys from query text."""
    normalized_query = normalize_text(query)
    matches: list[str] = []

    for profile_key in profiles:
        aliases = build_profile_aliases(profile_key)

        if any(alias in normalized_query for alias in aliases):
            matches.append(profile_key)

    return dedupe(matches)


def build_profile_aliases(profile_key: str) -> list[str]:
    """Build query aliases for a profile key."""
    normalized_key = normalize_text(profile_key)
    spaced = normalized_key.replace("_", " ")
    compact = normalized_key.replace("_", "")

    aliases = [
        normalized_key,
        spaced,
        compact,
    ]

    parts = [part for part in re.split(r"[_\s-]+", normalized_key) if part]

    if len(parts) >= 2:
        aliases.append(" ".join(parts))

        last_name = parts[-1]
        if len(last_name) >= 4:
            aliases.append(last_name)

    return dedupe([alias for alias in aliases if alias])


def build_planner_confidence(
    *,
    query: str,
    intent: str,
    scope: str,
    extracted_profiles: list[str],
    services: list[str],
) -> dict[str, Any]:
    """Build planner confidence."""
    score = 0.25

    if query.strip():
        score += 0.15

    if intent != "general_atlas_query":
        score += 0.20

    if scope != "general":
        score += 0.15

    if extracted_profiles:
        score += 0.15

    if services:
        score += 0.10

    if scope == "relationship" and len(extracted_profiles) < 2:
        score -= 0.20

    if scope == "profile" and len(extracted_profiles) < 1:
        score -= 0.15

    return confidence_record(score)


def build_plan_warnings(
    *,
    query: str,
    scope: str,
    extracted_profiles: list[str],
) -> list[str]:
    """Build query plan warnings."""
    warnings: list[str] = []

    if not query.strip():
        warnings.append("Query is empty.")

    if scope == "profile" and not extracted_profiles:
        warnings.append("No profile key was confidently extracted.")

    if scope == "relationship" and len(extracted_profiles) < 2:
        warnings.append("Relationship query needs two profile keys.")

    if scope == "population" and not extracted_profiles:
        warnings.append("Population query has no anchor profile.")

    return warnings


def build_execution_hint(
    scope: str,
    profiles: list[str],
    services: list[str],
) -> dict[str, Any]:
    """Build downstream execution hint."""
    if scope == "profile" and profiles:
        return {
            "call": "build_profile_ai_payload",
            "args": {
                "profile_key": profiles[0],
                "services": services,
            },
        }

    if scope == "relationship" and len(profiles) >= 2:
        return {
            "call": "build_relationship_ai_payload",
            "args": {
                "profile_a": profiles[0],
                "profile_b": profiles[1],
                "services": services,
            },
        }

    if scope == "population":
        return {
            "call": "population_services",
            "args": {
                "anchor_profiles": profiles,
                "services": services,
            },
        }

    return {
        "call": "clarify",
        "args": {
            "reason": "Planner could not determine a complete executable scope.",
        },
    }


def build_plan_metrics(plan: dict[str, Any]) -> dict[str, Any]:
    """Build query plan metrics."""
    return {
        "intent": plan.get("intent"),
        "scope": plan.get("scope"),
        "profile_count": len(plan.get("profiles", [])),
        "service_count": len(plan.get("services", [])),
        "warning_count": len(plan.get("warnings", [])),
        "planner_confidence": plan.get("confidence", {}),
    }


def render_query_plan_markdown(plan: dict[str, Any]) -> str:
    """Render query plan as Markdown."""
    confidence = plan.get("confidence", {})

    lines = [
        "# Atlas Query Plan",
        "",
        f"**Version:** {plan.get('version', QUERY_PLANNER_VERSION)}",
        f"**Intent:** {plan.get('intent', 'unknown')}",
        f"**Scope:** {plan.get('scope', 'unknown')}",
        f"**Confidence:** {confidence.get('percent', 0)}% {confidence.get('label', 'unknown')}",
        "",
        "## Query",
        plan.get("query", ""),
        "",
        "## Profiles",
    ]

    profiles = plan.get("profiles", [])
    if profiles:
        for profile in profiles:
            lines.append(f"- {profile}")
    else:
        lines.append("- None detected")

    lines.append("")
    lines.append("## Services")

    for service in plan.get("services", []):
        lines.append(f"- {service}")

    warnings = plan.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")

    lines.append("")
    lines.append("## Execution Hint")
    lines.append("```json")
    lines.append(json.dumps(plan.get("execution_hint", {}), indent=2))
    lines.append("```")

    return "\n".join(lines).strip() + "\n"


def contains_any(text: str, needles: list[str]) -> bool:
    """Return whether text contains any keyword."""
    return any(needle in text for needle in needles)


def normalize_text(value: str) -> str:
    """Normalize text for planning."""
    return " ".join(value.lower().strip().split())


def dedupe(values: list[str]) -> list[str]:
    """Dedupe values while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


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


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def json_export(data: Any) -> str:
    """Serialize query planner JSON."""
    return json.dumps(data, indent=2, sort_keys=True)