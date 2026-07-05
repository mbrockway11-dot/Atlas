
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
