"""Identity Vector Engine schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


IVE_VERSION = "0.3.0"


VECTOR_FEATURES = [
    "node_coverage",
    "edge_coverage",
    "density",
    "entropy",
    "axis_strength",
    "graph_coherence",
    "core_survival_score",
    "topology_stability",
    "attractor_stability",
    "bridge_ratio",
    "articulation_ratio",
    "loop_ratio",
    "hub_ratio",
    "leaf_ratio",
    "reduction_entropy",
    "node_survival_auc",
    "edge_survival_auc",
]


IDENTITY_GLOBAL_FEATURES = [
    "mean_node_coverage",
    "mean_edge_coverage",
    "mean_density",
    "mean_entropy",
    "mean_axis_strength",
    "mean_graph_coherence",
    "mean_core_survival_score",
    "mean_topology_stability",
    "mean_attractor_stability",
    "mean_bridge_ratio",
    "mean_articulation_ratio",
    "mean_loop_ratio",
    "mean_hub_ratio",
    "mean_leaf_ratio",
    "mean_reduction_entropy",
    "mean_node_survival_auc",
    "mean_edge_survival_auc",
    "planet_balance_index",
    "planet_variance_index",
    "structural_complexity_index",
    "structural_stability_index",
]


@dataclass(frozen=True)
class PlanetFeatureVector:
    """Raw bounded feature vector for one cipher x planet layer."""

    version: str
    name: str
    cipher: str
    planet: str
    kamea: str
    grid_size: int
    features: dict[str, float]


@dataclass(frozen=True)
class NormalizedPlanetVector:
    """Population-normalized feature vector for one cipher x planet layer."""

    version: str
    name: str
    cipher: str
    planet: str
    kamea: str
    grid_size: int
    features: dict[str, float]
    raw_features: dict[str, float]
    normalization_mode: str
    calibration_size: int


@dataclass(frozen=True)
class CompositePlanetVector:
    """Composite vector for one planet across all available ciphers.

    The composite is the mean of the source ciphers' features. The fusion
    fields record how much the ciphers *agreed* before they were averaged, so a
    consumer can tell a value the three translations converged on from one they
    disagreed about. These are runtime-assembled (never persisted in the
    compiled artifact), so they are additive fields with confident defaults for
    the single-cipher case rather than a schema-version change.
    """

    version: str
    name: str
    planet: str
    features: dict[str, float]
    source_ciphers: list[str]
    source_count: int
    normalization_mode: str
    feature_agreement: dict[str, float] = field(default_factory=dict)
    agreement_score: float = 1.0
    completeness: float = 1.0
    confidence_score: float = 1.0


@dataclass(frozen=True)
class IdentityVector:
    """Canonical Identity Vector for one Atlas profile."""

    version: str
    name: str
    planets: dict[str, CompositePlanetVector]
    global_features: dict[str, float]
    quality: dict[str, float | int | str]
    diagnostics: dict[str, Any]


def planet_feature_vector_to_dict(
    vector: PlanetFeatureVector,
) -> dict[str, Any]:
    """Convert PlanetFeatureVector to JSON-safe dictionary."""
    return asdict(vector)


def normalized_planet_vector_to_dict(
    vector: NormalizedPlanetVector,
) -> dict[str, Any]:
    """Convert NormalizedPlanetVector to JSON-safe dictionary."""
    return asdict(vector)


def composite_planet_vector_to_dict(
    vector: CompositePlanetVector,
) -> dict[str, Any]:
    """Convert CompositePlanetVector to JSON-safe dictionary."""
    return asdict(vector)


def identity_vector_to_dict(
    vector: IdentityVector,
) -> dict[str, Any]:
    """Convert IdentityVector to JSON-safe dictionary."""
    data = asdict(vector)
    data["planets"] = {
        planet: composite_planet_vector_to_dict(planet_vector)
        for planet, planet_vector in vector.planets.items()
    }
    return data


def validate_feature_vector(vector: PlanetFeatureVector) -> bool:
    """Validate that a planet feature vector contains bounded metrics."""
    if vector.version != IVE_VERSION:
        return False

    return validate_bounded_features(vector.features, VECTOR_FEATURES)


def validate_normalized_vector(vector: NormalizedPlanetVector) -> bool:
    """Validate that a normalized vector contains bounded normalized metrics."""
    if vector.version != IVE_VERSION:
        return False

    if vector.calibration_size < 1:
        return False

    if not validate_bounded_features(vector.features, VECTOR_FEATURES):
        return False

    if not validate_bounded_features(vector.raw_features, VECTOR_FEATURES):
        return False

    return True


def validate_composite_vector(vector: CompositePlanetVector) -> bool:
    """Validate a composite planet vector."""
    if vector.version != IVE_VERSION:
        return False

    if vector.source_count < 1:
        return False

    if len(vector.source_ciphers) != vector.source_count:
        return False

    return validate_bounded_features(vector.features, VECTOR_FEATURES)


def validate_identity_vector(vector: IdentityVector) -> bool:
    """Validate a canonical IdentityVector."""
    if vector.version != IVE_VERSION:
        return False

    if len(vector.planets) != 7:
        return False

    for planet_vector in vector.planets.values():
        if not validate_composite_vector(planet_vector):
            return False

    if not validate_bounded_features(
        vector.global_features,
        IDENTITY_GLOBAL_FEATURES,
    ):
        return False

    return True


def validate_bounded_features(
    features: dict[str, float],
    required_features: list[str],
) -> bool:
    """Validate that required features are present and bounded."""
    for feature in required_features:
        if feature not in features:
            return False

        value = features[feature]

        if not isinstance(value, int | float):
            return False

        if value < 0.0 or value > 1.0:
            return False

    return True