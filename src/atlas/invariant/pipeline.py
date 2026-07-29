"""Strict invariant structural analysis pipeline."""

from __future__ import annotations

from statistics import pstdev
from typing import Any

from atlas.ciphers import run_all_ciphers
from atlas.invariant.features import (
    extract_invariant_features,
    invariant_features_to_dict,
)
from atlas.invariant.subtype import (
    classify_invariant_subtype,
    invariant_subtype_to_dict,
)
from atlas.kamea.path_views import build_kamea_path_views
from atlas.kamea.projection import project_values_to_kamea


KAMEA_SIZES: dict[str, int] = {
    "saturn": 3,
    "jupiter": 4,
    "mars": 5,
    "sun": 6,
    "venus": 7,
    "mercury": 8,
    "moon": 9,
}


KAMEA_DISPLAY_NAMES: dict[str, str] = {
    "saturn": "Saturn",
    "jupiter": "Jupiter",
    "mars": "Mars",
    "sun": "Sun",
    "venus": "Venus",
    "mercury": "Mercury",
    "moon": "Moon",
}


PLANETARY_FUNCTIONS: dict[str, str] = {
    "Sun": "dominant node weight",
    "Saturn": "self-loops",
    "Jupiter": "node degree",
    "Mercury": "edge frequency",
    "Mars": "abrupt transitions",
    "Venus": "clustering / cohesion",
    "Moon": "entropy",
}


def run_invariant_pipeline(name: str) -> dict[str, Any]:
    """Run strict invariant analysis for all ciphers and kameas."""
    normalized = normalize_input(name)
    cipher_results = run_all_ciphers(name)

    analyses = []

    for cipher_name, values in cipher_results.items():
        for kamea_key, grid_size in KAMEA_SIZES.items():
            planet = KAMEA_DISPLAY_NAMES[kamea_key]

            path = project_values_to_kamea(
                values,
                kamea_key,
                use_planetary_transform=True,
            )

            path_views = build_kamea_path_views(path)
            features = extract_invariant_features(path, grid_size)
            subtype = classify_invariant_subtype(features)

            analyses.append(
                {
                    "cipher": cipher_name,
                    "planet": planet,
                    "kamea": kamea_key,
                    "grid_size": grid_size,
                    "sequence": {
                        "length": len(values),
                        "sum": sum(values),
                        "repetition": _repetition_count(values),
                        "values": values,
                        "planetary_reduced_values": list(path.reduced_values),
                    },
                    "path_views": path_views,
                    "features": invariant_features_to_dict(features),
                    "subtype": invariant_subtype_to_dict(subtype),
                    "kamea_score": score_kamea(
                        features=features,
                        grid_size=grid_size,
                        path_length=len(values),
                    ),
                    "planetary_function": PLANETARY_FUNCTIONS[planet],
                }
            )

    planetary_weights = build_planetary_weight_distribution(analyses)
    planetary_contrast = build_planetary_contrast_distribution(analyses)
    ranked_kameas = rank_kameas(analyses)
    consensus_subtype = build_consensus_subtype(analyses)

    return {
        "name": name,
        "normalized": normalized,
        "analysis_count": len(analyses),
        "sequences": build_sequence_summary(cipher_results),
        "analyses": analyses,
        "top_kameas": ranked_kameas[:3],
        "ranked_kameas": ranked_kameas,
        "subtype": consensus_subtype,
        "planetary_weights": planetary_weights,
        "planetary_contrast": planetary_contrast,
        "structural_summary": build_structural_summary(
            consensus_subtype,
            ranked_kameas,
            planetary_weights,
            planetary_contrast,
        ),
    }


def normalize_input(value: str) -> str:
    """Normalize input according to strict pipeline rules."""
    return "".join(
        character
        for character in value.upper()
        if character.isalnum()
    )


def build_sequence_summary(
    cipher_results: dict[str, list[int]],
) -> dict[str, Any]:
    """Build sequence summary for all ciphers."""
    return {
        cipher_name: {
            "length": len(values),
            "sum": sum(values),
            "repetition": _repetition_count(values),
            "values": values,
        }
        for cipher_name, values in cipher_results.items()
    }


