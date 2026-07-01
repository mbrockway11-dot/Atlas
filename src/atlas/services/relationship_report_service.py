"""Canonical Relationship Report service.

This service interprets interactions between two Atlas profiles using
existing graph/morphology and profile report services.

No new symbolic algorithms are introduced here.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_service import build_morphology_payload
from atlas.services.profile_report_service import (
    build_profile_report_payload,
    json_export,
)


def list_relationship_report_profiles() -> list[str]:
    """Return profiles available for relationship reporting."""
    return list_saved_profiles()


def build_relationship_report_payload(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Build relationship report between two profiles."""
    if profile_a == profile_b:
        return failure_payload(
            profile_a,
            profile_b,
            "Select two different profiles.",
        )

    profile_report_a = build_profile_report_payload(profile_a)
    profile_report_b = build_profile_report_payload(profile_b)
    morphology_payload = build_morphology_payload(profile_a, profile_b)

    errors = collect_errors(profile_report_a, profile_report_b, morphology_payload)
    warnings = collect_warnings(profile_report_a, profile_report_b, morphology_payload)

    if not profile_report_a.get("success") or not profile_report_b.get("success"):
        return {
            "success": False,
            "profile_a": profile_a,
            "profile_b": profile_b,
            "errors": errors,
            "warnings": warnings,
            "data": {
                "profile_a": safe_profile_summary(profile_report_a),
                "profile_b": safe_profile_summary(profile_report_b),
                "morphology": safe_morphology_summary(morphology_payload),
            },
            "exports": {},
            "metrics": build_relationship_metrics(
                profile_report_a,
                profile_report_b,
                morphology_payload,
            ),
        }

    report = build_relationship_markdown(
        profile_a=profile_a,
        profile_b=profile_b,
        profile_report_a=profile_report_a,
        profile_report_b=profile_report_b,
        morphology_payload=morphology_payload,
    )

    structured = build_structured_relationship_interpretation(
        profile_a=profile_a,
        profile_b=profile_b,
        profile_report_a=profile_report_a,
        profile_report_b=profile_report_b,
        morphology_payload=morphology_payload,
    )

    payload: dict[str, Any] = {
        "success": True,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": errors,
        "warnings": warnings,
        "data": {
            "profile_a": safe_profile_summary(profile_report_a),
            "profile_b": safe_profile_summary(profile_report_b),
            "morphology": safe_morphology_summary(morphology_payload),
            "structured_interpretation": structured,
        },
        "exports": {
            "markdown": report,
            "relationship_json": structured,
        },
        "metrics": build_relationship_metrics(
            profile_report_a,
            profile_report_b,
            morphology_payload,
        ),
    }

    payload["exports"]["full_payload_json"] = build_safe_relationship_export(payload)

    return payload


