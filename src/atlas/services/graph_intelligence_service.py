"""Graph Intelligence service.

Higher-level deterministic intelligence over graph reasoning outputs.

This service sits above:
- graph_service.py
- graph_reasoning_service.py

It does not mutate graph data or introduce new kernel algorithms.
It synthesizes graph reasoning into strategic intelligence:
- dominant structure
- structural strengths
- structural vulnerabilities
- intelligence summary
- action/research priorities
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_reasoning_service import (
    build_profile_graph_reasoning_payload,
    build_relationship_graph_reasoning_payload,
)


GRAPH_INTELLIGENCE_VERSION = "1.0"


def list_graph_intelligence_profiles() -> list[str]:
    """Return profiles available for graph intelligence."""
    return list_saved_profiles()


def build_profile_graph_intelligence_payload(profile_key: str) -> dict[str, Any]:
    """Build graph intelligence for one profile."""
    reasoning_payload = build_profile_graph_reasoning_payload(profile_key)

    if not reasoning_payload.get("success"):
        return failure_payload(
            scope="profile",
            errors=reasoning_payload.get("errors", []),
            warnings=reasoning_payload.get("warnings", []),
        )

    intelligence = build_profile_graph_intelligence(profile_key, reasoning_payload)

    return {
        "success": True,
        "version": GRAPH_INTELLIGENCE_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "errors": reasoning_payload.get("errors", []),
        "warnings": reasoning_payload.get("warnings", []),
        "data": {
            "intelligence": intelligence,
            "source_summary": summarize_source_payload(reasoning_payload),
        },
        "exports": {
            "intelligence_json": intelligence,
            "markdown": render_graph_intelligence_markdown(intelligence),
        },
        "metrics": build_graph_intelligence_metrics(intelligence, reasoning_payload),
    }


def build_relationship_graph_intelligence_payload(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Build graph intelligence for a relationship morphology comparison."""
    reasoning_payload = build_relationship_graph_reasoning_payload(
        profile_a,
        profile_b,
    )

    if not reasoning_payload.get("success"):
        return failure_payload(
            scope="relationship",
            errors=reasoning_payload.get("errors", []),
            warnings=reasoning_payload.get("warnings", []),
        )

    intelligence = build_relationship_graph_intelligence(
        profile_a,
        profile_b,
        reasoning_payload,
    )

    return {
        "success": True,
        "version": GRAPH_INTELLIGENCE_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": reasoning_payload.get("errors", []),
        "warnings": reasoning_payload.get("warnings", []),
        "data": {
            "intelligence": intelligence,
            "source_summary": summarize_source_payload(reasoning_payload),
        },
        "exports": {
            "intelligence_json": intelligence,
            "markdown": render_graph_intelligence_markdown(intelligence),
        },
        "metrics": build_graph_intelligence_metrics(intelligence, reasoning_payload),
    }


