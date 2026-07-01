"""Canonical Relationship Report service v2.

This service interprets interactions between two Atlas profiles using
existing profile report and graph/morphology services.

It does not introduce new symbolic algorithms.
It synthesizes existing outputs into claims, evidence, confidence, cautions,
and readable Markdown.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_service import build_morphology_payload
from atlas.services.profile_report_service import build_profile_report_payload


RELATIONSHIP_REPORT_VERSION = "2.0"


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

    confidence = build_relationship_confidence(
        profile_report_a=profile_report_a,
        profile_report_b=profile_report_b,
        morphology_payload=morphology_payload,
        warnings=warnings,
        errors=errors,
    )

    structured = build_structured_relationship_interpretation(
        profile_a=profile_a,
        profile_b=profile_b,
        profile_report_a=profile_report_a,
        profile_report_b=profile_report_b,
        morphology_payload=morphology_payload,
        confidence=confidence,
    )

    markdown = render_relationship_markdown(structured)

    payload: dict[str, Any] = {
        "success": (
            profile_report_a.get("success", False)
            and profile_report_b.get("success", False)
        ),
        "profile_a": profile_a,
        "profile_b": profile_b,
        "version": RELATIONSHIP_REPORT_VERSION,
        "errors": errors,
        "warnings": warnings,
        "data": {
            "profile_a": safe_profile_summary(profile_report_a),
            "profile_b": safe_profile_summary(profile_report_b),
            "morphology": safe_morphology_summary(morphology_payload),
            "structured_interpretation": structured,
        },
        "exports": {
            "markdown": markdown,
            "relationship_json": structured,
        },
        "metrics": build_relationship_metrics(
            profile_report_a=profile_report_a,
            profile_report_b=profile_report_b,
            morphology_payload=morphology_payload,
            confidence=confidence,
            structured=structured,
            warnings=warnings,
            errors=errors,
        ),
    }

    payload["exports"]["full_payload_json"] = build_safe_relationship_export(payload)

    return payload


def build_structured_relationship_interpretation(
    *,
    profile_a: str,
    profile_b: str,
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic relationship interpretation sections."""
    name_a = resolve_report_name(profile_a, profile_report_a)
    name_b = resolve_report_name(profile_b, profile_report_b)

    metrics = base_relationship_metrics(
        profile_report_a,
        profile_report_b,
        morphology_payload,
    )

    sections = [
        build_relationship_overview_section(
            name_a,
            name_b,
            metrics,
            confidence,
        ),
        build_morphological_interaction_section(
            name_a,
            name_b,
            metrics,
            morphology_payload,
            confidence,
        ),
        build_communication_dynamics_section(
            name_a,
            name_b,
            metrics,
            confidence,
        ),
        build_complementarity_section(
            name_a,
            name_b,
            metrics,
            confidence,
        ),
        build_tension_section(
            name_a,
            name_b,
            metrics,
            confidence,
        ),
        build_readiness_section(
            name_a,
            name_b,
            metrics,
            confidence,
        ),
        build_research_cautions_section(
            profile_report_a,
            profile_report_b,
            morphology_payload,
            confidence,
        ),
    ]

    return {
        "version": RELATIONSHIP_REPORT_VERSION,
        "profile_a": name_a,
        "profile_b": name_b,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "morphology_class": metrics.get("morphology_class", "n/a"),
            "morphology_similarity": metrics.get("morphology_similarity", 0),
            "mutation_score": metrics.get("mutation_score", 0),
            "relationship_readiness": metrics.get("shared_readiness", "unknown"),
            "overall_confidence": confidence.get("overall", {}),
        },
    }


