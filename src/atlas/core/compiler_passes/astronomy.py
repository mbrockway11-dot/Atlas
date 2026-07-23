"""Physical astronomy pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.astronomy import build_physical_astronomy
from atlas.core.canonical_structural_signature import AstronomyLayer
from atlas.core.compiler_passes.temporal import (
    build_birth_seed,
    is_time_known,
    safe_float_or_none,
    safe_int,
)
from atlas.temporal.models import BirthData


def build_astronomy_layer(*, profile_payload: dict[str, Any]) -> AstronomyLayer:
    birth = build_birth_seed(profile_payload)
    if not birth.get("birth_date"):
        return AstronomyLayer()
    birth_time = str(birth.get("birth_time") or "12:00")
    try:
        measurement = build_physical_astronomy(BirthData(
            name=str(birth.get("name") or ""),
            birth_date=str(birth["birth_date"]),
            birth_time=birth_time,
            birth_place=str(
                birth.get("birth_place") or birth.get("birth_location") or ""
            ),
            latitude=safe_float_or_none(birth.get("latitude")),
            longitude=safe_float_or_none(birth.get("longitude")),
            timezone=str(birth.get("timezone") or ""),
            source_file=str(birth.get("source_file") or ""),
            row_number=safe_int(birth.get("row_number")),
            time_known=is_time_known(birth_time),
        ))
    except Exception as exc:
        return AstronomyLayer(measurements={
            "success": False,
            "error": str(exc),
            "interpretation_applied": False,
        })
    return AstronomyLayer(
        measurements=measurement,
        planet_graph=measurement.get("planet_graph", {}),
        stellar_context={
            body: {
                "iau_constellation": row["iau_constellation"],
                "tropical_sign": row["tropical_sign"],
                "sidereal_lahiri_sign": row["sidereal_lahiri_sign"],
            }
            for body, row in measurement.get("bodies", {}).items()
        },
    )