def build_relationship_markdown(
    *,
    profile_a: str,
    profile_b: str,
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> str:
    """Build readable Markdown relationship report."""
    name_a = resolve_report_name(profile_a, profile_report_a)
    name_b = resolve_report_name(profile_b, profile_report_b)

    metrics = build_relationship_metrics(
        profile_report_a,
        profile_report_b,
        morphology_payload,
    )

    sections = build_structured_relationship_interpretation(
        profile_a=profile_a,
        profile_b=profile_b,
        profile_report_a=profile_report_a,
        profile_report_b=profile_report_b,
        morphology_payload=morphology_payload,
    )

    lines = [
        f"# Atlas Relationship Report: {name_a} ↔ {name_b}",
        "",
        "## Executive Summary",
        f"- Profile A: {name_a}",
        f"- Profile B: {name_b}",
        f"- Morphology class: {metrics.get('morphology_class', 'n/a')}",
        f"- Morphology similarity: {format_float(metrics.get('morphology_similarity'))}",
        f"- Mutation score: {format_float(metrics.get('mutation_score'))}",
        f"- Shared readiness: {metrics.get('shared_readiness', 'partial')}",
        "",
    ]

    for section in sections.get("sections", []):
        lines.append(f"## {section.get('title', 'Untitled Section')}")
        lines.append(section.get("summary", ""))

        details = section.get("details", [])
        if details:
            lines.append("")
            for detail in details:
                lines.append(f"- {detail}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_structured_relationship_interpretation(
    *,
    profile_a: str,
    profile_b: str,
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic relationship interpretation sections."""
    name_a = resolve_report_name(profile_a, profile_report_a)
    name_b = resolve_report_name(profile_b, profile_report_b)

    metrics = build_relationship_metrics(
        profile_report_a,
        profile_report_b,
        morphology_payload,
    )

    morphology = safe_morphology_summary(morphology_payload)

    return {
        "version": "1.0",
        "profile_a": name_a,
        "profile_b": name_b,
        "sections": [
            {
                "title": "Relationship Overview",
                "summary": (
                    f"{name_a} and {name_b} are interpreted through existing Atlas "
                    "profile reports and graph morphology comparison."
                ),
                "details": [
                    f"Profile A temporal layer available: {metrics.get('profile_a_temporal')}",
                    f"Profile B temporal layer available: {metrics.get('profile_b_temporal')}",
                    f"Profile A graph layer available: {metrics.get('profile_a_graph')}",
                    f"Profile B graph layer available: {metrics.get('profile_b_graph')}",
                ],
            },
            {
                "title": "Morphological Interaction",
                "summary": (
                    "Morphology describes the structural transformation required to move "
                    "from one identity graph stack to the other."
                ),
                "details": [
                    f"Morphology class: {metrics.get('morphology_class', 'n/a')}",
                    f"Distance: {format_float(metrics.get('morphology_distance'))}",
                    f"Similarity: {format_float(metrics.get('morphology_similarity'))}",
                    f"Mutation score: {format_float(metrics.get('mutation_score'))}",
                ],
            },
            {
                "title": "Communication Dynamics",
                "summary": build_communication_summary(metrics),
                "details": [
                    "High structural similarity tends to indicate easier recognition patterns.",
                    "High mutation distance suggests more translation effort between perspectives.",
                    "Graph and temporal warnings should be reviewed before making strong claims.",
                ],
            },
            {
                "title": "Complementarity and Tension",
                "summary": build_complementarity_summary(metrics),
                "details": [
                    f"Profile A sections: {metrics.get('profile_a_sections', 0)}",
                    f"Profile B sections: {metrics.get('profile_b_sections', 0)}",
                    f"Combined warning count: {metrics.get('warning_count', 0)}",
                    f"Combined error count: {metrics.get('error_count', 0)}",
                ],
            },
            {
                "title": "Interpretive Cautions",
                "summary": (
                    "This relationship report is deterministic and grounded in available "
                    "Atlas service outputs. Missing birth times, missing graph nodes, or "
                    "missing profile artifacts reduce certainty."
                ),
                "details": build_caution_details(
                    profile_report_a,
                    profile_report_b,
                    morphology_payload,
                ),
            },
        ],
        "metrics": metrics,
        "morphology": morphology,
    }


def build_communication_summary(metrics: dict[str, Any]) -> str:
    """Build communication summary from morphology metrics."""
    similarity = metrics.get("morphology_similarity")

    try:
        similarity_value = float(similarity)
    except (TypeError, ValueError):
        return "Communication dynamics cannot be strongly estimated because morphology similarity is unavailable."

    if similarity_value >= 0.75:
        return "The profiles appear structurally familiar to each other, suggesting easier pattern recognition and faster mutual translation."

    if similarity_value >= 0.45:
        return "The profiles show partial structural overlap, suggesting both recognition and meaningful difference."

    return "The profiles appear structurally distant, suggesting the interaction may require deliberate translation and patience."


def build_complementarity_summary(metrics: dict[str, Any]) -> str:
    """Build complementarity summary from mutation score."""
    mutation = metrics.get("mutation_score")

    try:
        mutation_value = float(mutation)
    except (TypeError, ValueError):
        return "Complementarity cannot be strongly estimated because mutation score is unavailable."

    if mutation_value >= 0.70:
        return "The relationship may carry strong contrast and transformative pressure."

    if mutation_value >= 0.35:
        return "The relationship may combine familiarity with enough difference to create learning and adaptation."

    return "The relationship appears structurally close, emphasizing resonance more than contrast."


def build_caution_details(
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> list[str]:
    """Build caution details from warnings/errors."""
    details: list[str] = []

    for label, payload in [
        ("Profile A", profile_report_a),
        ("Profile B", profile_report_b),
        ("Morphology", morphology_payload),
    ]:
        for warning in payload.get("warnings", []):
            details.append(f"{label} warning: {warning}")

        for error in payload.get("errors", []):
            details.append(f"{label} error: {error}")

    if not details:
        details.append("No service warnings or errors were reported.")

    return details


def build_relationship_metrics(
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build relationship-level metrics."""
    metrics_a = profile_report_a.get("metrics", {})
    metrics_b = profile_report_b.get("metrics", {})
    morphology_metrics = morphology_payload.get("metrics", {})

    return {
        "profile_a_temporal": metrics_a.get("has_temporal", False),
        "profile_b_temporal": metrics_b.get("has_temporal", False),
        "profile_a_graph": metrics_a.get("has_graph", False),
        "profile_b_graph": metrics_b.get("has_graph", False),
        "profile_a_sections": metrics_a.get("section_count", 0),
        "profile_b_sections": metrics_b.get("section_count", 0),
        "morphology_class": morphology_metrics.get("morphology_class", "n/a"),
        "morphology_distance": morphology_metrics.get("distance", 0),
        "morphology_similarity": morphology_metrics.get("similarity", 0),
        "mutation_score": morphology_metrics.get("mutation_score", 0),
        "warning_count": (
            len(profile_report_a.get("warnings", []))
            + len(profile_report_b.get("warnings", []))
            + len(morphology_payload.get("warnings", []))
        ),
        "error_count": (
            len(profile_report_a.get("errors", []))
            + len(profile_report_b.get("errors", []))
            + len(morphology_payload.get("errors", []))
        ),
        "shared_readiness": resolve_shared_readiness(
            profile_report_a,
            profile_report_b,
            morphology_payload,
        ),
    }


def resolve_shared_readiness(
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> str:
    """Resolve readiness label."""
    if not profile_report_a.get("success") or not profile_report_b.get("success"):
        return "blocked"

    if not morphology_payload.get("success"):
        return "partial"

    if profile_report_a.get("warnings") or profile_report_b.get("warnings"):
        return "caution"

    return "ready"


def safe_profile_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build safe profile summary."""
    return {
        "success": payload.get("success"),
        "profile_key": payload.get("profile_key"),
        "profile_dir": payload.get("profile_dir"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "report": payload.get("data", {}).get("report", {}),
        "interpretation": payload.get("data", {}).get("interpretation", {}),
    }


def safe_morphology_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build safe morphology summary."""
    morphology_data = payload.get("data", {}).get("morphology_data", {})

    return {
        "success": payload.get("success"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "morphology": morphology_data,
    }


def build_safe_relationship_export(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe relationship export."""
    return {
        "success": payload.get("success"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "structured_interpretation": payload.get("data", {}).get(
            "structured_interpretation",
            {},
        ),
    }


def resolve_report_name(profile_key: str, payload: dict[str, Any]) -> str:
    """Resolve readable profile name."""
    report = payload.get("data", {}).get("report", {})
    name = report.get("name")

    if name:
        return str(name)

    metrics = payload.get("metrics", {})
    graph_metrics = metrics.get("graph_metrics", {})
    graph_name = graph_metrics.get("name")

    if graph_name:
        return str(graph_name)

    return profile_key.replace("_", " ").title()


def collect_errors(*payloads: dict[str, Any]) -> list[Any]:
    """Collect errors from payloads."""
    errors: list[Any] = []

    for payload in payloads:
        errors.extend(payload.get("errors", []))

    return errors


def collect_warnings(*payloads: dict[str, Any]) -> list[str]:
    """Collect warnings from payloads."""
    warnings: list[str] = []

    for payload in payloads:
        warnings.extend(str(item) for item in payload.get("warnings", []))

    return warnings


def failure_payload(profile_a: str, profile_b: str, message: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": [message],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {},
    }


def format_float(value: Any) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def relationship_json_export(data: Any) -> str:
    """Serialize relationship data."""
    return json.dumps(data, indent=2, sort_keys=True)


# Backward-compatible export name.
json_export_relationship = relationship_json_export