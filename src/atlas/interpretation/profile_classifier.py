"""Atlas profile classifier."""

from __future__ import annotations

from typing import Any

PROFILE_CLASSIFIER_VERSION = "2.0"


def classify_profile(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify profile from graph-native topology, resonance, and temporal evidence."""
    identity = payload.get("identity", {})
    graph = payload.get("graph", {}) if isinstance(payload.get("graph"), dict) else {}
    topology_payload = payload.get("topology", {}) if isinstance(payload.get("topology"), dict) else {}
    resonance_payload = payload.get("resonance", {}) if isinstance(payload.get("resonance"), dict) else {}
    metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
    temporal = payload.get("temporal", {}) if isinstance(payload.get("temporal"), dict) else {}
    notes = str(payload.get("notes", ""))

    summary = graph.get("summary", {}) if isinstance(graph.get("summary"), dict) else {}
    fingerprint_summary = (
        payload.get("fingerprint", {}).get("summary", {})
        if isinstance(payload.get("fingerprint"), dict)
        else {}
    )

    dominant_motif = (
        summary.get("dominant_motif")
        or topology_payload.get("dominant_motif")
        or fingerprint_summary.get("dominant_motif")
        or metrics.get("dominant_motif")
        or ""
    )

    topology_class = (
        summary.get("topology_class")
        or topology_payload.get("topology_class")
        or fingerprint_summary.get("topology_class")
        or metrics.get("topology_class")
        or ""
    )

    axis = (
        summary.get("dominant_topology_axis")
        or topology_payload.get("dominant_topology_axis")
        or metrics.get("dominant_topology_axis")
        or ""
    )

    resonance_class = (
        summary.get("resonance_class")
        or resonance_payload.get("resonance_class")
        or fingerprint_summary.get("resonance_class")
        or metrics.get("resonance_class")
        or ""
    )

    resonance_axis = (
        summary.get("dominant_resonance_axis")
        or resonance_payload.get("dominant_resonance_axis")
        or metrics.get("dominant_resonance_axis")
        or ""
    )

    motif_richness = float(summary.get("motif_richness") or 0)
    raw_node_count = int(summary.get("raw_node_count") or 0)
    raw_edge_count = int(summary.get("raw_edge_count") or 0)
    truth_node_count = int(summary.get("truth_node_count") or 0)
    truth_edge_count = int(summary.get("truth_edge_count") or 0)

    has_ephemeris = bool(
        metrics.get("has_ephemeris")
        or temporal.get("runtime", {}).get("natal", {}).get("ephemeris")
        or temporal.get("natal", {}).get("ephemeris")
    )

    role = infer_role(
        dominant_motif=str(dominant_motif).lower(),
        topology_class=str(topology_class).lower(),
        axis=str(axis).lower(),
        resonance_class=str(resonance_class).lower(),
        resonance_axis=str(resonance_axis).lower(),
        motif_richness=motif_richness,
        raw_node_count=raw_node_count,
        raw_edge_count=raw_edge_count,
        truth_node_count=truth_node_count,
        truth_edge_count=truth_edge_count,
        notes=notes.lower(),
        has_ephemeris=has_ephemeris,
    )

    subtype = infer_subtype(
        role=role,
        topology_class=str(topology_class).lower(),
        axis=str(axis).lower(),
        resonance_axis=str(resonance_axis).lower(),
        motif_richness=motif_richness,
        truth_edge_count=truth_edge_count,
    )

    semantic = semantic_for_role(role)

    confidence_score = score_confidence(
        role=role,
        topology_class=str(topology_class),
        dominant_motif=str(dominant_motif),
        raw_node_count=raw_node_count,
        raw_edge_count=raw_edge_count,
        has_ephemeris=has_ephemeris,
    )

    return {
        "success": True,
        "version": PROFILE_CLASSIFIER_VERSION,
        "profile_key": payload.get("profile_key") or identity.get("profile_key", ""),
        "name": identity.get("display_name") or identity.get("full_name") or identity.get("name") or "Unknown Profile",
        "structural_role": role,
        "structural_subtype": subtype,
        **semantic,
        "confidence": {
            "score": confidence_score,
            "percent": round(confidence_score * 100, 2),
            "label": confidence_label(confidence_score),
        },
        "basis": {
            "dominant_motif": dominant_motif,
            "topology_class": topology_class,
            "dominant_topology_axis": axis,
            "resonance_class": resonance_class,
            "dominant_resonance_axis": resonance_axis,
            "motif_richness": motif_richness,
            "raw_node_count": raw_node_count,
            "raw_edge_count": raw_edge_count,
            "truth_node_count": truth_node_count,
            "truth_edge_count": truth_edge_count,
            "has_ephemeris": has_ephemeris,
        },
        "warnings": [],
        "errors": [],
    }


def infer_role(
    *,
    dominant_motif: str,
    topology_class: str,
    axis: str,
    resonance_class: str,
    resonance_axis: str,
    motif_richness: float,
    raw_node_count: int,
    raw_edge_count: int,
    truth_node_count: int,
    truth_edge_count: int,
    notes: str,
    has_ephemeris: bool,
) -> str:
    """Infer structural role from graph-native evidence."""
    if "developer" in notes or "builder" in notes or "architect" in notes:
        return "Architect-Regulator"

    if "cyclic" in topology_class or motif_richness >= 0.65:
        return "Cycle-Weaver"

    if dominant_motif == "hub" and "distributed" in topology_class and "persistence" in axis:
        return "Persistence-Architect"

    if dominant_motif == "hub" and "distributed" in topology_class:
        return "Connector-Architect"

    if dominant_motif == "hub":
        return "Amplifier-Connector"

    if truth_edge_count > truth_node_count and motif_richness >= 0.4:
        return "Pattern-Weaver"

    if "persistence" in axis or "stability" in axis or "stability" in resonance_axis:
        return "Regulator-Builder"

    if has_ephemeris:
        return "Temporal-Interpreter"

    return "Unclassified Structural Actor"


def infer_subtype(
    *,
    role: str,
    topology_class: str,
    axis: str,
    resonance_axis: str,
    motif_richness: float,
    truth_edge_count: int,
) -> str:
    """Infer role subtype."""
    if role == "Cycle-Weaver":
        if motif_richness >= 0.75:
            return "High-Motif Cyclic Integrator"
        return "Cyclic Pattern Integrator"

    if role == "Persistence-Architect":
        return "Persistent Distributed Architect"

    if role == "Connector-Architect":
        return "Distributed Hub Connector"

    if role == "Pattern-Weaver":
        return "Truth-Graph Pattern Weaver"

    if role == "Regulator-Builder":
        if "stability" in resonance_axis:
            return "Stability-Regulating Builder"
        return "Persistence-Regulating Builder"

    if role == "Temporal-Interpreter":
        return "Temporal Context Interpreter"

    return "Unresolved Subtype"


def score_confidence(
    *,
    role: str,
    topology_class: str,
    dominant_motif: str,
    raw_node_count: int,
    raw_edge_count: int,
    has_ephemeris: bool,
) -> float:
    """Score classification confidence."""
    if role == "Unclassified Structural Actor":
        return 0.35

    score = 0.45

    if topology_class:
        score += 0.15
    if dominant_motif:
        score += 0.1
    if raw_node_count >= 25:
        score += 0.1
    if raw_edge_count >= 50:
        score += 0.1
    if has_ephemeris:
        score += 0.05

    return round(min(score, 0.9), 4)


def confidence_label(score: float) -> str:
    """Return confidence label."""
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "moderate"
    if score >= 0.4:
        return "limited"
    return "low"


def semantic_for_role(role: str) -> dict[str, str]:
    if role == "Cycle-Weaver":
        return {
            "civilization_function": "Cycle Weaver: detects repeating loops, recurrence structures, and return-patterns within complex systems.",
            "cognitive_style": "Pattern-recursive, motif-rich, and cycle-aware. This mind is oriented toward loops, recurrence, feedback, and repeating structural signatures.",
            "motivation": "Motivated by discovering recurring patterns, closing loops, and understanding how systems return transformed.",
            "emotional_pattern": "Emotion may intensify around repeated themes, unfinished cycles, or recognition of familiar patterns in new forms.",
            "stress_response": "Under stress, this profile may overtrack loops, revisit unresolved cycles, or become caught in recursive analysis.",
            "growth_path": "Growth comes from knowing when a cycle has completed and when to step into a new structure.",
        }

    if role == "Persistence-Architect":
        return {
            "civilization_function": "Persistence Architect: builds continuity across distributed systems and preserves structure through time.",
            "cognitive_style": "Durable, integrative, and persistence-oriented. This mind connects distributed information while maintaining long-range continuity.",
            "motivation": "Motivated by coherence, endurance, timing, and the preservation of useful structures.",
            "emotional_pattern": "Emotion may intensify when continuity breaks or when long-built systems become unstable.",
            "stress_response": "Under stress, this profile may attempt to hold too much structure together alone.",
            "growth_path": "Growth comes from allowing structure to evolve without losing the continuity that gives it meaning.",
        }

    if role == "Pattern-Weaver":
        return {
            "civilization_function": "Pattern Weaver: links meaningful structures into recognizable forms and translates complexity into relational maps.",
            "cognitive_style": "Associative, relational, and motif-sensitive. This mind identifies meaningful links across dense structural fields.",
            "motivation": "Motivated by synthesis, recognition, symbolic mapping, and the discovery of hidden relationships.",
            "emotional_pattern": "Emotion may intensify when patterns are visible but not yet communicable.",
            "stress_response": "Under stress, this profile may become tangled in too many meaningful connections.",
            "growth_path": "Growth comes from pruning connections until the essential pattern becomes clear.",
        }

    if role == "Architect-Regulator":
        return {
            "civilization_function": "System Architect: builds durable structures that organize complexity into usable form.",
            "cognitive_style": "Structural, integrative, and systems-oriented. This mind looks for hidden architecture, recurring patterns, and practical ways to make complexity usable.",
            "motivation": "Motivated by coherence, mastery, usefulness, truth, and the desire to turn abstract systems into functioning tools.",
            "emotional_pattern": "Emotion may intensify when systems feel chaotic, misunderstood, or blocked.",
            "stress_response": "Under stress, this profile may overbuild, overanalyze, isolate, or feel responsible for holding too many moving parts together.",
            "growth_path": "Growth comes from balancing system-building with embodiment, collaboration, and iterative refinement.",
        }

    if role == "Connector-Architect":
        return {
            "civilization_function": "Network Architect: connects separate systems into a larger working field.",
            "cognitive_style": "Relational, topological, and systems-aware.",
            "motivation": "Motivated by connection, synthesis, coherence, and field-level understanding.",
            "emotional_pattern": "Emotion may intensify when systems fragment or meaningful links are ignored.",
            "stress_response": "Under stress, this profile may try to hold the entire network alone.",
            "growth_path": "Growth comes from discerning which connections are essential.",
        }

    if role == "Amplifier-Connector":
        return {
            "civilization_function": "Signal Amplifier: increases visibility, connection, and movement across a field.",
            "cognitive_style": "Expressive, associative, and catalytic.",
            "motivation": "Motivated by resonance, communication, influence, and shared activation.",
            "emotional_pattern": "Emotion may intensify around recognition, momentum, and blocked expression.",
            "stress_response": "Under stress, this profile may become overstimulated or reactive.",
            "growth_path": "Growth comes from grounding expression in stable structures.",
        }

    if role == "Regulator-Builder":
        return {
            "civilization_function": "Stability Builder: preserves continuity and turns repeated effort into durable structure.",
            "cognitive_style": "Practical, stabilizing, and persistence-oriented.",
            "motivation": "Motivated by reliability, proof, protection, and long-term usefulness.",
            "emotional_pattern": "Emotion may intensify when stability is threatened.",
            "stress_response": "Under stress, this profile may become rigid, guarded, or overly self-reliant.",
            "growth_path": "Growth comes from allowing adaptation without abandoning structure.",
        }

    if role == "Temporal-Interpreter":
        return {
            "civilization_function": "Timing Interpreter: reads structure through activation, sequence, and change over time.",
            "cognitive_style": "Timing-sensitive, contextual, and pattern-aware.",
            "motivation": "Motivated by timing, alignment, development, and understanding when patterns become visible.",
            "emotional_pattern": "Emotion may intensify during transition windows.",
            "stress_response": "Under stress, this profile may become overly focused on signals and timing.",
            "growth_path": "Growth comes from using timing as guidance, not confinement.",
        }

    return {
        "civilization_function": "Civilization function unresolved.",
        "cognitive_style": "Not enough deterministic evidence to classify cognitive style with confidence.",
        "motivation": "Motivation remains provisional until more layers are available.",
        "emotional_pattern": "Emotional style is not yet fully resolved.",
        "stress_response": "Stress response cannot be strongly classified yet.",
        "growth_path": "Growth path remains provisional.",
    }
