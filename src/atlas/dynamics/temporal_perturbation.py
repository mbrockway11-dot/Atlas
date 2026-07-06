
"""Temporal Perturbation Engine.

Applies temporal/current-state pressure to a profile's Unified Dynamics field
and predicts how recovery, sensitivity, attractors, and response mode shift.
"""

from __future__ import annotations

from typing import Any

from atlas.dynamics import build_unified_dynamics_report


PERTURBATION_VERSION = "1.0.0"


DEFAULT_PRESSURE = {
    "time_pressure": 0.0,
    "visibility": 0.0,
    "novelty": 0.0,
    "uncertainty": 0.0,
    "conflict": 0.0,
    "fatigue": 0.0,
    "complexity": 0.0,
    "resource_constraint": 0.0,
}


def build_temporal_perturbation_report(
    payload: dict[str, Any],
    *,
    pressure: dict[str, float] | None = None,
    label: str = "current_temporal_field",
) -> dict[str, Any]:
    """Build temporal perturbation report."""
    dynamics = payload.get("dynamics") or build_unified_dynamics_report(payload)
    dynamic_profile = dynamics.get("dynamic_profile", {}) or {}
    prediction = dynamics.get("prediction", {}) or {}
    identity_field = dynamics.get("identity_field", {}) or {}

    active_pressure = normalize_pressure(pressure or {})
    pressure_load = compute_pressure_load(active_pressure)
    pressure_vector = classify_pressure_vector(active_pressure)

    baseline = {
        "recovery_probability": float(prediction.get("recovery_probability") or 0.0),
        "perturbation_sensitivity": float(prediction.get("perturbation_sensitivity") or 0.0),
        "recurrence": float(dynamic_profile.get("recurrence") or 0.0),
        "mean_energy": float(dynamic_profile.get("mean_energy") or 0.0),
        "attractor_density": float(dynamic_profile.get("attractor_density") or 0.0),
    }

    perturbed = perturb_baseline(
        baseline,
        active_pressure,
        pressure_load,
    )

    attractor_shift = estimate_attractor_shift(
        identity_field,
        active_pressure,
        pressure_load,
    )

    response = classify_perturbed_response(perturbed, pressure_vector)

    return {
        "success": True,
        "version": PERTURBATION_VERSION,
        "profile_key": payload.get("profile_key"),
        "label": label,
        "pressure": active_pressure,
        "pressure_load": round(pressure_load, 6),
        "pressure_vector": pressure_vector,
        "baseline": baseline,
        "perturbed": perturbed,
        "deltas": build_deltas(baseline, perturbed),
        "attractor_shift": attractor_shift,
        "response": response,
        "summary": build_summary(payload.get("profile_key"), pressure_load, pressure_vector, response),
    }


def normalize_pressure(pressure: dict[str, float]) -> dict[str, float]:
    """Normalize pressure values to 0..1."""
    merged = dict(DEFAULT_PRESSURE)
    merged.update(pressure or {})

    return {
        key: clamp01(value)
        for key, value in merged.items()
    }


def compute_pressure_load(pressure: dict[str, float]) -> float:
    """Compute weighted pressure load."""
    weights = {
        "time_pressure": 0.14,
        "visibility": 0.12,
        "novelty": 0.12,
        "uncertainty": 0.14,
        "conflict": 0.13,
        "fatigue": 0.13,
        "complexity": 0.13,
        "resource_constraint": 0.09,
    }

    total = sum(weights.values()) or 1.0
    return sum(pressure.get(key, 0.0) * weight for key, weight in weights.items()) / total


def classify_pressure_vector(pressure: dict[str, float]) -> str:
    """Classify dominant pressure vector."""
    top_key = max(pressure, key=lambda key: pressure.get(key, 0.0))
    top_value = pressure.get(top_key, 0.0)

    if top_value < 0.25:
        return "low_perturbation"

    return {
        "time_pressure": "compression_pressure",
        "visibility": "exposure_pressure",
        "novelty": "novelty_pressure",
        "uncertainty": "ambiguity_pressure",
        "conflict": "friction_pressure",
        "fatigue": "depletion_pressure",
        "complexity": "complexity_pressure",
        "resource_constraint": "constraint_pressure",
    }.get(top_key, "mixed_pressure")