def build_profile_graph_intelligence(
    profile_key: str,
    reasoning_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build profile graph intelligence from graph reasoning."""
    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})
    reasoning_summary = reasoning.get("summary", {})
    confidence = build_intelligence_confidence(reasoning)

    topology_class = reasoning_summary.get("topology_class", "n/a")
    resonance_class = reasoning_summary.get("resonance_class", "n/a")
    dominant_motif = reasoning_summary.get("dominant_motif", "n/a")

    sections = [
        intelligence_section(
            title="Strategic Graph Summary",
            summary=(
                f"{profile_key} currently presents a {topology_class} topology, "
                f"{resonance_class} resonance, and {dominant_motif} dominant motif. "
                "This creates the profile's current graph intelligence signature."
            ),
            claims=[
                intelligence_claim(
                    "The profile has a coherent graph intelligence signature.",
                    confidence.get("overall", {}),
                    [
                        f"Topology class: {topology_class}",
                        f"Resonance class: {resonance_class}",
                        f"Dominant motif: {dominant_motif}",
                    ],
                )
            ],
            priorities=[
                "Use topology, resonance, and motif together rather than reading one metric alone."
            ],
            cautions=collect_reasoning_cautions(reasoning),
        ),
        intelligence_section(
            title="Structural Strengths",
            summary=resolve_profile_strength_summary(reasoning),
            claims=[
                intelligence_claim(
                    "Structural strengths are inferred from graph reasoning sections.",
                    confidence.get("strength", {}),
                    collect_section_summaries(reasoning),
                )
            ],
            priorities=[
                "Inspect dominant motif and topology axis for strongest identity pathways.",
                "Use Evidence Explorer when interpreting profile-level graph claims.",
            ],
            cautions=[],
        ),
        intelligence_section(
            title="Structural Vulnerabilities",
            summary=resolve_profile_vulnerability_summary(reasoning),
            claims=[
                intelligence_claim(
                    "Structural vulnerabilities are inferred from cautions and confidence limits.",
                    confidence.get("risk", {}),
                    collect_reasoning_cautions(reasoning),
                )
            ],
            priorities=[
                "Check audit status before strong topology claims.",
                "Prefer limited-confidence language when graph cautions are present.",
            ],
            cautions=collect_reasoning_cautions(reasoning),
        ),
        intelligence_section(
            title="Research Priorities",
            summary="The next research actions should focus on graph-richness, source evidence, and repeated motif validation.",
            claims=[
                intelligence_claim(
                    "Graph intelligence should drive research priorities, not absolute conclusions.",
                    confidence.get("overall", {}),
                    [
                        f"Reasoning sections: {reasoning_summary.get('section_count', 0)}",
                        f"Reasoning claims: {reasoning_summary.get('claim_count', 0)}",
                        f"Reasoning evidence: {reasoning_summary.get('evidence_count', 0)}",
                    ],
                )
            ],
            priorities=[
                "Compare this profile against nearest graph neighbors.",
                "Validate dominant motif across multiple profiles.",
                "Track whether topology class changes with future graph enrichment.",
            ],
            cautions=[],
        ),
    ]

    return {
        "version": GRAPH_INTELLIGENCE_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "priority_count": count_priorities(sections),
            "overall_confidence": confidence.get("overall", {}),
            "topology_class": topology_class,
            "resonance_class": resonance_class,
            "dominant_motif": dominant_motif,
        },
    }


def build_relationship_graph_intelligence(
    profile_a: str,
    profile_b: str,
    reasoning_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build relationship graph intelligence from morphology reasoning."""
    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})
    reasoning_summary = reasoning.get("summary", {})
    confidence = build_intelligence_confidence(reasoning)

    morphology_class = reasoning_summary.get("morphology_class", "n/a")
    similarity = safe_float(reasoning_summary.get("similarity"))
    distance = safe_float(reasoning_summary.get("distance"))
    mutation_score = safe_float(reasoning_summary.get("mutation_score"))

    sections = [
        intelligence_section(
            title="Strategic Relationship Summary",
            summary=(
                f"{profile_a} and {profile_b} show {morphology_class} morphology, "
                f"{round(similarity, 4)} similarity, {round(distance, 4)} distance, "
                f"and {round(mutation_score, 4)} mutation."
            ),
            claims=[
                intelligence_claim(
                    "The relationship has a measurable graph transformation signature.",
                    confidence.get("overall", {}),
                    [
                        f"Morphology class: {morphology_class}",
                        f"Similarity: {similarity}",
                        f"Distance: {distance}",
                        f"Mutation score: {mutation_score}",
                    ],
                )
            ],
            priorities=[
                "Read relationship graph intelligence as transformation, not compatibility."
            ],
            cautions=collect_reasoning_cautions(reasoning),
        ),
        intelligence_section(
            title="Alignment Potential",
            summary=resolve_relationship_alignment_summary(similarity),
            claims=[
                intelligence_claim(
                    "Alignment potential is primarily constrained by graph similarity and edge overlap.",
                    confidence.get("strength", {}),
                    collect_section_summaries(reasoning),
                )
            ],
            priorities=[
                "Review shared nodes and shared edges before making alignment claims.",
                "Treat node overlap and edge overlap as separate forms of similarity.",
            ],
            cautions=[],
        ),
        intelligence_section(
            title="Transformation Pressure",
            summary=resolve_relationship_transformation_summary(mutation_score, distance),
            claims=[
                intelligence_claim(
                    "Transformation pressure is inferred from mutation and structural edit distance.",
                    confidence.get("risk", {}),
                    [
                        f"Mutation score: {mutation_score}",
                        f"Distance: {distance}",
                        f"Morphology class: {morphology_class}",
                    ],
                )
            ],
            priorities=[
                "Inspect mutation layers to identify whether change comes from motif, genome, topology, or resonance.",
            ],
            cautions=collect_reasoning_cautions(reasoning),
        ),
        intelligence_section(
            title="Research Priorities",
            summary="Relationship graph intelligence should identify what to inspect next rather than forcing a single compatibility label.",
            claims=[
                intelligence_claim(
                    "Relationship interpretation should remain evidence-bounded.",
                    confidence.get("overall", {}),
                    [
                        f"Reasoning confidence: {confidence.get('overall', {}).get('percent', 0)}%",
                        f"Reasoning sections: {reasoning_summary.get('section_count', 0)}",
                        f"Reasoning evidence: {reasoning_summary.get('evidence_count', 0)}",
                    ],
                )
            ],
            priorities=[
                "Compare this pair against other historical inventor/scientist pairs.",
                "Identify which shared nodes are meaningful versus generic.",
                "Look for whether low edge overlap persists across similar profiles.",
            ],
            cautions=collect_reasoning_cautions(reasoning),
        ),
    ]

    return {
        "version": GRAPH_INTELLIGENCE_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "priority_count": count_priorities(sections),
            "overall_confidence": confidence.get("overall", {}),
            "morphology_class": morphology_class,
            "similarity": similarity,
            "distance": distance,
            "mutation_score": mutation_score,
        },
    }


