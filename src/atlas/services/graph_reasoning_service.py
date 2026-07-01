"""Graph Reasoning service.

Adds deterministic reasoning over Atlas graph service outputs.

This service does not introduce new graph algorithms into the kernel.
It interprets existing identity stack and morphology outputs into:
- structural claims
- evidence
- confidence
- cautions
- reasoning summaries
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_service import (
    build_identity_stack_payload,
    build_morphology_payload,
)


GRAPH_REASONING_VERSION = "1.0"


def list_graph_reasoning_profiles() -> list[str]:
    """Return profiles available for graph reasoning."""
    return list_saved_profiles()


def build_profile_graph_reasoning_payload(profile_key: str) -> dict[str, Any]:
    """Build graph reasoning payload for one profile."""
    stack_payload = build_identity_stack_payload(profile_key)

    if not stack_payload.get("success"):
        return failure_payload(
            scope="profile",
            errors=stack_payload.get("errors", []),
            warnings=stack_payload.get("warnings", []),
        )

    reasoning = build_profile_graph_reasoning(profile_key, stack_payload)

    return {
        "success": True,
        "version": GRAPH_REASONING_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "errors": stack_payload.get("errors", []),
        "warnings": stack_payload.get("warnings", []),
        "data": {
            "reasoning": reasoning,
            "source_summary": summarize_source_payload(stack_payload),
        },
        "exports": {
            "reasoning_json": reasoning,
            "markdown": render_reasoning_markdown(reasoning),
        },
        "metrics": build_reasoning_metrics(reasoning, stack_payload),
    }


def build_relationship_graph_reasoning_payload(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Build graph reasoning payload for a morphology comparison."""
    morphology_payload = build_morphology_payload(profile_a, profile_b)

    if not morphology_payload.get("success"):
        return failure_payload(
            scope="relationship",
            errors=morphology_payload.get("errors", []),
            warnings=morphology_payload.get("warnings", []),
        )

    reasoning = build_relationship_graph_reasoning(
        profile_a,
        profile_b,
        morphology_payload,
    )

    return {
        "success": True,
        "version": GRAPH_REASONING_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": morphology_payload.get("errors", []),
        "warnings": morphology_payload.get("warnings", []),
        "data": {
            "reasoning": reasoning,
            "source_summary": summarize_source_payload(morphology_payload),
        },
        "exports": {
            "reasoning_json": reasoning,
            "markdown": render_reasoning_markdown(reasoning),
        },
        "metrics": build_reasoning_metrics(reasoning, morphology_payload),
    }


def build_profile_graph_reasoning(
    profile_key: str,
    stack_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic reasoning from identity stack metrics."""
    metrics = stack_payload.get("metrics", {})
    stack_data = stack_payload.get("data", {}).get("stack_data", {})
    summary = stack_data.get("summary", {})

    confidence = build_profile_graph_confidence(metrics)

    sections = [
        build_graph_overview_section(profile_key, metrics, summary, confidence),
        build_structure_density_section(profile_key, metrics, summary, confidence),
        build_topology_reasoning_section(profile_key, metrics, summary, confidence),
        build_resonance_reasoning_section(profile_key, metrics, summary, confidence),
        build_motif_reasoning_section(profile_key, metrics, summary, confidence),
        build_graph_cautions_section(profile_key, metrics, summary, confidence),
    ]

    return {
        "version": GRAPH_REASONING_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "overall_confidence": confidence.get("overall", {}),
            "topology_class": metrics.get("topology_class", "n/a"),
            "resonance_class": metrics.get("resonance_class", "n/a"),
            "dominant_motif": metrics.get("dominant_motif", "n/a"),
        },
    }


def build_relationship_graph_reasoning(
    profile_a: str,
    profile_b: str,
    morphology_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic reasoning from morphology metrics."""
    metrics = morphology_payload.get("metrics", {})
    confidence = build_relationship_graph_confidence(metrics, morphology_payload)

    sections = [
        build_morphology_overview_section(profile_a, profile_b, metrics, confidence),
        build_similarity_reasoning_section(profile_a, profile_b, metrics, confidence),
        build_mutation_reasoning_section(profile_a, profile_b, metrics, confidence),
        build_overlap_reasoning_section(profile_a, profile_b, metrics, confidence),
        build_relationship_graph_cautions_section(profile_a, profile_b, metrics, confidence),
    ]

    return {
        "version": GRAPH_REASONING_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "overall_confidence": confidence.get("overall", {}),
            "morphology_class": metrics.get("morphology_class", "n/a"),
            "similarity": metrics.get("similarity", 0),
            "distance": metrics.get("distance", 0),
            "mutation_score": metrics.get("mutation_score", 0),
        },
    }


def build_graph_overview_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build graph overview reasoning."""
    name = metrics.get("name", profile_key)

    summary_text = (
        f"{name}'s graph stack is represented through raw identity structure, "
        "truth-filtered structure, motif summary, topology classification, "
        "and resonance classification."
    )

    details = [
        f"Raw nodes: {metrics.get('cig_nodes', 0)}",
        f"Raw edges: {metrics.get('cig_edges', 0)}",
        f"Truth nodes: {metrics.get('stg_nodes', 0)}",
        f"Truth edges: {metrics.get('stg_edges', 0)}",
        f"Audit status: {metrics.get('audit_status', 'unknown')}",
    ]

    claims = [
        claim(
            "The graph stack is available for profile-level reasoning.",
            confidence.get("structure", {}),
            details,
        )
    ]

    cautions = []
    if metrics.get("audit_status") == "warning":
        cautions.append("Graph audit status is warning; conclusions should remain evidence-bounded.")

    return section("Graph Overview", summary_text, details, claims, cautions)


def build_structure_density_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build structure density reasoning."""
    raw_nodes = safe_float(metrics.get("cig_nodes"))
    raw_edges = safe_float(metrics.get("cig_edges"))
    truth_nodes = safe_float(metrics.get("stg_nodes"))
    truth_edges = safe_float(metrics.get("stg_edges"))

    raw_density = safe_ratio(raw_edges, max(raw_nodes, 1))
    truth_density = safe_ratio(truth_edges, max(truth_nodes, 1))

    if raw_density >= 3:
        summary_text = "The raw identity graph appears highly connected, suggesting dense symbolic association."
    elif raw_density >= 1:
        summary_text = "The raw identity graph appears moderately connected, suggesting usable symbolic structure."
    else:
        summary_text = "The raw identity graph appears sparse, so structural claims should remain conservative."

    details = [
        f"Raw node/edge ratio: {round(raw_density, 4)}",
        f"Truth node/edge ratio: {round(truth_density, 4)}",
        f"Raw node count: {int(raw_nodes)}",
        f"Raw edge count: {int(raw_edges)}",
        f"Truth node count: {int(truth_nodes)}",
        f"Truth edge count: {int(truth_edges)}",
    ]

    claims = [
        claim(
            "Graph density can support reasoning about symbolic connectedness.",
            confidence.get("structure", {}),
            details,
        )
    ]

    return section("Structure Density", summary_text, details, claims, [])


def build_topology_reasoning_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build topology reasoning."""
    topology_class = metrics.get("topology_class", "n/a")
    dominant_axis = metrics.get("dominant_topology_axis", "n/a")

    summary_text = (
        f"The graph topology is classified as {topology_class}, with "
        f"{dominant_axis} identified as the dominant topology axis."
    )

    details = [
        f"Topology class: {topology_class}",
        f"Dominant topology axis: {dominant_axis}",
        f"Motif richness: {metrics.get('motif_count', 0)}",
    ]

    claims = [
        claim(
            "Topology classification provides a profile-level structural signature.",
            confidence.get("topology", {}),
            details,
        )
    ]

    cautions = []
    if topology_class in {"n/a", "", None}:
        cautions.append("Topology class is unavailable.")

    return section("Topology Reasoning", summary_text, details, claims, cautions)


def build_resonance_reasoning_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build resonance reasoning."""
    resonance_class = metrics.get("resonance_class", "n/a")
    dominant_axis = metrics.get("dominant_resonance_axis", "n/a")

    summary_text = (
        f"The resonance layer is classified as {resonance_class}, with "
        f"{dominant_axis} identified as the dominant resonance axis."
    )

    details = [
        f"Resonance class: {resonance_class}",
        f"Dominant resonance axis: {dominant_axis}",
    ]

    claims = [
        claim(
            "Resonance classification provides a profile-level activation signature.",
            confidence.get("resonance", {}),
            details,
        )
    ]

    cautions = []
    if resonance_class in {"n/a", "", None}:
        cautions.append("Resonance class is unavailable.")

    return section("Resonance Reasoning", summary_text, details, claims, cautions)


