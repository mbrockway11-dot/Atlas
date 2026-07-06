
"""Shared ontology for Atlas Synthesis."""

from __future__ import annotations

from typing import Final


SYNTHESIS_ONTOLOGY_VERSION: Final[str] = "1.0"


CATEGORIES: Final[dict[str, str]] = {
    "identity_architecture": "How the system organizes selfhood, authorship, purpose, and visibility.",
    "cognitive_architecture": "How the system routes information, learns, interprets, and communicates.",
    "emotional_architecture": "How the system stabilizes internally and returns to equilibrium.",
    "motivational_architecture": "How effort, desire, drive, expansion, and initiative are allocated.",
    "relational_architecture": "How connection, value, attraction, reciprocity, and social bonding organize.",
    "constraint_architecture": "How limits, discipline, responsibility, compression, and durability shape the system.",
    "symbolic_architecture": "How encoded identity, gematria, numerology, Kamea, and symbolic patterns converge.",
    "temporal_architecture": "How timing, activation windows, recurrence, and developmental sequencing behave.",
    "population_position": "How rare, central, impactful, or unusual the profile is within the corpus.",
    "relationship_dynamics": "How the profile interacts with another profile or group.",
    "structural_risk": "Where friction, overload, imbalance, or contradiction may emerge.",
    "growth_path": "How the system develops, refines, integrates, and evolves.",
}


FEATURES: Final[dict[str, str]] = {
    "persistent_architecture": "Durable system-building, continuity, long-term structure, and preservation.",
    "visible_authorship": "Public expression, creative identity, authorship, visibility, and leadership through creation.",
    "recursive_patterning": "Cycles, loops, recurrence, iterative refinement, and repeated symbolic structures.",
    "distributed_integration": "Connecting many domains without collapsing them into one narrow hierarchy.",
    "high_truth_density": "Reduced graph retains unusually strong internal structural connectivity.",
    "low_truth_density": "Reduced graph is sparse, selective, or highly compressed.",
    "high_graph_complexity": "Canonical graph produces many nodes or relationships relative to the corpus.",
    "low_graph_complexity": "Canonical graph is compact or selectively connected.",
    "information_routing": "How meaning, communication, interpretation, and symbolic logic move through the system.",
    "internal_stabilization": "How the system regulates emotion, memory, comfort, and psychological equilibrium.",
    "energy_allocation": "Where drive, force, protection, conflict, and action concentrate.",
    "expansion_pattern": "Where the system grows, teaches, magnifies, or generalizes meaning.",
    "constraint_pattern": "Where limits, discipline, endurance, or responsibility compress the system into durable form.",
    "value_selection": "How the system chooses what is beautiful, worthy, desirable, or relationally important.",
    "innovation_pattern": "How novelty, discontinuity, or system-breaking insight enters the graph.",
    "abstraction_pattern": "How imagination, symbolism, uncertainty, dream logic, or porous boundaries affect the system.",
    "transformation_pattern": "How deep rewrites, endings, regeneration, or power shifts reshape the system.",
    "rare_signature": "Profile expresses an uncommon pattern in the current corpus.",
    "high_impact_signature": "Profile scores highly across multiple structural impact dimensions.",
    "alignment": "Two or more systems reinforce the same structural theme.",
    "conflict": "Two or more systems point toward competing structural themes.",
    "long_horizon_planning": "Maintains long planning arcs and organizes behavior around delayed structural outcomes.",
    "durable_system_construction": "Builds systems intended to persist beyond the immediate moment.",
    "continuity_preservation": "Protects coherence, memory, and continuity across time.",
    "recurrence_detection": "Recognizes repeated patterns, cycles, and returning themes.",
    "iterative_refinement": "Improves through repeated passes rather than one-time completion.",
    "cross_domain_linking": "Connects ideas, people, or systems across different domains.",
    "parallel_context_management": "Maintains multiple active contexts without collapsing them into one.",
    "signal_amplification": "Increases visibility, attention, and movement around a signal.",
    "expressive_catalysis": "Activates others through expression, communication, or performance.",
    "pattern_compression": "Compresses complexity into recognizable structures or reusable forms.",
    "high_resolution_discrimination": "Separates signal from noise with unusually fine structural sensitivity.",
    "complexity_tolerance": "Can operate inside dense or highly connected information environments.",
    "structural_selectivity": "Preserves only relationships that remain structurally meaningful after reduction.",
    "aggressive_compression": "Reduces complexity sharply, sometimes discarding weak or peripheral signals.",
    "branching_decision_style": "Explores decisions through branching alternatives and parallel routes.",
    "constraint_sensitive_execution": "Acts with strong awareness of limits, bottlenecks, and structural consequences.",
    "stability_seeking": "Prioritizes regulation, steadiness, and coherent internal state.",
    "message_propagation": "Moves information outward through channels, networks, or repeated transmission.",
    "activation_driven_action": "Acts when sufficient energetic or situational activation accumulates.",
    "prime_structure": "A symbolic encoding resolves to a prime total, suggesting low factor decomposition and strong indivisibility.",
    "reduction_stability": "Multiple encodings reduce to the same root or closely related reduction pattern.",
    "symbolic_coherence": "Independent symbolic encodings converge rather than diverge.",
}