def build_relationship_overview_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build relationship overview."""
    summary = (
        f"{name_a} and {name_b} are interpreted through profile reports, "
        "temporal availability, graph availability, and graph morphology. "
        f"The current relationship synthesis carries "
        f"{confidence.get('overall', {}).get('label', 'unknown')} confidence."
    )

    claims = [
        claim(
            "Both profiles are available for relationship synthesis.",
            confidence.get("profile_readiness", {}),
            [
                f"{name_a} temporal available: {metrics.get('profile_a_temporal')}",
                f"{name_b} temporal available: {metrics.get('profile_b_temporal')}",
                f"{name_a} graph available: {metrics.get('profile_a_graph')}",
                f"{name_b} graph available: {metrics.get('profile_b_graph')}",
            ],
        ),
        claim(
            "The relationship report is grounded in existing Atlas service outputs.",
            confidence.get("overall", {}),
            [
                "Source: profile_report_service",
                "Source: graph_service.build_morphology_payload",
                "Source: relationship_report_service",
            ],
        ),
    ]

    details = [
        f"Profile A sections: {metrics.get('profile_a_sections', 0)}",
        f"Profile B sections: {metrics.get('profile_b_sections', 0)}",
        f"Warnings: {metrics.get('warning_count', 0)}",
        f"Errors: {metrics.get('error_count', 0)}",
        f"Readiness: {metrics.get('shared_readiness', 'unknown')}",
    ]

    cautions = []

    if metrics.get("warning_count", 0):
        cautions.append("Warnings are present and should be reviewed before strong interpretation.")

    return section("Relationship Overview", summary, details, claims, cautions)


def build_morphological_interaction_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    morphology_payload: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build morphology interaction section."""
    morphology_class = metrics.get("morphology_class", "n/a")
    similarity = metrics.get("morphology_similarity", 0)
    mutation = metrics.get("mutation_score", 0)

    summary = (
        "Morphology describes the structural transformation required to move "
        f"from {name_a}'s identity graph stack to {name_b}'s identity graph stack. "
        f"The current morphology class is {morphology_class}."
    )

    claims = [
        claim(
            "Graph morphology can be used as the structural comparison layer.",
            confidence.get("morphology", {}),
            [
                f"Morphology service success: {morphology_payload.get('success')}",
                f"Morphology class: {morphology_class}",
                f"Similarity: {similarity}",
                f"Mutation score: {mutation}",
            ],
        ),
        claim(
            "The interaction should be read as transformation, not simple compatibility.",
            confidence.get("morphology", {}),
            [
                "Morphology compares structural change between graph stacks.",
                "Relationship interpretation is based on transformation metrics.",
            ],
        ),
    ]

    details = [
        f"Morphology class: {morphology_class}",
        f"Distance: {format_float(metrics.get('morphology_distance'))}",
        f"Similarity: {format_float(similarity)}",
        f"Mutation score: {format_float(mutation)}",
    ]

    cautions = []

    if not morphology_payload.get("success"):
        cautions.append("Morphology payload did not fully succeed; graph comparison may be incomplete.")

    return section("Morphological Interaction", summary, details, claims, cautions)


def build_communication_dynamics_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build communication dynamics section."""
    summary = build_communication_summary(metrics)

    claims = [
        claim(
            "Communication ease is estimated from structural similarity and warning load.",
            confidence.get("communication", {}),
            [
                f"Morphology similarity: {metrics.get('morphology_similarity', 0)}",
                f"Warning count: {metrics.get('warning_count', 0)}",
                f"Readiness: {metrics.get('shared_readiness', 'unknown')}",
            ],
        )
    ]

    details = [
        f"{name_a} and {name_b} may recognize each other more easily when similarity is high.",
        "Higher morphology distance suggests more translation effort.",
        "Warnings reduce the confidence of communication claims.",
    ]

    cautions = [
        "Communication dynamics are inferred from structural metrics, not from observed dialogue."
    ]

    return section("Communication Dynamics", summary, details, claims, cautions)


def build_complementarity_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build complementarity section."""
    summary = build_complementarity_summary(metrics)

    claims = [
        claim(
            "Complementarity is estimated from mutation score and morphology class.",
            confidence.get("complementarity", {}),
            [
                f"Mutation score: {metrics.get('mutation_score', 0)}",
                f"Morphology class: {metrics.get('morphology_class', 'n/a')}",
            ],
        )
    ]

    details = [
        "Low mutation suggests resonance and familiarity.",
        "Moderate mutation suggests learning potential.",
        "High mutation suggests transformative contrast.",
    ]

    cautions = [
        "Complementarity does not imply emotional compatibility by itself."
    ]

    return section("Complementarity", summary, details, claims, cautions)