def build_motif_reasoning_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build motif reasoning."""
    dominant_motif = metrics.get("dominant_motif", "n/a")
    motif_richness = metrics.get("motif_count", 0)

    summary_text = (
        f"The dominant motif is {dominant_motif}, with motif richness "
        f"reported as {motif_richness}."
    )

    details = [
        f"Dominant motif: {dominant_motif}",
        f"Motif richness: {motif_richness}",
    ]

    claims = [
        claim(
            "Dominant motif gives a compact description of graph organization.",
            confidence.get("motif", {}),
            details,
        )
    ]

    return section("Motif Reasoning", summary_text, details, claims, [])


def build_graph_cautions_section(
    profile_key: str,
    metrics: dict[str, Any],
    summary: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build graph caution section."""
    cautions = []

    if metrics.get("audit_status") == "warning":
        cautions.append("Audit status is warning.")

    if safe_float(metrics.get("stg_nodes")) == 0:
        cautions.append("Truth graph has zero nodes.")

    if safe_float(metrics.get("stg_edges")) == 0:
        cautions.append("Truth graph has zero edges.")

    if not cautions:
        cautions.append("No major graph reasoning cautions were surfaced.")

    summary_text = "Graph reasoning should preserve structural limits and audit boundaries."

    claims = [
        claim(
            "Graph reasoning confidence depends on graph richness and audit quality.",
            confidence.get("overall", {}),
            cautions,
        )
    ]

    return section("Graph Reasoning Cautions", summary_text, cautions, claims, cautions)