def build_intelligence_confidence(reasoning: dict[str, Any]) -> dict[str, Any]:
    """Build graph intelligence confidence from graph reasoning confidence."""
    reasoning_confidence = reasoning.get("confidence", {})
    overall = reasoning_confidence.get("overall", {})
    overall_score = safe_float(overall.get("score"))

    caution_count = len(collect_reasoning_cautions(reasoning))
    caution_penalty = min(caution_count * 0.04, 0.20)

    strength_score = clamp(overall_score - caution_penalty * 0.40)
    risk_score = clamp(overall_score - caution_penalty * 0.20)
    priority_score = clamp(overall_score)

    adjusted_overall = clamp(
        strength_score * 0.35
        + risk_score * 0.25
        + priority_score * 0.25
        + max(0.0, 1.0 - caution_penalty) * 0.15
    )

    return {
        "strength": confidence_record(strength_score),
        "risk": confidence_record(risk_score),
        "priority": confidence_record(priority_score),
        "cautions": {
            "count": caution_count,
            "penalty": round(caution_penalty, 4),
        },
        "overall": confidence_record(adjusted_overall),
    }


def resolve_profile_strength_summary(reasoning: dict[str, Any]) -> str:
    """Resolve profile strength summary."""
    summary = reasoning.get("summary", {})
    topology = summary.get("topology_class", "n/a")
    resonance = summary.get("resonance_class", "n/a")
    motif = summary.get("dominant_motif", "n/a")

    return (
        f"The strongest graph intelligence signal is the combined pattern of "
        f"{topology} topology, {resonance} resonance, and {motif} motif."
    )


def resolve_profile_vulnerability_summary(reasoning: dict[str, Any]) -> str:
    """Resolve profile vulnerability summary."""
    cautions = collect_reasoning_cautions(reasoning)

    if not cautions:
        return "No major graph intelligence vulnerabilities were surfaced by the reasoning layer."

    return "Graph intelligence vulnerabilities are concentrated in the reported reasoning cautions."


def resolve_relationship_alignment_summary(similarity: float) -> str:
    """Resolve relationship alignment summary."""
    if similarity >= 0.70:
        return "The pair shows strong graph alignment."
    if similarity >= 0.40:
        return "The pair shows moderate graph alignment."
    if similarity > 0:
        return "The pair shows limited graph alignment."
    return "Graph alignment is unavailable or zero."


def resolve_relationship_transformation_summary(
    mutation_score: float,
    distance: float,
) -> str:
    """Resolve relationship transformation summary."""
    if mutation_score >= 0.70 or distance >= 0.70:
        return "The relationship shows strong transformation pressure."
    if mutation_score >= 0.35 or distance >= 0.35:
        return "The relationship shows moderate transformation pressure."
    if mutation_score > 0 or distance > 0:
        return "The relationship shows limited transformation pressure."
    return "Transformation pressure is unavailable or zero."


def collect_section_summaries(reasoning: dict[str, Any]) -> list[str]:
    """Collect section summaries as evidence."""
    summaries = []

    for item in reasoning.get("sections", []):
        title = item.get("title", "Untitled Section")
        summary = item.get("summary", "")
        if summary:
            summaries.append(f"{title}: {summary}")

    return summaries


