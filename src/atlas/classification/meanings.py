"""Official Atlas classification meanings."""

from typing import Any


FUNCTIONAL_ROLE_MEANINGS: dict[str, dict[str, Any]] = {
    "Driver": {
        "core_function": "Initiates change.",
        "description": (
            "Drivers inject directional energy into a system. They tend to "
            "produce movement, concentrate influence, and reorganize existing "
            "structures."
        ),
        "topological_indicators": [
            "high driver score",
            "strong asymmetry",
            "directional flow",
            "dominant hubs",
            "high stress gradients",
            "lower equilibrium",
        ],
        "system_behavior": [
            "creates movement",
            "begins transitions",
            "alters trajectories",
            "breaks equilibrium",
            "establishes new centers of influence",
        ],
        "typical_roles": [
            "founders",
            "conquerors",
            "revolutionaries",
            "disruptive innovators",
            "explorers",
        ],
        "research_hypothesis": (
            "Driver-dominant cohorts may appear more frequently during periods "
            "of formation, expansion, or institutional transformation."
        ),
    },
    "Amplifier": {
        "core_function": "Increases propagation.",
        "description": (
            "Amplifiers spread, reinforce, and accelerate existing dynamics "
            "through a network."
        ),
        "topological_indicators": [
            "high amplifier score",
            "high connectivity",
            "dense transmission paths",
            "moderate asymmetry",
            "efficient information flow",
        ],
        "system_behavior": [
            "accelerates diffusion",
            "reinforces trends",
            "connects subsystems",
            "expands influence",
            "increases responsiveness",
        ],
        "typical_roles": [
            "philosophers",
            "teachers",
            "evangelists",
            "scientists",
            "artists",
            "cultural icons",
        ],
        "research_hypothesis": (
            "Amplifier-dominant cohorts may become more common during periods "
            "of intellectual, cultural, or technological expansion."
        ),
    },
    "Regulator": {
        "core_function": "Maintains coherence.",
        "description": (
            "Regulators stabilize systems by distributing influence, balancing "
            "competing forces, and reducing structural volatility."
        ),
        "topological_indicators": [
            "high regulator score",
            "high symmetry",
            "distributed connectivity",
            "lower stress",
            "stable equilibrium",
        ],
        "system_behavior": [
            "preserves structure",
            "coordinates subsystems",
            "prevents fragmentation",
            "redistributes influence",
            "supports institutional continuity",
        ],
        "typical_roles": [
            "administrators",
            "judges",
            "diplomats",
            "civil servants",
            "institutional architects",
        ],
        "research_hypothesis": (
            "Regulator-dominant cohorts may be associated with consolidation, "
            "governance, and long-lived institutions."
        ),
    },
}


TOPOLOGICAL_EXPRESSION_MEANINGS: dict[str, dict[str, Any]] = {
    "Hub-Dominant": {
        "description": "Influence is concentrated in a small number of highly connected nodes.",
        "traits": [
            "centralized",
            "directional",
            "efficient",
            "vulnerable to hub loss",
        ],
    },
    "Distributed": {
        "description": "Influence is spread broadly across the network.",
        "traits": [
            "balanced",
            "redundant",
            "resilient",
            "decentralized",
        ],
    },
    "Radiating": {
        "description": "Influence flows outward from one or more active centers.",
        "traits": [
            "expansion",
            "broadcasting",
            "outward propagation",
        ],
    },
    "Linear-Sequential": {
        "description": "Influence follows sequential pathways.",
        "traits": [
            "ordered progression",
            "stepwise development",
            "low branching",
        ],
    },
    "Bridge-Connector": {
        "description": "The topology emphasizes passages between otherwise separated regions.",
        "traits": [
            "connective",
            "mediating",
            "translation between regions",
        ],
    },
    "Convergent": {
        "description": "Many pathways merge into common endpoints.",
        "traits": [
            "integration",
            "synthesis",
            "consolidation",
        ],
    },
    "Cyclic": {
        "description": "Feedback loops dominate the structure.",
        "traits": [
            "recurrence",
            "reinforcement",
            "self-reference",
        ],
    },
    "Fragmented": {
        "description": "The topology contains separated regions with limited integration.",
        "traits": [
            "disconnected",
            "low cohesion",
            "cluster separation",
        ],
    },
    "Mixed": {
        "description": "No single expression dominates the topology.",
        "traits": [
            "hybrid organization",
            "mixed structural signals",
            "context-dependent behavior",
        ],
    },
}


