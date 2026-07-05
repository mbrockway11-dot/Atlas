
"""Atlas structural synthesis engine.

This module fuses classification, graph, topology, resonance, fingerprint,
semantic, and Vedic/temporal context into integrated human-readable synthesis.
"""

from __future__ import annotations

from typing import Any


STRUCTURAL_SYNTHESIS_VERSION = "1.0"


def build_structural_synthesis(payload: dict[str, Any]) -> dict[str, Any]:
    """Build integrated structural synthesis from canonical profile payload."""
    classification = safe_dict(payload.get("classification"))
    graph = safe_dict(payload.get("graph"))
    topology = safe_dict(payload.get("topology"))
    resonance = safe_dict(payload.get("resonance"))
    fingerprint = safe_dict(payload.get("fingerprint"))
    temporal = safe_dict(payload.get("temporal"))
    semantic = safe_dict(payload.get("semantic"))

    graph_summary = safe_dict(graph.get("summary"))
    topology_summary = safe_dict(topology.get("summary"))
    resonance_summary = safe_dict(resonance.get("summary"))
    fingerprint_summary = safe_dict(fingerprint.get("summary"))

    identity = safe_dict(payload.get("identity"))
    name = (
        identity.get("display_name")
        or identity.get("full_name")
        or identity.get("name")
        or payload.get("profile_key")
        or "This profile"
    )

    role = classification.get("structural_role", "Unclassified Structural Actor")
    subtype = classification.get("structural_subtype", "Unresolved Subtype")
    confidence = safe_dict(classification.get("confidence"))

    synthesis = {
        "success": True,
        "version": STRUCTURAL_SYNTHESIS_VERSION,
        "profile_key": payload.get("profile_key"),
        "name": name,
        "role": role,
        "subtype": subtype,
        "confidence": confidence,
        "executive_synthesis": build_executive_synthesis(
            name=name,
            role=role,
            subtype=subtype,
            confidence=confidence,
            classification=classification,
            graph_summary=graph_summary,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
            fingerprint_summary=fingerprint_summary,
        ),
        "mind_architecture": build_mind_architecture(
            role=role,
            classification=classification,
            graph_summary=graph_summary,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
            temporal=temporal,
        ),
        "decision_style": build_decision_style(
            role=role,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
        ),
        "relationship_dynamics": build_relationship_dynamics(
            role=role,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
        ),
        "career_expression": build_career_expression(
            role=role,
            classification=classification,
            fingerprint_summary=fingerprint_summary,
        ),
        "stress_pattern": build_stress_pattern(
            role=role,
            classification=classification,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
        ),
        "growth_strategy": build_growth_strategy(
            role=role,
            classification=classification,
            graph_summary=graph_summary,
            topology_summary=topology_summary,
        ),
        "evidence": build_evidence(
            classification=classification,
            graph_summary=graph_summary,
            topology_summary=topology_summary,
            resonance_summary=resonance_summary,
            fingerprint_summary=fingerprint_summary,
            semantic=semantic,
        ),
    }

    return synthesis


def build_executive_synthesis(
    *,
    name: str,
    role: str,
    subtype: str,
    confidence: dict[str, Any],
    classification: dict[str, Any],
    graph_summary: dict[str, Any],
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
    fingerprint_summary: dict[str, Any],
) -> str:
    """Build integrated executive synthesis."""
    confidence_text = format_confidence(confidence)

    topology_class = (
        graph_summary.get("topology_class")
        or topology_summary.get("topology_class")
        or fingerprint_summary.get("topology_class")
        or "unresolved topology"
    )
    dominant_axis = (
        graph_summary.get("dominant_topology_axis")
        or topology_summary.get("dominant_axis")
        or "unresolved axis"
    )
    dominant_motif = (
        graph_summary.get("dominant_motif")
        or fingerprint_summary.get("dominant_motif")
        or "unresolved motif"
    )
    resonance_class = (
        graph_summary.get("resonance_class")
        or resonance_summary.get("resonance_class")
        or fingerprint_summary.get("resonance_class")
        or "unresolved resonance"
    )

    raw_nodes = graph_summary.get("raw_node_count", 0)
    raw_edges = graph_summary.get("raw_edge_count", 0)
    truth_nodes = graph_summary.get("truth_node_count", 0)
    truth_edges = graph_summary.get("truth_edge_count", 0)
    motif_richness = graph_summary.get("motif_richness", 0)

    role_sentence = classification.get("civilization_function", "")

    return f"""
{name} is structurally classified by Atlas as a **{role}** with the subtype **{subtype}**. The current classification carries **{confidence_text}** confidence.

{role_sentence}

The Kamea-derived identity graph resolves into a **{topology_class}** topology organized primarily through **{dominant_axis}**. Its dominant motif is **{dominant_motif}**, while the resonance field resolves as **{resonance_class}**.

The graph generated **{raw_nodes} canonical identity nodes** and **{raw_edges} canonical structural relationships** before truth reduction. After deterministic reduction, Atlas preserved **{truth_nodes} truth nodes** and **{truth_edges} essential relationships**. Motif richness currently measures **{format_float(motif_richness)}**.

Taken together, these layers indicate that the profile should not be read as isolated traits. It is a structural pattern: a way that identity, cognition, timing, symbolic recurrence, and behavioral activation organize into a stable operating architecture.
""".strip()


