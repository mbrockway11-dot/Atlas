"""Atlas profile classifier.

Converts available profile evidence into human-readable structural roles.
"""

from __future__ import annotations

from typing import Any


PROFILE_CLASSIFIER_VERSION = "1.0"


def classify_profile(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify a profile from canonical profile payload data."""
    identity = payload.get("identity", {})
    graph = payload.get("graph", {})
    temporal = payload.get("temporal", {})
    metrics = payload.get("metrics", {})
    intake_notes = extract_notes(payload)

    graph_metrics = extract_graph_metrics(graph, payload)
    temporal_ready = bool(
        temporal.get("temporal_composite_completed")
        or temporal.get("runtime", {}).get("natal", {}).get("ephemeris")
        or metrics.get("has_ephemeris")
    )

    role = infer_structural_role(
        graph_metrics=graph_metrics,
        temporal_ready=temporal_ready,
        notes=intake_notes,
    )

    semantic = role_semantic(role)

    return {
        "success": True,
        "version": PROFILE_CLASSIFIER_VERSION,
        "profile_key": payload.get("profile_key") or identity.get("profile_key", ""),
        "name": identity.get("display_name") or identity.get("full_name") or "Unknown Profile",
        "structural_role": role,
        "civilization_function": semantic["civilization_function"],
        "cognitive_style": semantic["cognitive_style"],
        "motivation": semantic["motivation"],
        "emotional_pattern": semantic["emotional_pattern"],
        "stress_response": semantic["stress_response"],
        "growth_path": semantic["growth_path"],
        "confidence": resolve_confidence(graph_metrics, temporal_ready),
        "basis": {
            "graph_metrics": graph_metrics,
            "temporal_ready": temporal_ready,
            "notes": intake_notes,
        },
        "warnings": [],
        "errors": [],
    }


def extract_notes(payload: dict[str, Any]) -> str:
    """Extract available profile notes."""
    intake = payload.get("intake", {})
    if isinstance(intake, dict) and intake.get("notes"):
        return str(intake.get("notes", ""))

    summary = payload.get("summary", {})
    if isinstance(summary, dict) and summary.get("notes"):
        return str(summary.get("notes", ""))

    return str(payload.get("notes", ""))


def extract_graph_metrics(
    graph: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Extract graph metrics from canonical or legacy payload shapes."""
    candidates = [
        graph.get("graph_intelligence", {}),
        graph.get("graph", {}),
        graph.get("topology", {}),
        payload.get("acf", {}).get("metrics", {}),
        payload.get("metrics", {}),
    ]

    merged: dict[str, Any] = {}

    for candidate in candidates:
        if isinstance(candidate, dict):
            merged.update(flatten_known_graph(candidate))

    return merged


def flatten_known_graph(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten known graph metric shapes."""
    result: dict[str, Any] = {}

    for key in (
        "dominant_motif",
        "topology_class",
        "dominant_topology_axis",
        "resonance_class",
        "dominant_resonance_axis",
        "cig_nodes",
        "cig_edges",
        "stg_nodes",
        "stg_edges",
        "motif_count",
        "audit_status",
    ):
        if key in data:
            result[key] = data[key]

    metrics = data.get("metrics")
    if isinstance(metrics, dict):
        result.update(flatten_known_graph(metrics))

    return result


def infer_structural_role(
    *,
    graph_metrics: dict[str, Any],
    temporal_ready: bool,
    notes: str,
) -> str:
    """Infer structural role from graph, temporal, and notes."""
    motif = str(graph_metrics.get("dominant_motif", "")).lower()
    topology = str(graph_metrics.get("topology_class", "")).lower()
    axis = str(graph_metrics.get("dominant_topology_axis", "")).lower()
    resonance = str(graph_metrics.get("resonance_class", "")).lower()
    notes_lower = notes.lower()

    if any(word in notes_lower for word in ("developer", "builder", "architect", "engineer")):
        if "distributed" in topology or axis in {"persistence", "structure", "stability"}:
            return "Architect-Regulator"
        return "Builder-Interpreter"

    if motif == "hub" and "distributed" in topology:
        return "Connector-Architect"

    if motif == "hub":
        return "Amplifier-Connector"

    if "persistence" in axis or "stability" in axis:
        return "Regulator-Builder"

    if "low_resonance" in resonance and temporal_ready:
        return "Observer-Integrator"

    if temporal_ready:
        return "Temporal-Interpreter"

    return "Unclassified Structural Actor"


def role_semantic(role: str) -> dict[str, str]:
    """Return semantic description for a structural role."""
    library = {
        "Architect-Regulator": {
            "civilization_function": "System Architect: builds durable structures that organize complexity into usable form.",
            "cognitive_style": "Structural, integrative, and systems-oriented. This mind looks for hidden architecture, recurring patterns, and practical ways to make complexity usable.",
            "motivation": "Motivated by coherence, mastery, usefulness, truth, and the desire to turn abstract systems into functioning tools.",
            "emotional_pattern": "Emotion may intensify when systems feel chaotic, misunderstood, or blocked. The profile often seeks stability through design, language, and structure.",
            "stress_response": "Under stress, this profile may overbuild, overanalyze, isolate, or feel responsible for holding too many moving parts together.",
            "growth_path": "Growth comes from balancing system-building with embodiment, collaboration, and trust in iterative refinement.",
        },
        "Builder-Interpreter": {
            "civilization_function": "Bridge Builder: translates abstract meaning into practical systems others can use.",
            "cognitive_style": "Interpretive, constructive, and pattern-sensitive. This mind moves between symbolic meaning and concrete implementation.",
            "motivation": "Motivated by discovery, expression, usefulness, and the urge to make invisible patterns communicable.",
            "emotional_pattern": "Emotion may collect around being understood, being useful, and making complex insights accessible.",
            "stress_response": "Under stress, this profile may become scattered between vision and execution.",
            "growth_path": "Growth comes from sequencing ideas clearly and finishing one bridge before opening the next.",
        },
        "Connector-Architect": {
            "civilization_function": "Network Architect: connects separate systems into a larger working field.",
            "cognitive_style": "Relational, topological, and systems-aware. This mind sees how nodes, people, ideas, and structures interlock.",
            "motivation": "Motivated by connection, synthesis, coherence, and field-level understanding.",
            "emotional_pattern": "Emotion may intensify when systems fragment or when meaningful links are ignored.",
            "stress_response": "Under stress, this profile may try to hold the entire network alone.",
            "growth_path": "Growth comes from discerning which connections are essential and which can remain latent.",
        },
        "Amplifier-Connector": {
            "civilization_function": "Signal Amplifier: increases visibility, connection, and movement across a field.",
            "cognitive_style": "Expressive, associative, and catalytic. This mind activates ideas by linking them to people, language, and momentum.",
            "motivation": "Motivated by resonance, communication, influence, and shared activation.",
            "emotional_pattern": "Emotion may intensify around recognition, momentum, and blocked expression.",
            "stress_response": "Under stress, this profile may become overstimulated or reactive.",
            "growth_path": "Growth comes from grounding expression in stable structures.",
        },
        "Regulator-Builder": {
            "civilization_function": "Stability Builder: preserves continuity and turns repeated effort into durable structure.",
            "cognitive_style": "Practical, stabilizing, and persistence-oriented. This mind values what can be tested, repeated, and maintained.",
            "motivation": "Motivated by reliability, proof, protection, and long-term usefulness.",
            "emotional_pattern": "Emotion may intensify when stability is threatened or when work is not respected.",
            "stress_response": "Under stress, this profile may become rigid, guarded, or overly self-reliant.",
            "growth_path": "Growth comes from allowing adaptation without abandoning structure.",
        },
        "Observer-Integrator": {
            "civilization_function": "Pattern Integrator: observes weak signals and gradually converts them into coherent understanding.",
            "cognitive_style": "Reflective, integrative, and perception-oriented. This mind gathers fragments until a larger pattern becomes visible.",
            "motivation": "Motivated by truth, synthesis, discernment, and subtle pattern recognition.",
            "emotional_pattern": "Emotion may intensify around ambiguity, hidden meaning, or being unable to name what is perceived.",
            "stress_response": "Under stress, this profile may withdraw, overprocess, or delay action until certainty improves.",
            "growth_path": "Growth comes from turning perception into timely action.",
        },
        "Temporal-Interpreter": {
            "civilization_function": "Timing Interpreter: reads structure through activation, sequence, and change over time.",
            "cognitive_style": "Timing-sensitive, contextual, and pattern-aware. This mind understands behavior as something that changes under pressure.",
            "motivation": "Motivated by timing, alignment, development, and understanding when patterns become visible.",
            "emotional_pattern": "Emotion may intensify during transition windows or when timing feels misaligned.",
            "stress_response": "Under stress, this profile may become overly focused on signals and timing.",
            "growth_path": "Growth comes from using timing as guidance, not as confinement.",
        },
        "Unclassified Structural Actor": {
            "civilization_function": "Civilization function unresolved.",
            "cognitive_style": "Not enough deterministic evidence to classify cognitive style with confidence.",
            "motivation": "Motivation remains provisional until more layers are available.",
            "emotional_pattern": "Emotional style is not yet fully resolved.",
            "stress_response": "Stress response cannot be strongly classified yet.",
            "growth_path": "Growth path remains provisional.",
        },
    }

    return library.get(role, library["Unclassified Structural Actor"])


def resolve_confidence(
    graph_metrics: dict[str, Any],
    temporal_ready: bool,
) -> dict[str, Any]:
    """Resolve classifier confidence."""
    score = 0.25

    if graph_metrics:
        score += 0.35

    if graph_metrics.get("dominant_motif"):
        score += 0.10

    if graph_metrics.get("topology_class"):
        score += 0.10

    if temporal_ready:
        score += 0.15

    score = min(score, 0.95)

    if score >= 0.75:
        label = "high"
    elif score >= 0.55:
        label = "moderate"
    elif score >= 0.35:
        label = "limited"
    else:
        label = "low"

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": label,
    }