FEATURE_TO_CATEGORY: Final[dict[str, str]] = {
    "persistent_architecture": "identity_architecture",
    "visible_authorship": "identity_architecture",
    "recursive_patterning": "symbolic_architecture",
    "distributed_integration": "cognitive_architecture",
    "high_truth_density": "population_position",
    "low_truth_density": "population_position",
    "high_graph_complexity": "population_position",
    "low_graph_complexity": "population_position",
    "information_routing": "cognitive_architecture",
    "internal_stabilization": "emotional_architecture",
    "energy_allocation": "motivational_architecture",
    "expansion_pattern": "motivational_architecture",
    "constraint_pattern": "constraint_architecture",
    "value_selection": "relational_architecture",
    "innovation_pattern": "cognitive_architecture",
    "abstraction_pattern": "symbolic_architecture",
    "transformation_pattern": "growth_path",
    "rare_signature": "population_position",
    "high_impact_signature": "population_position",
    "alignment": "relationship_dynamics",
    "conflict": "structural_risk",
    "long_horizon_planning": "motivational_architecture",
    "durable_system_construction": "constraint_architecture",
    "continuity_preservation": "identity_architecture",
    "recurrence_detection": "cognitive_architecture",
    "iterative_refinement": "growth_path",
    "cross_domain_linking": "cognitive_architecture",
    "parallel_context_management": "cognitive_architecture",
    "signal_amplification": "relationship_dynamics",
    "expressive_catalysis": "relationship_dynamics",
    "pattern_compression": "cognitive_architecture",
    "high_resolution_discrimination": "cognitive_architecture",
    "complexity_tolerance": "cognitive_architecture",
    "structural_selectivity": "constraint_architecture",
    "aggressive_compression": "constraint_architecture",
    "branching_decision_style": "cognitive_architecture",
    "constraint_sensitive_execution": "constraint_architecture",
    "stability_seeking": "emotional_architecture",
    "message_propagation": "relationship_dynamics",
    "activation_driven_action": "motivational_architecture",
    "prime_structure": "symbolic_architecture",
    "reduction_stability": "symbolic_architecture",
    "symbolic_coherence": "symbolic_architecture",
}


def describe_category(category: str) -> str:
    """Return category description."""
    return CATEGORIES.get(normalize_key(category), "Unknown synthesis category.")


def describe_feature(feature: str) -> str:
    """Return feature description."""
    return FEATURES.get(normalize_key(feature), "Unknown synthesis feature.")


def category_for_feature(feature: str, default: str = "symbolic_architecture") -> str:
    """Return ontology category for a feature."""
    return FEATURE_TO_CATEGORY.get(normalize_key(feature), default)


def normalize_key(value: str) -> str:
    """Normalize ontology key."""
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )
