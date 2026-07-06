
"""Unified Dynamics report builder."""

from __future__ import annotations

from typing import Any

from atlas.dynamics.evidence import build_dynamics_evidence
from atlas.dynamics.field import build_identity_field
from atlas.dynamics.integration import build_dynamic_signature
from atlas.dynamics.prediction import build_dynamic_prediction
from atlas.dynamics.profile_signature import build_profile_dynamic_signature
from atlas.dynamics.reasoning import build_dynamics_reasoning


DYNAMICS_REPORT_VERSION = "1.0.0"


def build_unified_dynamics_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build full Unified Dynamics report."""
    signature = build_dynamic_signature(payload)
    field = build_identity_field(signature)
    dynamic_profile = build_profile_dynamic_signature(signature)
    evidence = build_dynamics_evidence(signature)
    reasoning = build_dynamics_reasoning(dynamic_profile)
    prediction = build_dynamic_prediction(dynamic_profile)

    return {
        "success": True,
        "version": DYNAMICS_REPORT_VERSION,
        "profile_key": payload.get("profile_key"),
        "dynamic_signature": signature,
        "identity_field": field,
        "dynamic_profile": dynamic_profile,
        "evidence": evidence,
        "reasoning": reasoning,
        "prediction": prediction,
        "summary": build_summary(dynamic_profile, reasoning, prediction),
    }


def build_summary(
    dynamic_profile: dict[str, Any],
    reasoning: dict[str, Any],
    prediction: dict[str, Any],
) -> str:
    """Build summary."""
    return (
        f"Unified Dynamics identifies this profile as {dynamic_profile.get('flow_stability')} "
        f"with {dynamic_profile.get('phase_complexity')}. "
        f"It generated {reasoning.get('inference_count', 0)} dynamic inference(s). "
        f"Predicted response mode: {prediction.get('likely_dynamic_response')}."
    )