def build_mind_architecture(
    *,
    role: str,
    classification: dict[str, Any],
    graph_summary: dict[str, Any],
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
    temporal: dict[str, Any],
) -> str:
    """Build mind architecture synthesis."""
    cognitive_style = classification.get("cognitive_style", "")
    topology_class = graph_summary.get("topology_class") or topology_summary.get("topology_class", "")
    motif_richness = float_or_zero(graph_summary.get("motif_richness"))
    axis = graph_summary.get("dominant_topology_axis") or topology_summary.get("dominant_axis", "")
    resonance_axis = graph_summary.get("dominant_resonance_axis") or resonance_summary.get("dominant_resonance_axis", "")

    role_frame = role_specific_mind_frame(role)

    motif_frame = (
        "High motif richness suggests the mind detects and reuses recurring structural forms across contexts."
        if motif_richness >= 0.65
        else "Moderate or focused motif richness suggests the mind specializes around a smaller set of recurring structural anchors."
    )

    temporal_note = ""
    if temporal.get("status") == "compiled":
        temporal_note = "The temporal layer is compiled, so timing, activation, and natal context are available as supporting behavioral context."

    return " ".join(
        part for part in [
            role_frame,
            cognitive_style,
            f"The topology class **{topology_class}** indicates how information organizes after graph reduction.",
            f"The dominant axis **{axis}** identifies the structural behavior that most strongly survives reduction.",
            f"The resonance axis **{resonance_axis}** describes how activation moves through the profile.",
            motif_frame,
            temporal_note,
        ]
        if part
    )


def build_decision_style(
    *,
    role: str,
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
) -> str:
    """Build decision-style synthesis."""
    topology_class = topology_summary.get("topology_class", "")
    axis = topology_summary.get("dominant_axis", "")
    resonance_class = resonance_summary.get("resonance_class", "")

    if role == "Cycle-Weaver":
        return (
            "Decision-making likely improves through iteration. This profile may need to revisit a pattern multiple times before the correct choice becomes obvious. "
            "The strongest decisions emerge when repeating signals are distinguished from emotional loops."
        )

    if role == "Persistence-Architect":
        return (
            "Decision-making likely favors continuity, structural durability, and long-range consequence. "
            "This profile may prefer choices that preserve useful systems rather than choices that create short-term novelty."
        )

    if role == "Pattern-Weaver":
        return (
            "Decision-making likely depends on recognizing relationships between signals. "
            "The risk is overconnecting data before identifying the essential pattern."
        )

    return (
        f"Decision-making should be interpreted through the current topology **{topology_class}**, dominant axis **{axis}**, and resonance class **{resonance_class}**."
    )


def build_relationship_dynamics(
    *,
    role: str,
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
) -> str:
    """Build relationship dynamics synthesis."""
    topology_class = topology_summary.get("topology_class", "")
    resonance_class = resonance_summary.get("resonance_class", "")

    if role == "Cycle-Weaver":
        return (
            "In relationships, this profile may notice repeated emotional, behavioral, or conversational loops quickly. "
            "It may be especially sensitive to patterns that return unresolved. Healthy relationship dynamics require naming the cycle without becoming trapped inside it."
        )

    if role == "Persistence-Architect":
        return (
            "In relationships, this profile tends to value continuity, reliability, and long-term structural trust. "
            "It may become strained when relational systems are unstable, inconsistent, or repeatedly rebuilt without integration."
        )

    return (
        f"Relationship dynamics are interpreted through **{topology_class}** topology and **{resonance_class}** resonance. "
        "This describes how connection, pressure, adaptation, and stability move through the profile."
    )


def build_career_expression(
    *,
    role: str,
    classification: dict[str, Any],
    fingerprint_summary: dict[str, Any],
) -> str:
    """Build career/contribution synthesis."""
    function = classification.get("civilization_function", "")
    motif = fingerprint_summary.get("dominant_motif", "unresolved motif")
    topology = fingerprint_summary.get("topology_class", "unresolved topology")

    return (
        f"The strongest contribution pattern is described by the role **{role}**. {function} "
        f"The structural fingerprint resolves through **{topology}** topology and a **{motif}** motif, suggesting that career expression is strongest when the environment rewards the profile's native structural behavior."
    )