def perturb_baseline(
    baseline: dict[str, float],
    pressure: dict[str, float],
    pressure_load: float,
) -> dict[str, Any]:
    """Apply pressure to baseline dynamics."""
    sensitivity = baseline["perturbation_sensitivity"]
    recurrence = baseline["recurrence"]
    attractor_density = baseline["attractor_density"]

    destabilizing = (
        pressure.get("uncertainty", 0.0) * 0.22
        + pressure.get("conflict", 0.0) * 0.20
        + pressure.get("fatigue", 0.0) * 0.20
        + pressure.get("novelty", 0.0) * 0.14
        + pressure.get("time_pressure", 0.0) * 0.14
        + pressure.get("complexity", 0.0) * 0.10
    )

    stabilizing_capacity = min(1.0, recurrence * 0.45 + min(0.35, attractor_density / 10))

    sensitivity_shift = pressure_load * (0.35 + sensitivity * 0.45)
    recovery_shift = destabilizing * (0.30 + sensitivity * 0.30) - stabilizing_capacity * 0.22

    energy_shift = pressure_load * (1.0 + pressure.get("complexity", 0.0) * 0.65)
    recurrence_shift = (
        pressure.get("time_pressure", 0.0) * 0.08
        + pressure.get("conflict", 0.0) * 0.06
        - pressure.get("novelty", 0.0) * 0.04
    )

    perturbed_recovery = clamp01(baseline["recovery_probability"] - recovery_shift)
    perturbed_sensitivity = clamp01(sensitivity + sensitivity_shift)
    perturbed_recurrence = clamp01(recurrence + recurrence_shift)
    perturbed_energy = max(0.0, baseline["mean_energy"] + energy_shift)

    return {
        "recovery_probability": round(perturbed_recovery, 6),
        "perturbation_sensitivity": round(perturbed_sensitivity, 6),
        "recurrence": round(perturbed_recurrence, 6),
        "mean_energy": round(perturbed_energy, 6),
        "attractor_density": round(attractor_density, 6),
    }


def estimate_attractor_shift(
    identity_field: dict[str, Any],
    pressure: dict[str, float],
    pressure_load: float,
) -> dict[str, Any]:
    """Estimate attractor stability/shift under pressure."""
    attractors = identity_field.get("dominant_attractors", []) or []
    currents = identity_field.get("dominant_currents", []) or []

    shift_strength = clamp01(
        pressure_load * 0.55
        + pressure.get("novelty", 0.0) * 0.20
        + pressure.get("uncertainty", 0.0) * 0.15
        + pressure.get("conflict", 0.0) * 0.10
    )

    stable_count = max(0, int(round(len(attractors) * (1.0 - shift_strength))))
    activated_count = min(len(currents), int(round(len(currents) * shift_strength)))

    return {
        "shift_strength": round(shift_strength, 6),
        "stability_label": attractor_stability_label(shift_strength),
        "stable_attractors": attractors[:stable_count],
        "activated_currents": currents[:activated_count],
        "dominant_attractor_count": len(attractors),
        "activated_current_count": activated_count,
    }


def classify_perturbed_response(
    perturbed: dict[str, Any],
    pressure_vector: str,
) -> dict[str, Any]:
    """Classify perturbed response."""
    recovery = float(perturbed.get("recovery_probability") or 0.0)
    sensitivity = float(perturbed.get("perturbation_sensitivity") or 0.0)
    recurrence = float(perturbed.get("recurrence") or 0.0)

    if recovery >= 0.70 and sensitivity >= 0.65:
        mode = "activated_recovery_loop"
    elif recovery >= 0.70:
        mode = "stable_basin_recovery"
    elif recovery < 0.50 and sensitivity >= 0.65:
        mode = "flow_disruption_risk"
    elif recurrence >= 0.35:
        mode = "recursive_compensation"
    else:
        mode = "adaptive_reorientation"

    return {
        "mode": mode,
        "pressure_vector": pressure_vector,
        "interpretation": response_interpretation(mode),
    }


def build_deltas(
    baseline: dict[str, float],
    perturbed: dict[str, Any],
) -> dict[str, float]:
    """Build baseline-to-perturbed deltas."""
    return {
        key: round(float(perturbed.get(key) or 0.0) - float(baseline.get(key) or 0.0), 6)
        for key in baseline
        if key in perturbed
    }


def attractor_stability_label(shift: float) -> str:
    """Label attractor shift."""
    if shift >= 0.70:
        return "major_attractor_shift"
    if shift >= 0.45:
        return "moderate_attractor_shift"
    if shift >= 0.25:
        return "mild_attractor_shift"
    return "stable_attractor_field"


def response_interpretation(mode: str) -> str:
    """Explain response mode."""
    return {
        "activated_recovery_loop": "The field becomes more activated under pressure but still retains a recovery path.",
        "stable_basin_recovery": "The field is likely to absorb perturbation and return to a stable basin.",
        "flow_disruption_risk": "The field may leave its normal recovery basin and require external stabilization.",
        "recursive_compensation": "The field may compensate by returning repeatedly to familiar attractors.",
        "adaptive_reorientation": "The field may seek a new orientation rather than returning through established basins.",
    }.get(mode, "The response is mixed or unresolved.")


def build_summary(
    profile_key: str | None,
    pressure_load: float,
    pressure_vector: str,
    response: dict[str, Any],
) -> str:
    """Build plain-English summary."""
    return (
        f"Temporal Perturbation modeled {profile_key or 'profile'} under {pressure_vector} "
        f"with pressure load {pressure_load:.3f}. Predicted response: {response.get('mode')}."
    )


def clamp01(value: Any) -> float:
    """Clamp numeric value to 0..1."""
    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0

    return max(0.0, min(1.0, numeric))