def score_kamea(features, grid_size: int, path_length: int) -> float:
    """Score kamea strength with grid-size normalization.

    This corrects small-grid compression bias, especially Saturn 3x3 dominance.
    """
    grid_capacity = grid_size * grid_size

    active_nodes = len(features.node_weights)
    active_edges = len(features.edge_weights)

    node_coverage = active_nodes / grid_capacity if grid_capacity else 0.0
    edge_capacity = grid_capacity * max(grid_capacity - 1, 1)
    edge_coverage = active_edges / edge_capacity if edge_capacity else 0.0

    mean_node_weight = _mean(features.node_weights.values())
    mean_edge_weight = _mean(features.edge_weights.values())
    mean_degree = _mean(features.degrees.values())

    normalized_node_activity = mean_node_weight * node_coverage
    normalized_edge_activity = mean_edge_weight * edge_coverage
    normalized_degree_activity = mean_degree / max(path_length, 1)

    persistence = features.axis_strength
    loop_rate = features.self_loops / max(path_length - 1, 1)

    raw_score = (
        normalized_node_activity
        + normalized_edge_activity
        + normalized_degree_activity
        + persistence
    ) / 4.0

    loop_penalty = loop_rate * 0.25

    return max(0.0, raw_score - loop_penalty)


def rank_kameas(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank kameas by average invariant score across ciphers."""
    grouped: dict[str, list[float]] = {}

    for analysis in analyses:
        planet = analysis["planet"]
        grouped.setdefault(planet, [])
        grouped[planet].append(analysis["kamea_score"])

    raw_scores = {
        planet: _mean(scores)
        for planet, scores in grouped.items()
    }

    contrast = _z_score_distribution(raw_scores)

    ranked = [
        {
            "planet": planet,
            "score": raw_scores[planet],
            "z_score": contrast[planet],
        }
        for planet in raw_scores
    ]

    return sorted(
        ranked,
        key=lambda item: item["z_score"],
        reverse=True,
    )


def build_planetary_weight_distribution(
    analyses: list[dict[str, Any]],
) -> dict[str, float]:
    """Build normalized planetary weight distribution."""
    grouped: dict[str, list[float]] = {}

    for analysis in analyses:
        grouped.setdefault(analysis["planet"], [])
        grouped[analysis["planet"]].append(analysis["kamea_score"])

    raw = {
        planet: _mean(scores)
        for planet, scores in grouped.items()
    }

    total = sum(raw.values())

    if total == 0:
        return {
            planet: 0.0
            for planet in raw
        }

    return {
        planet: value / total
        for planet, value in raw.items()
    }


def build_planetary_contrast_distribution(
    analyses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build raw, delta, and z-score contrast distribution by planet."""
    grouped: dict[str, list[float]] = {}

    for analysis in analyses:
        grouped.setdefault(analysis["planet"], [])
        grouped[analysis["planet"]].append(analysis["kamea_score"])

    raw_scores = {
        planet: _mean(scores)
        for planet, scores in grouped.items()
    }

    mean_score = _mean(raw_scores.values())
    z_scores = _z_score_distribution(raw_scores)

    ranked = sorted(
        [
            {
                "planet": planet,
                "raw_score": raw_score,
                "delta_from_mean": raw_score - mean_score,
                "z_score": z_scores[planet],
            }
            for planet, raw_score in raw_scores.items()
        ],
        key=lambda item: item["z_score"],
        reverse=True,
    )

    top = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None

    dominance_gap = (
        top["z_score"] - second["z_score"]
        if top and second
        else 0.0
    )

    return {
        "raw_scores": raw_scores,
        "mean_score": mean_score,
        "z_scores": z_scores,
        "ranked": ranked,
        "dominance_gap": dominance_gap,
        "is_distinct_motion_profile": dominance_gap >= 0.25,
    }


def build_consensus_subtype(
    analyses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build consensus subtype from all invariant analyses."""
    subtype_scores: dict[str, list[float]] = {}

    for analysis in analyses:
        for subtype_name, score in analysis["subtype"]["scores"].items():
            subtype_scores.setdefault(subtype_name, [])
            subtype_scores[subtype_name].append(score)

    averaged = {
        subtype_name: _mean(scores)
        for subtype_name, scores in subtype_scores.items()
    }

    ranked = sorted(
        averaged.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "primary_type": ranked[0][0],
        "secondary_modifier": ranked[1][0],
        "scores": averaged,
        "ranked": [
            {
                "type": item[0],
                "score": item[1],
            }
            for item in ranked
        ],
    }


def build_planetary_differential(
    ranked_kameas: list[dict[str, Any]],
) -> dict[str, Any]:
    """Top-3 vs bottom-4 activity differential ("the stack vs the background").

    Splits the seven ranked kameas into the three most-active (the profile's
    dominant stack) and the four least-active, and measures how sharply the
    stack stands out. A large differential is a *peaked* profile carried by a
    few planets; near zero is a *flat*, evenly balanced one. Reported on both
    the raw kamea score and the within-profile z-score.

    CAVEAT (measured over the corpus): the *magnitude* varies per profile
    (CoV ~0.23), but the *identity* of the top-3 does not -- ``kamea_score`` is
    not normalized across grid size, so the smallest squares (Saturn 3x3,
    Jupiter 4x4, Mars 5x5) score highest and land in the top-3 for ~95% of
    profiles, with Saturn ranked first for essentially everyone. So the raw
    differential conflates real peakedness with a grid-size scale bias. To make
    *which* planets are active discriminate, rank by a per-planet
    population-relative score (as the identity vector normalizes within
    cipher x planet) rather than the raw kamea score.
    """
    if len(ranked_kameas) < 4:
        return {
            "top_planets": [item["planet"] for item in ranked_kameas],
            "bottom_planets": [],
            "top_mean_score": _mean(item["score"] for item in ranked_kameas),
            "bottom_mean_score": 0.0,
            "score_differential": 0.0,
            "z_differential": 0.0,
        }

    top = ranked_kameas[:3]
    bottom = ranked_kameas[3:]
    top_score = _mean(item["score"] for item in top)
    bottom_score = _mean(item["score"] for item in bottom)

    return {
        "top_planets": [item["planet"] for item in top],
        "bottom_planets": [item["planet"] for item in bottom],
        "top_mean_score": top_score,
        "bottom_mean_score": bottom_score,
        "score_differential": top_score - bottom_score,
        "z_differential": (
            _mean(item["z_score"] for item in top)
            - _mean(item["z_score"] for item in bottom)
        ),
    }


def build_structural_summary(
    subtype: dict[str, Any],
    ranked_kameas: list[dict[str, Any]],
    planetary_weights: dict[str, float],
    planetary_contrast: dict[str, Any],
) -> dict[str, Any]:
    """Build strict structural summary."""
    top_planets = [
        item["planet"]
        for item in ranked_kameas[:3]
    ]

    strongest_planet = top_planets[0] if top_planets else None

    return {
        "subtype_statement": (
            f"{subtype['primary_type']} with "
            f"{subtype['secondary_modifier']} modifier."
        ),
        "strongest_planet": strongest_planet,
        "top_planets": top_planets,
        "planetary_weights": planetary_weights,
        "planetary_contrast": planetary_contrast,
        "planetary_differential": build_planetary_differential(ranked_kameas),
    }


def _z_score_distribution(raw_scores: dict[str, float]) -> dict[str, float]:
    """Convert raw score dictionary to z-score contrast dictionary."""
    if not raw_scores:
        return {}

    values = list(raw_scores.values())
    mean_value = _mean(values)
    deviation = pstdev(values)

    if deviation == 0:
        return {
            key: 0.0
            for key in raw_scores
        }

    return {
        key: (value - mean_value) / deviation
        for key, value in raw_scores.items()
    }


def _repetition_count(values: list[int]) -> int:
    """Count repeated values beyond first occurrence."""
    return len(values) - len(set(values))


def _mean(values) -> float:
    """Mean helper."""
    values = list(values)

    if not values:
        return 0.0

    return sum(values) / len(values)