def collect_reasoning_cautions(reasoning: dict[str, Any]) -> list[str]:
    """Collect cautions from reasoning sections."""
    cautions = []

    for item in reasoning.get("sections", []):
        for caution in item.get("cautions", []):
            if caution not in cautions:
                cautions.append(caution)

    return cautions


def build_graph_intelligence_metrics(
    intelligence: dict[str, Any],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build graph intelligence metrics."""
    sections = intelligence.get("sections", [])
    markdown = render_graph_intelligence_markdown(intelligence)

    return {
        "section_count": len(sections),
        "claim_count": count_claims(sections),
        "evidence_count": count_evidence(sections),
        "priority_count": count_priorities(sections),
        "word_count": len(markdown.split()),
        "overall_confidence": intelligence.get("confidence", {}).get("overall", {}),
        "source_warnings": len(source_payload.get("warnings", [])),
        "source_errors": len(source_payload.get("errors", [])),
    }


def render_graph_intelligence_markdown(intelligence: dict[str, Any]) -> str:
    """Render graph intelligence Markdown."""
    if intelligence.get("scope") == "profile":
        title = f"Atlas Graph Intelligence: {intelligence.get('profile_key', 'Profile')}"
    else:
        title = (
            f"Atlas Graph Intelligence: {intelligence.get('profile_a', 'Profile A')} "
            f"↔ {intelligence.get('profile_b', 'Profile B')}"
        )

    lines = [
        f"# {title}",
        "",
        f"**Version:** {intelligence.get('version', GRAPH_INTELLIGENCE_VERSION)}",
        "",
        "## Confidence",
    ]

    for key, record in intelligence.get("confidence", {}).items():
        if isinstance(record, dict) and "percent" in record:
            lines.append(
                f"- {key.title()}: {record.get('label', 'unknown')} "
                f"({record.get('percent', 0)}%)"
            )

    lines.append("")

    for item in intelligence.get("sections", []):
        lines.append(f"## {item.get('title', 'Untitled Section')}")
        lines.append(item.get("summary", ""))

        claims = item.get("claims", [])
        if claims:
            lines.append("")
            lines.append("### Claims")
            for claim_item in claims:
                confidence = claim_item.get("confidence", {})
                lines.append(
                    f"- {claim_item.get('claim', '')} "
                    f"[{confidence.get('label', 'unknown')}, "
                    f"{confidence.get('percent', 0)}%]"
                )

                for evidence in claim_item.get("evidence", []):
                    lines.append(f"  - Evidence: {evidence}")

        priorities = item.get("priorities", [])
        if priorities:
            lines.append("")
            lines.append("### Research Priorities")
            for priority in priorities:
                lines.append(f"- {priority}")

        cautions = item.get("cautions", [])
        if cautions:
            lines.append("")
            lines.append("### Cautions")
            for caution in cautions:
                lines.append(f"- {caution}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def intelligence_section(
    *,
    title: str,
    summary: str,
    claims: list[dict[str, Any]],
    priorities: list[str],
    cautions: list[str],
) -> dict[str, Any]:
    """Build graph intelligence section."""
    return {
        "title": title,
        "summary": summary,
        "claims": claims,
        "priorities": priorities,
        "cautions": cautions,
    }


def intelligence_claim(
    text: str,
    confidence: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build graph intelligence claim."""
    return {
        "claim": text,
        "confidence": confidence,
        "evidence": evidence,
    }


def count_claims(sections: list[dict[str, Any]]) -> int:
    """Count claims."""
    return sum(len(section.get("claims", [])) for section in sections)


def count_evidence(sections: list[dict[str, Any]]) -> int:
    """Count evidence items."""
    return sum(
        len(claim.get("evidence", []))
        for section in sections
        for claim in section.get("claims", [])
    )


def count_priorities(sections: list[dict[str, Any]]) -> int:
    """Count priorities."""
    return sum(len(section.get("priorities", [])) for section in sections)


def summarize_source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe source summary."""
    return {
        "success": payload.get("success"),
        "version": payload.get("version"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
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


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def failure_payload(
    *,
    scope: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": GRAPH_INTELLIGENCE_VERSION,
        "scope": scope,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    """Serialize graph intelligence JSON."""
    return json.dumps(data, indent=2, sort_keys=True)