def build_morphology_overview_section(
    profile_a: str,
    profile_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build morphology overview."""
    morphology_class = metrics.get("morphology_class", "n/a")

    summary_text = (
        f"The graph transformation from {profile_a} to {profile_b} is classified "
        f"as {morphology_class}."
    )

    details = [
        f"Morphology class: {morphology_class}",
        f"Distance: {metrics.get('distance', 0)}",
        f"Similarity: {metrics.get('similarity', 0)}",
        f"Mutation score: {metrics.get('mutation_score', 0)}",
    ]

    claims = [
        claim(
            "Morphology comparison is available for relationship-level graph reasoning.",
            confidence.get("morphology", {}),
            details,
        )
    ]

    return section("Morphology Overview", summary_text, details, claims, [])


def build_similarity_reasoning_section(
    profile_a: str,
    profile_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build similarity reasoning."""
    similarity = safe_float(metrics.get("similarity"))
    node_overlap = safe_float(metrics.get("node_overlap"))
    edge_overlap = safe_float(metrics.get("edge_overlap"))

    if similarity >= 0.70:
        summary_text = "The profiles show high graph similarity."
    elif similarity >= 0.40:
        summary_text = "The profiles show moderate graph similarity."
    elif similarity > 0:
        summary_text = "The profiles show limited graph similarity."
    else:
        summary_text = "Graph similarity is unavailable or zero."

    details = [
        f"Similarity: {round(similarity, 4)}",
        f"Node overlap: {round(node_overlap, 4)}",
        f"Edge overlap: {round(edge_overlap, 4)}",
        f"Shared nodes: {metrics.get('shared_node_count', 0)}",
        f"Shared edges: {metrics.get('shared_edge_count', 0)}",
    ]

    claims = [
        claim(
            "Similarity is driven by node overlap and edge overlap.",
            confidence.get("similarity", {}),
            details,
        )
    ]

    cautions = []
    if edge_overlap < 0.10:
        cautions.append("Edge overlap is low, so similarity should not be overstated.")

    return section("Similarity Reasoning", summary_text, details, claims, cautions)


def build_mutation_reasoning_section(
    profile_a: str,
    profile_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build mutation reasoning."""
    mutation = safe_float(metrics.get("mutation_score"))

    if mutation >= 0.70:
        summary_text = "The graph transformation shows strong mutation pressure."
    elif mutation >= 0.35:
        summary_text = "The graph transformation shows moderate mutation pressure."
    elif mutation > 0:
        summary_text = "The graph transformation shows limited mutation pressure."
    else:
        summary_text = "Mutation score is unavailable or zero."

    details = [
        f"Mutation score: {round(mutation, 4)}",
        f"Motif mutation: {metrics.get('motif_mutation', 0)}",
        f"Genome mutation: {metrics.get('genome_mutation', 0)}",
        f"Topology mutation: {metrics.get('topology_mutation', 0)}",
        f"Resonance mutation: {metrics.get('resonance_mutation', 0)}",
    ]

    claims = [
        claim(
            "Mutation score combines motif, genome, topology, and resonance changes.",
            confidence.get("mutation", {}),
            details,
        )
    ]

    return section("Mutation Reasoning", summary_text, details, claims, [])


def build_overlap_reasoning_section(
    profile_a: str,
    profile_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build overlap reasoning."""
    shared_nodes = metrics.get("shared_node_count", 0)
    shared_edges = metrics.get("shared_edge_count", 0)

    summary_text = (
        f"The profiles share {shared_nodes} nodes and {shared_edges} edges. "
        "Shared nodes indicate common structural vocabulary; shared edges indicate "
        "common relational structure."
    )

    details = [
        f"Shared nodes: {shared_nodes}",
        f"Shared edges: {shared_edges}",
        f"Added nodes: {metrics.get('added_node_count', 0)}",
        f"Removed nodes: {metrics.get('removed_node_count', 0)}",
        f"Added edges: {metrics.get('added_edge_count', 0)}",
        f"Removed edges: {metrics.get('removed_edge_count', 0)}",
    ]

    claims = [
        claim(
            "Node overlap and edge overlap describe different types of similarity.",
            confidence.get("overlap", {}),
            details,
        )
    ]

    return section("Overlap Reasoning", summary_text, details, claims, [])


def build_relationship_graph_cautions_section(
    profile_a: str,
    profile_b: str,
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build relationship graph cautions."""
    cautions = []

    if safe_float(metrics.get("edge_overlap")) < 0.10:
        cautions.append("Edge overlap is low.")

    if safe_float(metrics.get("similarity")) < 0.40:
        cautions.append("Overall similarity is limited.")

    if safe_float(metrics.get("mutation_score")) < 0.20:
        cautions.append("Mutation score is low and may indicate limited transformation or under-resolution.")

    if not cautions:
        cautions.append("No major morphology cautions were surfaced.")

    summary_text = "Relationship graph reasoning should preserve morphology limits."

    claims = [
        claim(
            "Relationship graph reasoning confidence depends on similarity, overlap, mutation, and edit distance.",
            confidence.get("overall", {}),
            cautions,
        )
    ]

    return section("Relationship Graph Cautions", summary_text, cautions, claims, cautions)


def build_profile_graph_confidence(metrics: dict[str, Any]) -> dict[str, Any]:
    """Build confidence for profile graph reasoning."""
    structure_score = 0.0

    if safe_float(metrics.get("cig_nodes")) > 0:
        structure_score += 0.25

    if safe_float(metrics.get("cig_edges")) > 0:
        structure_score += 0.25

    if safe_float(metrics.get("stg_nodes")) > 0:
        structure_score += 0.20

    if safe_float(metrics.get("stg_edges")) > 0:
        structure_score += 0.20

    if metrics.get("audit_status") in {"passed", "warning"}:
        structure_score += 0.10

    structure_score = clamp(structure_score)

    topology_score = 0.75 if metrics.get("topology_class") not in {"", None, "n/a"} else 0.25
    resonance_score = 0.75 if metrics.get("resonance_class") not in {"", None, "n/a"} else 0.25
    motif_score = 0.75 if metrics.get("dominant_motif") not in {"", None, "n/a"} else 0.25

    overall_score = clamp(
        structure_score * 0.45
        + topology_score * 0.20
        + resonance_score * 0.20
        + motif_score * 0.15
    )

    return {
        "structure": confidence_record(structure_score),
        "topology": confidence_record(topology_score),
        "resonance": confidence_record(resonance_score),
        "motif": confidence_record(motif_score),
        "overall": confidence_record(overall_score),
    }


def build_relationship_graph_confidence(
    metrics: dict[str, Any],
    morphology_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build confidence for relationship graph reasoning."""
    morphology_score = 0.25

    if morphology_payload.get("success"):
        morphology_score += 0.20

    if metrics.get("morphology_class") not in {"", None, "n/a"}:
        morphology_score += 0.15

    similarity = safe_float(metrics.get("similarity"))
    node_overlap = safe_float(metrics.get("node_overlap"))
    edge_overlap = safe_float(metrics.get("edge_overlap"))
    mutation = safe_float(metrics.get("mutation_score"))
    distance = safe_float(metrics.get("distance"))

    similarity_score = clamp(
        min(similarity, 1.0) * 0.40
        + min(node_overlap, 1.0) * 0.35
        + min(edge_overlap, 1.0) * 0.25
    )

    mutation_score = clamp(
        min(mutation, 1.0) * 0.45
        + min(distance, 1.0) * 0.35
        + min(edge_overlap, 1.0) * 0.20
    )

    overlap_score = clamp(
        min(node_overlap, 1.0) * 0.55
        + min(edge_overlap, 1.0) * 0.45
    )

    morphology_score = clamp(morphology_score)

    overall_score = clamp(
        morphology_score * 0.30
        + similarity_score * 0.25
        + mutation_score * 0.25
        + overlap_score * 0.20
    )

    return {
        "morphology": confidence_record(morphology_score),
        "similarity": confidence_record(similarity_score),
        "mutation": confidence_record(mutation_score),
        "overlap": confidence_record(overlap_score),
        "overall": confidence_record(overall_score),
    }


def build_reasoning_metrics(
    reasoning: dict[str, Any],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build reasoning metrics."""
    sections = reasoning.get("sections", [])
    markdown = render_reasoning_markdown(reasoning)

    return {
        "section_count": len(sections),
        "claim_count": count_claims(sections),
        "evidence_count": count_evidence(sections),
        "word_count": len(markdown.split()),
        "overall_confidence": reasoning.get("confidence", {}).get("overall", {}),
        "source_warnings": len(source_payload.get("warnings", [])),
        "source_errors": len(source_payload.get("errors", [])),
    }


def render_reasoning_markdown(reasoning: dict[str, Any]) -> str:
    """Render graph reasoning as Markdown."""
    title = "Atlas Graph Reasoning"

    if reasoning.get("scope") == "profile":
        title = f"Atlas Graph Reasoning: {reasoning.get('profile_key', 'Profile')}"

    if reasoning.get("scope") == "relationship":
        title = (
            f"Atlas Graph Reasoning: {reasoning.get('profile_a', 'Profile A')} "
            f"↔ {reasoning.get('profile_b', 'Profile B')}"
        )

    lines = [
        f"# {title}",
        "",
        f"**Version:** {reasoning.get('version', GRAPH_REASONING_VERSION)}",
        "",
        "## Confidence",
    ]

    for key, record in reasoning.get("confidence", {}).items():
        if isinstance(record, dict) and "percent" in record:
            lines.append(
                f"- {key.replace('_', ' ').title()}: "
                f"{record.get('label', 'unknown')} ({record.get('percent', 0)}%)"
            )

    lines.append("")

    for item in reasoning.get("sections", []):
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
                confidence = item_claim.get("confidence", {})
                lines.append(
                    f"- {item_claim.get('claim', '')} "
                    f"[{confidence.get('label', 'unknown')}, "
                    f"{confidence.get('percent', 0)}%]"
                )
                for evidence in item_claim.get("evidence", []):
                    lines.append(f"  - Evidence: {evidence}")

        cautions = item.get("cautions", [])
        if cautions:
            lines.append("")
            lines.append("### Cautions")
            for caution in cautions:
                lines.append(f"- {caution}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def summarize_source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe source summary."""
    return {
        "success": payload.get("success"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
    }


def section(
    title: str,
    summary: str,
    details: list[str],
    claims: list[dict[str, Any]],
    cautions: list[str],
) -> dict[str, Any]:
    """Build reasoning section."""
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
    return sum(len(section.get("claims", [])) for section in sections)


def count_evidence(sections: list[dict[str, Any]]) -> int:
    """Count evidence items."""
    return sum(
        len(claim_item.get("evidence", []))
        for section in sections
        for claim_item in section.get("claims", [])
    )


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Label confidence score."""
    if score >= 0.85:
        return "high"

    if score >= 0.65:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def safe_ratio(numerator: float, denominator: float) -> float:
    """Return safe ratio."""
    if denominator == 0:
        return 0.0

    return numerator / denominator


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
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
        "version": GRAPH_REASONING_VERSION,
        "scope": scope,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    """Serialize graph reasoning JSON."""
    return json.dumps(data, indent=2, sort_keys=True)