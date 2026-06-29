"""Identity Resonance Engine.

The Identity Resonance Engine measures how activation propagates through an
Identity Topology. It does not interpret personality. It produces deterministic
graph-behavior measurements from topology scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.graph.identity_topology import IdentityTopology


RESONANCE_VERSION = "1.0"


@dataclass(frozen=True)
class IdentityResonance:
    """Resonance behavior profile for one identity topology."""

    version: str
    name: str
    resonance_class: str
    dominant_resonance_axis: str
    activation_pattern: str
    propagation_pattern: str
    damping_pattern: str
    resonance_vector: dict[str, float]
    summary: dict[str, Any]


def build_identity_resonance(
    topology: IdentityTopology,
) -> IdentityResonance:
    """Build Identity Resonance from Identity Topology."""
    resonance_vector = {
        "activation": compute_activation(topology),
        "propagation": compute_propagation(topology),
        "stability": topology.persistence_score,
        "recirculation": topology.cyclicity_score,
        "channeling": topology.bottleneck_score,
        "branching": topology.branching_score,
    }

    dominant_resonance_axis = max(
        resonance_vector,
        key=resonance_vector.get,
    )

    resonance_class = classify_resonance(resonance_vector)
    activation_pattern = classify_activation_pattern(resonance_vector)
    propagation_pattern = classify_propagation_pattern(resonance_vector)
    damping_pattern = classify_damping_pattern(resonance_vector)

    summary = {
        "version": RESONANCE_VERSION,
        "definition": (
            "Deterministic resonance behavior profile derived from IdentityTopology."
        ),
        "source": "IdentityTopology",
        "topology_version": topology.version,
        "resonance_class": resonance_class,
        "dominant_resonance_axis": dominant_resonance_axis,
        "activation_pattern": activation_pattern,
        "propagation_pattern": propagation_pattern,
        "damping_pattern": damping_pattern,
        "resonance_vector": resonance_vector,
    }

    return IdentityResonance(
        version=RESONANCE_VERSION,
        name=topology.name,
        resonance_class=resonance_class,
        dominant_resonance_axis=dominant_resonance_axis,
        activation_pattern=activation_pattern,
        propagation_pattern=propagation_pattern,
        damping_pattern=damping_pattern,
        resonance_vector=resonance_vector,
        summary=summary,
    )


def compute_activation(topology: IdentityTopology) -> float:
    """Compute activation potential."""
    return clamp(
        topology.persistence_score * 0.35
        + topology.branching_score * 0.25
        + topology.hierarchy_score * 0.20
        + topology.cyclicity_score * 0.20
    )


def compute_propagation(topology: IdentityTopology) -> float:
    """Compute propagation potential."""
    return clamp(
        topology.branching_score * 0.35
        + topology.cyclicity_score * 0.25
        + topology.bottleneck_score * 0.20
        + topology.persistence_score * 0.20
    )


def classify_resonance(vector: dict[str, float]) -> str:
    """Classify resonance behavior."""
    if vector["recirculation"] >= 0.35 and vector["activation"] >= 0.50:
        return "recirculating_activation"

    if vector["channeling"] >= 0.30 and vector["stability"] >= 0.50:
        return "channeled_stability"

    if vector["branching"] >= 0.35 and vector["propagation"] >= 0.45:
        return "branching_propagation"

    if vector["stability"] >= 0.70:
        return "stable_resonance"

    if vector["activation"] >= 0.50:
        return "activated_field"

    return "low_resonance"


def classify_activation_pattern(vector: dict[str, float]) -> str:
    """Classify activation pattern."""
    if vector["activation"] >= 0.70:
        return "high_activation"

    if vector["activation"] >= 0.45:
        return "moderate_activation"

    return "low_activation"


def classify_propagation_pattern(vector: dict[str, float]) -> str:
    """Classify propagation pattern."""
    if vector["branching"] >= 0.35:
        return "branching_spread"

    if vector["channeling"] >= 0.30:
        return "channeled_flow"

    if vector["recirculation"] >= 0.30:
        return "recursive_flow"

    return "diffuse_flow"


def classify_damping_pattern(vector: dict[str, float]) -> str:
    """Classify damping pattern."""
    if vector["stability"] >= 0.70 and vector["channeling"] >= 0.25:
        return "contained"

    if vector["recirculation"] >= 0.35:
        return "self_reinforcing"

    if vector["activation"] < 0.35:
        return "strongly_damped"

    return "moderately_damped"


def identity_resonance_to_dict(
    resonance: IdentityResonance,
) -> dict[str, Any]:
    """Convert IdentityResonance to JSON-safe dictionary."""
    return asdict(resonance)


def clamp(value: float) -> float:
    """Clamp to 0-1."""
    return max(0.0, min(1.0, float(value)))