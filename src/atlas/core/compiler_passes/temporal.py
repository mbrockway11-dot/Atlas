"""Temporal seed pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import TemporalLayer
from atlas.core.compiler_passes.utils import extract_acf, extract_temporal, first_dict


def build_temporal_layer(*, profile_payload: dict[str, Any]) -> TemporalLayer:
    """Build CSS temporal layer from saved profile payload."""
    temporal = extract_temporal(profile_payload)

    birth = {
        "birth_date": profile_payload.get("birth_date"),
        "birth_time": profile_payload.get("birth_time"),
        "birth_place": profile_payload.get("birth_place"),
        "birth_location": profile_payload.get("birth_location"),
    }
    birth = {key: value for key, value in birth.items() if value is not None}

    acf = extract_acf(profile_payload)
    planetary_matrix = first_dict(
        profile_payload.get("planetary_matrix"),
        acf.get("planetary_matrix"),
    )

    natal = first_dict(
        temporal.get("natal"),
        temporal.get("natal_chart"),
        profile_payload.get("natal"),
        profile_payload.get("natal_chart"),
    )

    if birth or planetary_matrix:
        natal = {
            **natal,
            "birth": birth,
            "planetary_matrix": planetary_matrix,
            "temporal_status": "seed_from_saved_profile",
        }

    transits = first_dict(
        temporal.get("transits"),
        temporal.get("transit"),
        profile_payload.get("transits"),
        profile_payload.get("transit"),
    )

    dasha = first_dict(
        temporal.get("dasha"),
        temporal.get("vimshottari_dasha"),
        temporal.get("dashas"),
        profile_payload.get("dasha"),
        profile_payload.get("vimshottari_dasha"),
        profile_payload.get("dashas"),
    )

    calibration = first_dict(
        temporal.get("calibration"),
        profile_payload.get("calibration"),
    )

    return TemporalLayer(
        natal=natal,
        transits=transits,
        dasha=dasha,
        calibration=calibration,
    )