STRUCTURAL_STATE_MEANINGS: dict[str, dict[str, Any]] = {
    "Stable": {
        "description": "The topology shows durable coherence and balanced structure.",
        "traits": [
            "high symmetry",
            "low stress",
            "strong regulation",
            "persistent organization",
        ],
    },
    "Adaptive": {
        "description": "The topology preserves coherence while remaining flexible.",
        "traits": [
            "balanced flexibility",
            "moderate change",
            "preserved coherence",
        ],
    },
    "Transitional": {
        "description": "The topology is actively reorganizing.",
        "traits": [
            "active reorganization",
            "structural migration",
            "high directional movement",
        ],
    },
    "Emergent": {
        "description": "The topology shows new structure formation.",
        "traits": [
            "new hubs forming",
            "rapid connectivity growth",
            "novel structure",
        ],
    },
    "Fragile": {
        "description": "The topology may be sensitive to perturbation.",
        "traits": [
            "apparent stability",
            "high sensitivity",
            "limited redundancy",
        ],
    },
    "Fragmented": {
        "description": "The topology has reduced integration across separated regions.",
        "traits": [
            "multiple disconnected components",
            "reduced integration",
            "declining coherence",
        ],
    },
    "Saturated": {
        "description": "The topology has high redundancy and limited novelty.",
        "traits": [
            "dense connectivity",
            "few novel pathways",
            "high redundancy",
        ],
    },
}


PLANETARY_TOPOLOGY_MEANINGS: dict[str, dict[str, Any]] = {
    "Saturn": {
        "topological_theme": "Constraint, persistence, structural order.",
    },
    "Jupiter": {
        "topological_theme": "Expansion, integration, system growth.",
    },
    "Mars": {
        "topological_theme": "Initiation, conflict, directed action.",
    },
    "Sun": {
        "topological_theme": "Centralization, identity, organization.",
    },
    "Venus": {
        "topological_theme": "Harmony, relational cohesion, attraction.",
    },
    "Mercury": {
        "topological_theme": "Communication, information flow, adaptation.",
    },
    "Moon": {
        "topological_theme": "Memory, cyclicity, collective responsiveness.",
    },
}


def get_functional_role_meaning(role: str) -> dict[str, Any]:
    """Return meaning for a functional role, including hybrids."""
    if role in FUNCTIONAL_ROLE_MEANINGS:
        return FUNCTIONAL_ROLE_MEANINGS[role]

    if "Hybrid" in role:
        parts = role.replace(" Hybrid", "").split("-")
        return {
            "core_function": "Hybrid function.",
            "description": (
                "This topology blends multiple primary functions rather than "
                "expressing one dominant role cleanly."
            ),
            "components": [
                {
                    "role": part,
                    "meaning": FUNCTIONAL_ROLE_MEANINGS.get(part, {}),
                }
                for part in parts
            ],
        }

    return {
        "core_function": "Unclassified function.",
        "description": f"No official meaning is registered for role: {role}.",
    }


def get_expression_meaning(expression: str) -> dict[str, Any]:
    """Return meaning for a topological expression."""
    return TOPOLOGICAL_EXPRESSION_MEANINGS.get(
        expression,
        {
            "description": f"No official meaning is registered for expression: {expression}.",
            "traits": [],
        },
    )


def get_structural_state_meaning(state: str) -> dict[str, Any]:
    """Return meaning for a structural state."""
    return STRUCTURAL_STATE_MEANINGS.get(
        state,
        {
            "description": f"No official meaning is registered for state: {state}.",
            "traits": [],
        },
    )


def get_planetary_topology_meaning(planet: str) -> dict[str, Any]:
    """Return meaning for a planetary topology layer."""
    return PLANETARY_TOPOLOGY_MEANINGS.get(
        planet,
        {
            "topological_theme": f"No official topology meaning is registered for planet: {planet}.",
        },
    )