def build_tension_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build tension section."""
    mutation = safe_float(metrics.get("mutation_score"))
    warnings = int(metrics.get("warning_count", 0) or 0)

    if mutation >= 0.70:
        summary = (
            f"{name_a} and {name_b} may generate strong contrast because the "
            "mutation score suggests substantial structural transformation."
        )
    elif mutation >= 0.35:
        summary = (
            f"{name_a} and {name_b} may experience manageable tension: enough "
            "difference for growth, but not necessarily destabilizing."
        )
    else:
        summary = (
            f"{name_a} and {name_b} show limited structural tension from the "
            "current mutation score."
        )

    claims = [
        claim(
            "Potential tension is estimated from mutation score and warnings.",
            confidence.get("tension", {}),
            [
                f"Mutation score: {mutation}",
                f"Warning count: {warnings}",
            ],
        )
    ]

    details = [
        f"Mutation score: {format_float(mutation)}",
        f"Warnings: {warnings}",
        f"Errors: {metrics.get('error_count', 0)}",
    ]

    cautions = []

    if warnings:
        cautions.append("Warnings may indicate missing source artifacts that affect tension interpretation.")

    return section("Tension Vectors", summary, details, claims, cautions)


def build_readiness_section(
    name_a: str,
    name_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build readiness section."""
    readiness = metrics.get("shared_readiness", "unknown")

    summary = (
        f"The relationship report readiness is currently marked as {readiness}. "
        "This label reflects whether profile reports, graph reports, warnings, "
        "and errors permit a strong interpretation."
    )

    claims = [
        claim(
            "Readiness summarizes whether the report should be trusted as complete, partial, or cautionary.",
            confidence.get("overall", {}),
            [
                f"Shared readiness: {readiness}",
                f"Profile A temporal: {metrics.get('profile_a_temporal')}",
                f"Profile B temporal: {metrics.get('profile_b_temporal')}",
                f"Error count: {metrics.get('error_count', 0)}",
            ],
        )
    ]

    details = [
        "ready = profile and morphology payloads are complete with low warning load.",
        "caution = core payloads exist but warnings are present.",
        "partial = morphology or graph output is incomplete.",
        "blocked = one or both profile reports failed.",
    ]

    cautions = []

    if readiness != "ready":
        cautions.append("Relationship report should be read as provisional until missing inputs are resolved.")

    return section("Relationship Readiness", summary, details, claims, cautions)


