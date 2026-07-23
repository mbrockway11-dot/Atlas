"""Semantic feature registry for Atlas profile comparisons.

This module controls which corpus measurements may participate in structural
comparison. Selection is based on feature meaning, not merely numeric dtype.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


FEATURE_REGISTRY_VERSION = "atlas.comparison.features.v1"


PLANETS: tuple[str, ...] = (
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
)


@dataclass(frozen=True)
class FeatureRule:
    """One semantic comparison feature-family rule."""

    family: str
    prefixes: tuple[str, ...]
    contains: tuple[str, ...] = ()
    suffixes: tuple[str, ...] = ()
    weight: float = 1.0
    enabled: bool = True


FEATURE_RULES: tuple[FeatureRule, ...] = (
    FeatureRule(
        family="kamea_structure",
        prefixes=(
            "kamea_",
            "structural_",
        ),
        contains=(
            "average_degree",
            "average_path_length",
            "axiality",
            "branching_factor",
            "clustering_coefficient",
            "edge_density",
            "entropy",
            "graph_diameter",
            "hub_ratio",
            "loop_density",
            "node_coverage",
            "persistence_score",
            "revisit_intensity",
            "reflection_symmetry",
            "rotational_symmetry",
        ),
        weight=1.0,
    ),
    FeatureRule(
        family="planetary_topology",
        prefixes=tuple(f"{planet}_" for planet in PLANETS),
        contains=(
            "driver",
            "amplifier",
            "regulator",
            "density",
            "entropy",
            "symmetry",
            "motif",
            "coverage",
            "hub",
            "loop",
            "branch",
            "persistence",
            "revisit",
            "centrality",
            "diameter",
            "degree",
        ),
        weight=1.0,
    ),
    FeatureRule(
        family="cross_cipher_stability",
        prefixes=(
            "cipher_",
            "cross_cipher_",
            "topology_",
        ),
        contains=(
            "agreement",
            "similarity",
            "stability",
            "variance",
            "persistence",
            "dominance_gap",
            "inter_layer",
        ),
        weight=1.0,
    ),
    FeatureRule(
        family="resonance",
        prefixes=("resonance_",),
        contains=(
            "driver",
            "amplifier",
            "regulator",
            "density",
            "entropy",
            "symmetry",
            "motif",
            "bridge",
            "chain",
            "dead_end",
            "hub",
            "loop",
            "reciprocal",
        ),
        weight=0.8,
    ),
    FeatureRule(
        family="master_graph",
        prefixes=("master_graph_",),
        contains=(
            "node_count",
            "edge_count",
            "density",
            "weight",
            "aspect",
            "degree",
            "clustering",
            "diameter",
            "entropy",
        ),
        weight=0.8,
    ),
    FeatureRule(
        family="astronomy_structure",
        prefixes=("astronomy_",),
        contains=(
            "aspect_count",
            "aspect_edge_count",
            "body_count",
            "retrograde_count",
            "aspect_density",
            "orb_strength",
        ),
        weight=0.5,
    ),
)


EXCLUDED_PREFIXES: tuple[str, ...] = (
    "quality_",
    "diagnostic_",
    "metadata_",
    "compiler_",
    "runtime_",
    "timing_",
    "raw_",
)


EXCLUDED_SUFFIXES: tuple[str, ...] = (
    "_source_count",
    "_sequence_index",
    "_array_index",
    "_row_index",
    "_column_index",
    "_timestamp",
    "_elapsed_ms",
)


EXCLUDED_TERMS: tuple[str, ...] = (
    "longitude",
    "latitude",
    "declination",
    "right_ascension",
    "coordinate",
    "sequence_index",
    "array_index",
    "compiler_version",
    "elapsed_ms",
    "timestamp",
)


def normalize_feature_name(feature: str) -> str:
    """Normalize one corpus feature name for semantic matching."""

    return (
        str(feature)
        .strip()
        .lower()
        .replace(".", "_")
        .replace("::", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def feature_is_explicitly_excluded(feature: str) -> bool:
    """Return whether a feature is known comparison noise."""

    normalized = normalize_feature_name(feature)

    return (
        normalized.startswith(EXCLUDED_PREFIXES)
        or normalized.endswith(EXCLUDED_SUFFIXES)
        or any(term in normalized for term in EXCLUDED_TERMS)
    )


def matching_feature_rule(feature: str) -> FeatureRule | None:
    """Return the first enabled semantic rule matching a feature."""

    if feature_is_explicitly_excluded(feature):
        return None

    normalized = normalize_feature_name(feature)

    for rule in FEATURE_RULES:
        if not rule.enabled:
            continue

        prefix_match = bool(rule.prefixes) and normalized.startswith(rule.prefixes)
        contains_match = bool(rule.contains) and any(
            term in normalized for term in rule.contains
        )
        suffix_match = bool(rule.suffixes) and normalized.endswith(rule.suffixes)

        if prefix_match and (
            contains_match
            or suffix_match
            or (not rule.contains and not rule.suffixes)
        ):
            return rule

    return None


def feature_is_registered(feature: str) -> bool:
    """Return whether a feature is approved for structural comparison."""

    return matching_feature_rule(feature) is not None


def feature_family(feature: str) -> str | None:
    """Return the semantic family assigned to a feature."""

    rule = matching_feature_rule(feature)
    return rule.family if rule else None


def feature_weight(feature: str) -> float:
    """Return the configured semantic weight for a feature."""

    rule = matching_feature_rule(feature)
    return float(rule.weight) if rule else 0.0


def registered_features(features: Iterable[str]) -> list[str]:
    """Filter feature names through the semantic registry."""

    return [
        feature
        for feature in features
        if feature_is_registered(feature)
    ]


def infer_planet_from_feature_name(feature: str) -> str | None:
    """Infer a planet from common flattened naming styles."""

    normalized = normalize_feature_name(feature)
    tokens = set(normalized.split("_"))

    for planet in PLANETS:
        if planet in tokens or normalized.startswith(f"{planet}_"):
            return planet.title()

    return None
