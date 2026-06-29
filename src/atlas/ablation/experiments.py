"""Ablation experiment definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AblationExperiment:
    """Definition for one ablation experiment."""

    name: str
    description: str
    remove_prefixes: tuple[str, ...] = ()
    remove_suffixes: tuple[str, ...] = ()
    remove_contains: tuple[str, ...] = ()
    remove_columns: tuple[str, ...] = ()


def build_planet_experiments() -> list[AblationExperiment]:
    """Build one experiment per planet."""
    planets = [
        "saturn",
        "jupiter",
        "mars",
        "sun",
        "venus",
        "mercury",
        "moon",
    ]

    return [
        AblationExperiment(
            name=f"remove_{planet}",
            description=f"Remove all {planet.title()} features.",
            remove_prefixes=(f"{planet}_",),
        )
        for planet in planets
    ]


def build_feature_family_experiments() -> list[AblationExperiment]:
    """Build experiments for major feature families."""
    return [
        AblationExperiment(
            name="remove_coverage",
            description="Remove node and edge coverage features.",
            remove_contains=(
                "node_coverage",
                "edge_coverage",
            ),
        ),
        AblationExperiment(
            name="remove_entropy",
            description="Remove entropy and reduction entropy features.",
            remove_contains=(
                "entropy",
            ),
        ),
        AblationExperiment(
            name="remove_density",
            description="Remove density features.",
            remove_contains=(
                "density",
            ),
        ),
        AblationExperiment(
            name="remove_stability",
            description="Remove stability and survival features.",
            remove_contains=(
                "stability",
                "survival",
            ),
        ),
        AblationExperiment(
            name="remove_roles",
            description="Remove role-like topology features.",
            remove_contains=(
                "hub_ratio",
                "leaf_ratio",
                "loop_ratio",
                "bridge_ratio",
                "articulation_ratio",
            ),
        ),
        AblationExperiment(
            name="remove_axis",
            description="Remove axis strength features.",
            remove_contains=(
                "axis_strength",
            ),
        ),
        AblationExperiment(
            name="remove_global",
            description="Remove global aggregate features.",
            remove_prefixes=(
                "global_",
            ),
        ),
    ]


def all_default_experiments() -> list[AblationExperiment]:
    """Return all default ablation experiments."""
    return [
        *build_planet_experiments(),
        *build_feature_family_experiments(),
    ]