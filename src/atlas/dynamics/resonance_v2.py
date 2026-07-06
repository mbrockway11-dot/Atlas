
"""Dynamic Resonance v2.

Compares two profiles by dynamic field behavior:
recurrence, attractor basins, directed currents, transition energy,
field density, and predicted recovery response.
"""

from __future__ import annotations

from typing import Any

from atlas.dynamics import build_unified_dynamics_report


RESONANCE_V2_VERSION = "2.0.0"


def build_dynamic_resonance_v2(
    left_payload: dict[str, Any],
    right_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build Dynamic Resonance v2 comparison."""
    left = left_payload.get("dynamics") or build_unified_dynamics_report(left_payload)
    right = right_payload.get("dynamics") or build_unified_dynamics_report(right_payload)

    left_profile = left.get("dynamic_profile", {}) or {}
    right_profile = right.get("dynamic_profile", {}) or {}

    left_field = left.get("identity_field", {}) or {}
    right_field = right.get("identity_field", {}) or {}

    left_prediction = left.get("prediction", {}) or {}
    right_prediction = right.get("prediction", {}) or {}

    components = {
        "recurrence": recurrence_similarity(left_profile, right_profile),
        "energy": energy_similarity(left_profile, right_profile),
        "attractor_density": attractor_density_similarity(left_profile, right_profile),
        "field_density": field_density_similarity(left_field, right_field),
        "attractor_overlap": attractor_overlap(left_field, right_field),
        "current_overlap": current_overlap(left_field, right_field),
        "recovery_response": recovery_response_similarity(left_prediction, right_prediction),
    }

    score = weighted_score(
        components,
        {
            "recurrence": 0.18,
            "energy": 0.14,
            "attractor_density": 0.16,
            "field_density": 0.10,
            "attractor_overlap": 0.18,
            "current_overlap": 0.14,
            "recovery_response": 0.10,
        },
    )

    return {
        "success": True,
        "version": RESONANCE_V2_VERSION,
        "left_profile_key": left_payload.get("profile_key"),
        "right_profile_key": right_payload.get("profile_key"),
        "dynamic_resonance": round(score, 6),
        "label": resonance_label(score),
        "component_scores": {
            key: round(value, 6)
            for key, value in components.items()
        },
        "shared": build_shared_dynamic_features(left, right),
        "differences": build_dynamic_differences(left, right),
        "narrative": build_resonance_narrative(left_payload, right_payload, score, components),
    }


def recurrence_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compare recurrence ratios."""
    return bounded_inverse_distance(
        float(left.get("recurrence") or 0.0),
        float(right.get("recurrence") or 0.0),
    )


def energy_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compare mean transition energy."""
    return inverse_scale_distance(
        float(left.get("mean_energy") or 0.0),
        float(right.get("mean_energy") or 0.0),
    )


def attractor_density_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compare attractor density."""
    return inverse_scale_distance(
        float(left.get("attractor_density") or 0.0),
        float(right.get("attractor_density") or 0.0),
    )


def field_density_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compare field density."""
    return inverse_scale_distance(
        float(left.get("field_density") or 0.0),
        float(right.get("field_density") or 0.0),
    )


def attractor_overlap(left_field: dict[str, Any], right_field: dict[str, Any]) -> float:
    """Compare dominant attractor nodes."""
    left_nodes = {
        str(item.get("node"))
        for item in left_field.get("dominant_attractors", []) or []
        if item.get("node") is not None
    }
    right_nodes = {
        str(item.get("node"))
        for item in right_field.get("dominant_attractors", []) or []
        if item.get("node") is not None
    }

    return jaccard(left_nodes, right_nodes)


def current_overlap(left_field: dict[str, Any], right_field: dict[str, Any]) -> float:
    """Compare dominant directed currents."""
    left_edges = {
        str(item.get("edge"))
        for item in left_field.get("dominant_currents", []) or []
        if item.get("edge") is not None
    }
    right_edges = {
        str(item.get("edge"))
        for item in right_field.get("dominant_currents", []) or []
        if item.get("edge") is not None
    }

    return jaccard(left_edges, right_edges)


def recovery_response_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compare predicted recovery behavior."""
    mode_score = 1.0 if left.get("likely_dynamic_response") == right.get("likely_dynamic_response") else 0.0

    recovery_score = bounded_inverse_distance(
        float(left.get("recovery_probability") or 0.0),
        float(right.get("recovery_probability") or 0.0),
    )

    sensitivity_score = bounded_inverse_distance(
        float(left.get("perturbation_sensitivity") or 0.0),
        float(right.get("perturbation_sensitivity") or 0.0),
    )

    return mode_score * 0.45 + recovery_score * 0.35 + sensitivity_score * 0.20


def build_shared_dynamic_features(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Build shared dynamic features."""
    left_field = left.get("identity_field", {}) or {}
    right_field = right.get("identity_field", {}) or {}

    left_attractors = {
        str(item.get("node"))
        for item in left_field.get("dominant_attractors", []) or []
        if item.get("node") is not None
    }
    right_attractors = {
        str(item.get("node"))
        for item in right_field.get("dominant_attractors", []) or []
        if item.get("node") is not None
    }

    left_currents = {
        str(item.get("edge"))
        for item in left_field.get("dominant_currents", []) or []
        if item.get("edge") is not None
    }
    right_currents = {
        str(item.get("edge"))
        for item in right_field.get("dominant_currents", []) or []
        if item.get("edge") is not None
    }

    return {
        "attractors": sorted(left_attractors & right_attractors),
        "currents": sorted(left_currents & right_currents),
        "same_flow_stability": (
            (left.get("dynamic_profile", {}) or {}).get("flow_stability")
            == (right.get("dynamic_profile", {}) or {}).get("flow_stability")
        ),
        "same_phase_complexity": (
            (left.get("dynamic_profile", {}) or {}).get("phase_complexity")
            == (right.get("dynamic_profile", {}) or {}).get("phase_complexity")
        ),
        "same_response_mode": (
            (left.get("prediction", {}) or {}).get("likely_dynamic_response")
            == (right.get("prediction", {}) or {}).get("likely_dynamic_response")
        ),
    }


def build_dynamic_differences(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Build dynamic difference summary."""
    lp = left.get("dynamic_profile", {}) or {}
    rp = right.get("dynamic_profile", {}) or {}

    pred_left = left.get("prediction", {}) or {}
    pred_right = right.get("prediction", {}) or {}

    return {
        "recurrence_delta": round(float(lp.get("recurrence") or 0.0) - float(rp.get("recurrence") or 0.0), 6),
        "mean_energy_delta": round(float(lp.get("mean_energy") or 0.0) - float(rp.get("mean_energy") or 0.0), 6),
        "attractor_density_delta": round(float(lp.get("attractor_density") or 0.0) - float(rp.get("attractor_density") or 0.0), 6),
        "recovery_probability_delta": round(
            float(pred_left.get("recovery_probability") or 0.0)
            - float(pred_right.get("recovery_probability") or 0.0),
            6,
        ),
        "perturbation_sensitivity_delta": round(
            float(pred_left.get("perturbation_sensitivity") or 0.0)
            - float(pred_right.get("perturbation_sensitivity") or 0.0),
            6,
        ),
    }


def build_resonance_narrative(
    left_payload: dict[str, Any],
    right_payload: dict[str, Any],
    score: float,
    components: dict[str, float],
) -> dict[str, Any]:
    """Build narrative explanation."""
    left_key = left_payload.get("profile_key", "left profile")
    right_key = right_payload.get("profile_key", "right profile")

    strongest = sorted(
        components.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:3]

    weakest = sorted(
        components.items(),
        key=lambda item: item[1],
    )[:3]

    return {
        "headline": f"{left_key} and {right_key}: {resonance_label(score)}",
        "summary": (
            f"Dynamic Resonance v2 compares how both profiles move through their symbolic fields. "
            f"The total resonance score is {score:.3f}. Strongest shared dynamics: "
            f"{', '.join(name for name, _ in strongest)}."
        ),
        "strongest_components": [
            {"component": name, "score": round(value, 6)}
            for name, value in strongest
        ],
        "weakest_components": [
            {"component": name, "score": round(value, 6)}
            for name, value in weakest
        ],
        "interpretation": resonance_interpretation(score),
    }


def resonance_interpretation(score: float) -> str:
    """Interpret resonance score."""
    if score >= 0.82:
        return "The profiles appear to move through their symbolic fields in highly similar ways."
    if score >= 0.62:
        return "The profiles share meaningful dynamic behavior, though their currents or attractors may differ."
    if score >= 0.42:
        return "The profiles show limited dynamic resonance; some field behaviors overlap but the total motion differs."
    return "The profiles appear dynamically dissonant, with different recurrence, attractor, or recovery patterns."


def weighted_score(values: dict[str, float], weights: dict[str, float]) -> float:
    """Compute weighted score."""
    total_weight = sum(weights.values()) or 1.0
    return sum(values.get(key, 0.0) * weight for key, weight in weights.items()) / total_weight


def bounded_inverse_distance(left: float, right: float) -> float:
    """Similarity for values naturally in 0..1."""
    return max(0.0, min(1.0, 1.0 - abs(left - right)))


def inverse_scale_distance(left: float, right: float) -> float:
    """Similarity for open-scale positive values."""
    return 1.0 / (1.0 + abs(left - right))


def jaccard(left: set[str], right: set[str]) -> float:
    """Jaccard similarity."""
    if not left and not right:
        return 0.0

    return len(left & right) / max(1, len(left | right))


def resonance_label(score: float) -> str:
    """Label dynamic resonance."""
    if score >= 0.82:
        return "high_dynamic_resonance"
    if score >= 0.62:
        return "moderate_dynamic_resonance"
    if score >= 0.42:
        return "low_dynamic_resonance"
    return "dynamic_dissonance"