def build_stress_pattern(
    *,
    role: str,
    classification: dict[str, Any],
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
) -> str:
    """Build stress synthesis."""
    role_stress = classification.get("stress_response", "")
    damping = resonance_summary.get("damping_pattern", "")
    stability = topology_summary.get("stability_pattern", "")

    return (
        f"{role_stress} "
        f"The resonance layer shows **{damping or 'unresolved damping'}**, while topology shows **{stability or 'unresolved stability'}**. "
        "Stress should be read as a change in graph behavior: where activation concentrates, where it dampens, and which structures become overloaded."
    ).strip()


def build_growth_strategy(
    *,
    role: str,
    classification: dict[str, Any],
    graph_summary: dict[str, Any],
    topology_summary: dict[str, Any],
) -> str:
    """Build growth strategy synthesis."""
    growth = classification.get("growth_path", "")
    motif_richness = float_or_zero(graph_summary.get("motif_richness"))
    axis = topology_summary.get("dominant_axis") or graph_summary.get("dominant_topology_axis", "")

    if role == "Cycle-Weaver":
        strategy = (
            "The key developmental task is distinguishing productive recurrence from repetitive entanglement. "
            "Cycles should become instruments of refinement, not traps."
        )
    elif role == "Persistence-Architect":
        strategy = (
            "The key developmental task is allowing durable systems to evolve. "
            "Persistence should preserve meaning without becoming rigidity."
        )
    else:
        strategy = (
            "The key developmental task is converting structural awareness into embodied, repeatable action."
        )

    return (
        f"{growth} {strategy} Motif richness is **{format_float(motif_richness)}**, and the dominant axis is **{axis}**, which indicates the structural behavior most relevant to growth."
    ).strip()


def build_evidence(
    *,
    classification: dict[str, Any],
    graph_summary: dict[str, Any],
    topology_summary: dict[str, Any],
    resonance_summary: dict[str, Any],
    fingerprint_summary: dict[str, Any],
    semantic: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build evidence records."""
    return [
        {
            "source": "classification",
            "claim": "Structural role and subtype were used as the primary synthesis frame.",
            "basis": classification,
        },
        {
            "source": "graph_summary",
            "claim": "Canonical and truth graph metrics support structural interpretation.",
            "basis": graph_summary,
        },
        {
            "source": "topology",
            "claim": "Topology explains organization after deterministic reduction.",
            "basis": topology_summary,
        },
        {
            "source": "resonance",
            "claim": "Resonance explains activation, damping, propagation, and stability.",
            "basis": resonance_summary,
        },
        {
            "source": "fingerprint",
            "claim": "Fingerprint preserves profile-level structural uniqueness.",
            "basis": fingerprint_summary,
        },
        {
            "source": "semantic",
            "claim": "Semantic intelligence provides human-domain interpretation.",
            "basis": {
                "success": semantic.get("success"),
                "confidence": semantic.get("confidence"),
                "domain_count": len(semantic.get("domains", []) or []),
            },
        },
    ]


def role_specific_mind_frame(role: str) -> str:
    """Return role-specific mind frame."""
    if role == "Cycle-Weaver":
        return (
            "The mind architecture is recursive and motif-sensitive. It is optimized for recognizing return-patterns, loops, repeated signals, and structures that transform through recurrence."
        )

    if role == "Persistence-Architect":
        return (
            "The mind architecture is continuity-oriented and structurally durable. It is optimized for preserving, refining, and extending complex systems across time."
        )

    if role == "Pattern-Weaver":
        return (
            "The mind architecture is associative and relational. It is optimized for discovering hidden links between concepts, symbols, and systems."
        )

    if role == "Connector-Architect":
        return (
            "The mind architecture is connective and systems-aware. It is optimized for linking separate structures into a coherent field."
        )

    return (
        "The mind architecture should be interpreted through the complete structural payload."
    )


def format_confidence(confidence: dict[str, Any]) -> str:
    """Format confidence object."""
    if not isinstance(confidence, dict):
        return "unknown"

    percent = confidence.get("percent")
    label = confidence.get("label", "")

    if percent is None:
        return str(label or "unknown")

    return f"{percent}% {label}".strip()


def format_float(value: Any) -> str:
    """Format numeric value."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "0.000"


def float_or_zero(value: Any) -> float:
    """Safely convert to float."""
    try:
        return float(value)
    except Exception:
        return 0.0


def safe_dict(value: Any) -> dict[str, Any]:
    """Return dict or empty dict."""
    return value if isinstance(value, dict) else {}

