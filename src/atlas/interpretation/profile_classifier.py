"""Atlas profile classifier."""

from __future__ import annotations

from typing import Any

PROFILE_CLASSIFIER_VERSION = "1.0"


def classify_profile(payload: dict[str, Any]) -> dict[str, Any]:
    identity = payload.get("identity", {})
    graph = payload.get("graph", {})
    metrics = payload.get("metrics", {})
    temporal = payload.get("temporal", {})
    notes = str(payload.get("notes", ""))

    graph_intel = graph.get("graph_intelligence", {}) if isinstance(graph, dict) else {}
    topology = graph.get("topology", {}) if isinstance(graph, dict) else {}

    dominant_motif = (
        graph_intel.get("dominant_motif")
        or topology.get("dominant_motif")
        or metrics.get("dominant_motif")
        or ""
    )

    topology_class = (
        graph_intel.get("topology_class")
        or topology.get("topology_class")
        or metrics.get("topology_class")
        or ""
    )

    axis = (
        graph_intel.get("dominant_topology_axis")
        or topology.get("dominant_topology_axis")
        or metrics.get("dominant_topology_axis")
        or ""
    )

    has_ephemeris = bool(
        metrics.get("has_ephemeris")
        or temporal.get("runtime", {}).get("natal", {}).get("ephemeris")
        or temporal.get("natal", {}).get("ephemeris")
    )

    role = infer_role(
        dominant_motif=str(dominant_motif).lower(),
        topology_class=str(topology_class).lower(),
        axis=str(axis).lower(),
        notes=notes.lower(),
        has_ephemeris=has_ephemeris,
    )

    semantic = semantic_for_role(role)

    return {
        "success": True,
        "version": PROFILE_CLASSIFIER_VERSION,
        "profile_key": payload.get("profile_key") or identity.get("profile_key", ""),
        "name": identity.get("display_name") or identity.get("full_name") or "Unknown Profile",
        "structural_role": role,
        **semantic,
        "confidence": {
            "score": 0.75 if role != "Unclassified Structural Actor" else 0.35,
            "percent": 75.0 if role != "Unclassified Structural Actor" else 35.0,
            "label": "moderate" if role != "Unclassified Structural Actor" else "limited",
        },
        "basis": {
            "dominant_motif": dominant_motif,
            "topology_class": topology_class,
            "dominant_topology_axis": axis,
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
    notes: str,
    has_ephemeris: bool,
) -> str:
    if "developer" in notes or "builder" in notes or "architect" in notes:
        return "Architect-Regulator"

    if dominant_motif == "hub" and "distributed" in topology_class:
        return "Connector-Architect"

    if dominant_motif == "hub":
        return "Amplifier-Connector"

    if "persistence" in axis or "stability" in axis:
        return "Regulator-Builder"

    if has_ephemeris:
        return "Temporal-Interpreter"

    return "Unclassified Structural Actor"


def semantic_for_role(role: str) -> dict[str, str]:
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