def build_research_cautions_section(
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build research cautions."""
    details = build_caution_details(
        profile_report_a,
        profile_report_b,
        morphology_payload,
    )

    summary = (
        "This relationship interpretation is deterministic and should be read "
        "as a synthesis of existing Atlas service outputs, not as an independent "
        "symbolic engine or unconstrained narrative."
    )

    claims = [
        claim(
            "The report preserves source-layer cautions.",
            confidence.get("overall", {}),
            details,
        )
    ]

    return section("Research Cautions", summary, details, claims, details)


def build_relationship_confidence(
    *,
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
    warnings: list[str],
    errors: list[Any],
) -> dict[str, Any]:
    """Build deterministic confidence model for relationship interpretation."""
    metrics_a = profile_report_a.get("metrics", {})
    metrics_b = profile_report_b.get("metrics", {})
    morphology_metrics = morphology_payload.get("metrics", {})

    profile_score = confidence_from_booleans(
        [
            profile_report_a.get("success", False),
            profile_report_b.get("success", False),
            metrics_a.get("has_temporal", False),
            metrics_b.get("has_temporal", False),
            metrics_a.get("has_graph", False),
            metrics_b.get("has_graph", False),
        ]
    )

    morphology_score = confidence_from_morphology(
        morphology_payload,
        morphology_metrics,
    )

    communication_score = clamp((profile_score * 0.55) + (morphology_score * 0.45))
    complementarity_score = morphology_score
    tension_score = clamp((morphology_score * 0.70) + (profile_score * 0.30))

    warning_penalty = min(len(warnings) * 0.04, 0.24)
    error_penalty = min(len(errors) * 0.10, 0.40)

    overall_score = clamp(
        profile_score * 0.35
        + morphology_score * 0.35
        + communication_score * 0.15
        + max(0.0, 1.0 - warning_penalty - error_penalty) * 0.15
    )

    return {
        "profile_readiness": confidence_record(profile_score),
        "morphology": confidence_record(morphology_score),
        "communication": confidence_record(communication_score),
        "complementarity": confidence_record(complementarity_score),
        "tension": confidence_record(tension_score),
        "warnings": {
            "count": len(warnings),
            "penalty": warning_penalty,
        },
        "errors": {
            "count": len(errors),
            "penalty": error_penalty,
        },
        "overall": confidence_record(overall_score),
    }


def confidence_from_booleans(values: list[bool]) -> float:
    """Build confidence from booleans."""
    if not values:
        return 0.0

    return sum(1 for value in values if value) / len(values)


def confidence_from_morphology(
    morphology_payload: dict[str, Any],
    morphology_metrics: dict[str, Any],
) -> float:
    """Build confidence from morphology availability."""
    if not morphology_payload.get("success"):
        return 0.25

    score = 0.50

    if morphology_metrics.get("morphology_class") not in {"", None, "n/a"}:
        score += 0.20

    if "similarity" in morphology_metrics:
        score += 0.10

    if "mutation_score" in morphology_metrics:
        score += 0.10

    if "distance" in morphology_metrics:
        score += 0.10

    return clamp(score)


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Convert confidence score to label."""
    if score >= 0.85:
        return "high"

    if score >= 0.65:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def base_relationship_metrics(
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build base relationship metrics."""
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


def build_relationship_metrics(
    *,
    profile_report_a: dict[str, Any],
    profile_report_b: dict[str, Any],
    morphology_payload: dict[str, Any],
    confidence: dict[str, Any],
    structured: dict[str, Any],
    warnings: list[str],
    errors: list[Any],
) -> dict[str, Any]:
    """Build final relationship metrics."""
    base = base_relationship_metrics(
        profile_report_a,
        profile_report_b,
        morphology_payload,
    )

    base.update(
        {
            "section_count": len(structured.get("sections", [])),
            "claim_count": count_claims(structured.get("sections", [])),
            "evidence_count": count_evidence(structured.get("sections", [])),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "overall_confidence": confidence.get("overall", {}),
        }
    )

    return base


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


def build_communication_summary(metrics: dict[str, Any]) -> str:
    """Build communication summary from morphology metrics."""
    similarity = safe_float(metrics.get("morphology_similarity"))

    if similarity >= 0.75:
        return "The profiles appear structurally familiar to each other, suggesting easier recognition patterns and faster mutual translation."

    if similarity >= 0.45:
        return "The profiles show partial structural overlap, suggesting both recognition and meaningful difference."

    return "The profiles appear structurally distant or under-resolved, suggesting the interaction may require deliberate translation and patience."


def build_complementarity_summary(metrics: dict[str, Any]) -> str:
    """Build complementarity summary from mutation score."""
    mutation = safe_float(metrics.get("mutation_score"))

    if mutation >= 0.70:
        return "The relationship may carry strong contrast and transformative pressure."

    if mutation >= 0.35:
        return "The relationship may combine familiarity with enough difference to create learning and adaptation."

    return "The relationship currently appears structurally close or under-resolved, emphasizing resonance or limited contrast more than dramatic transformation."


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
        "version": payload.get("version"),
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


def render_relationship_markdown(structured: dict[str, Any]) -> str:
    """Render relationship report as Markdown."""
    name_a = structured.get("profile_a", "Profile A")
    name_b = structured.get("profile_b", "Profile B")

    lines = [
        f"# Atlas Relationship Intelligence: {name_a} ↔ {name_b}",
        "",
        f"**Version:** {structured.get('version', RELATIONSHIP_REPORT_VERSION)}",
        "",
        "## Confidence",
    ]

    confidence = structured.get("confidence", {})

    for key in [
        "profile_readiness",
        "morphology",
        "communication",
        "complementarity",
        "tension",
        "overall",
    ]:
        record = confidence.get(key, {})
        lines.append(
            f"- {key.replace('_', ' ').title()}: "
            f"{record.get('label', 'unknown')} "
            f"({record.get('percent', 0)}%)"
        )

    lines.append("")

    for item in structured.get("sections", []):
        lines.append(f"## {item.get('title', 'Untitled Section')}")
        lines.append(item.get("summary", ""))

        details = item.get("details", [])
        if details:
            lines.append("")
            lines.append("### Details")
            for detail in details:
                lines.append(f"- {detail}")

        claims = item.get("claims", [])
        if claims:
            lines.append("")
            lines.append("### Claims")
            for item_claim in claims:
                confidence_record_value = item_claim.get("confidence", {})
                lines.append(
                    f"- {item_claim.get('claim', '')} "
                    f"[{confidence_record_value.get('label', 'unknown')}, "
                    f"{confidence_record_value.get('percent', 0)}%]"
                )

                for evidence_item in item_claim.get("evidence", []):
                    lines.append(f"  - Evidence: {evidence_item}")

        cautions = item.get("cautions", [])
        if cautions:
            lines.append("")
            lines.append("### Cautions")
            for caution in cautions:
                lines.append(f"- {caution}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def section(
    title: str,
    summary: str,
    details: list[str],
    claims: list[dict[str, Any]],
    cautions: list[str],
) -> dict[str, Any]:
    """Build relationship section."""
    return {
        "title": title,
        "summary": summary,
        "details": details,
        "claims": claims,
        "cautions": cautions,
    }


def claim(
    text: str,
    confidence: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build evidence-backed claim."""
    return {
        "claim": text,
        "confidence": confidence,
        "evidence": evidence,
    }


def count_claims(sections: list[dict[str, Any]]) -> int:
    """Count claims."""
    return sum(len(section_item.get("claims", [])) for section_item in sections)


def count_evidence(sections: list[dict[str, Any]]) -> int:
    """Count evidence items."""
    return sum(
        len(claim_item.get("evidence", []))
        for section_item in sections
        for claim_item in section_item.get("claims", [])
    )


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
        "version": RELATIONSHIP_REPORT_VERSION,
        "errors": [message],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {},
    }


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_float(value: Any) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def relationship_json_export(data: Any) -> str:
    """Serialize relationship data."""
    return json.dumps(data, indent=2, sort_keys=True)


# Backward-compatible export name.
json_export_relationship = relationship_json_export