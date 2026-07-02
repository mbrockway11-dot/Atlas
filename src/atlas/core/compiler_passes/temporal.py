"""Temporal ephemeris pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import TemporalLayer
from atlas.core.compiler_passes.utils import (
    extract_acf,
    extract_intake,
    extract_temporal,
    first_dict,
)
from atlas.temporal.sidereal import (
    convert_ephemeris_to_sidereal,
    sidereal_chart_to_dict,
)
from atlas.temporal.nakshatra import (
    build_nakshatra_chart,
    nakshatra_chart_to_dict,
)
from atlas.temporal.houses import (
    build_house_chart,
    house_chart_to_dict,
)
from atlas.temporal.aspects import (
    aspect_chart_to_dict,
    build_aspect_chart,
)
from atlas.temporal.dignity import (
    build_dignity_chart,
    dignity_chart_to_dict,
)
from atlas.temporal.ephemeris import build_ephemeris, ephemeris_result_to_dict
from atlas.temporal.models import BirthData, NatalChart


def build_temporal_layer(*, profile_payload: dict[str, Any]) -> TemporalLayer:
    """Build CSS temporal layer from saved profile payload plus ephemeris."""
    temporal = extract_temporal(profile_payload)
    birth = build_birth_seed(profile_payload)

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

    ephemeris = build_safe_ephemeris(
        profile_payload=profile_payload,
        birth=birth,
    )

    if birth or planetary_matrix or ephemeris:
        natal = {
            **natal,
            "birth": birth,
            "planetary_matrix": planetary_matrix,
            "ephemeris": ephemeris,
            "temporal_status": (
                "ephemeris_enriched"
                if ephemeris.get("ephemeris_status") == "computed"
                else "seed_from_saved_profile"
            ),
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


def build_birth_seed(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Build birth seed from profile payload and intake data."""
    intake = extract_intake(profile_payload)

    birth = {
        "name": intake.get("name") or profile_payload.get("name"),
        "birth_date": intake.get("birth_date") or profile_payload.get("birth_date"),
        "birth_time": intake.get("birth_time") or profile_payload.get("birth_time"),
        "birth_place": (
            intake.get("birth_place")
            or intake.get("birth_location")
            or profile_payload.get("birth_place")
            or profile_payload.get("birth_location")
        ),
        "birth_location": (
            intake.get("birth_location")
            or intake.get("birth_place")
            or profile_payload.get("birth_location")
            or profile_payload.get("birth_place")
        ),
        "latitude": intake.get("latitude") or profile_payload.get("latitude"),
        "longitude": intake.get("longitude") or profile_payload.get("longitude"),
        "timezone": intake.get("timezone") or profile_payload.get("timezone"),
        "source_file": intake.get("source_file") or profile_payload.get("source_file"),
        "row_number": intake.get("row_number") or profile_payload.get("row_number"),
    }

    return {
        key: value
        for key, value in birth.items()
        if value is not None
    }


def build_safe_ephemeris(
    *,
    profile_payload: dict[str, Any],
    birth: dict[str, Any],
) -> dict[str, Any]:
    """Build ephemeris dict safely.

    Missing or partial birth data should never break CSS compilation.
    """
    birth_date = birth.get("birth_date")
    if not birth_date:
        return {}

    birth_time = birth.get("birth_time") or "12:00"
    birth_place = birth.get("birth_place") or birth.get("birth_location") or ""

    try:
        birth_data = BirthData(
            name=str(birth.get("name") or profile_payload.get("name") or ""),
            birth_date=str(birth_date),
            birth_time=str(birth_time),
            birth_place=str(birth_place),
            latitude=safe_float_or_none(birth.get("latitude")),
            longitude=safe_float_or_none(birth.get("longitude")),
            timezone=str(birth.get("timezone") or ""),
            source_file=str(birth.get("source_file") or ""),
            row_number=safe_int(birth.get("row_number")),
            time_known=is_time_known(str(birth_time)),
        )

        result = build_ephemeris(birth_data)

        data = ephemeris_result_to_dict(result)

        #
        # NEW
        # Convert the tropical ephemeris into
        # a sidereal chart.
        #
        try:
            sidereal_chart = convert_ephemeris_to_sidereal(result)

            data["sidereal"] = sidereal_chart_to_dict(
                sidereal_chart
            )

            data["sidereal_status"] = "computed"

            try:
                natal_chart = NatalChart(
                    version="1.0",
                    name=sidereal_chart.name,
                    birth=birth_data,
                    ayanamsa=sidereal_chart.ayanamsa,
                    zodiac=sidereal_chart.zodiac,
                    planets=sidereal_chart.planets,
                    summary=sidereal_chart.summary,
                )

                nakshatra_chart = build_nakshatra_chart(natal_chart)

                data["nakshatra"] = nakshatra_chart_to_dict(
                    nakshatra_chart
                )

                data["nakshatra_status"] = "computed"

                try:
                    house_chart = build_house_chart(natal_chart)

                    data["houses"] = house_chart_to_dict(
                        house_chart
                    )

                    data["houses_status"] = "computed"

                    try:
                        aspect_chart = build_aspect_chart(house_chart)

                        data["aspects"] = aspect_chart_to_dict(
                            aspect_chart
                        )

                        data["aspects_status"] = "computed"

                    except Exception as exc:
                        data["aspects"] = {}
                        data["aspects_status"] = "failed"
                        data["aspects_error"] = str(exc)

                    try:
                        dignity_chart = build_dignity_chart(natal_chart)

                        data["dignity"] = dignity_chart_to_dict(
                            dignity_chart
                        )

                        data["dignity_status"] = "computed"

                    except Exception as exc:
                        data["dignity"] = {}
                        data["dignity_status"] = "failed"
                        data["dignity_error"] = str(exc)

                except Exception as exc:
                    data["houses"] = {}
                    data["aspects"] = {}
                    data["dignity"] = {}
                    data["houses_status"] = "failed"
                    data["aspects_status"] = "skipped"
                    data["dignity_status"] = "skipped"
                    data["houses_error"] = str(exc)

            except Exception as exc:
                data["nakshatra"] = {}
                data["nakshatra_status"] = "failed"
                data["nakshatra_error"] = str(exc)

        except Exception as exc:
            data["sidereal"] = {}
            data["nakshatra"] = {}
            data["houses"] = {}

            data["sidereal_status"] = "failed"
            data["nakshatra_status"] = "skipped"
            data["houses_status"] = "skipped"

            data["sidereal_error"] = str(exc)

        data["ephemeris_status"] = "computed"

        return data

    except Exception as exc:  # noqa: BLE001
        return {
            "ephemeris_status": "failed",
            "error": str(exc),
        }


def safe_float_or_none(value: Any) -> float | None:
    """Convert value to float or None."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def is_time_known(value: str) -> bool:
    """Return whether birth time appears known."""
    text = value.strip().casefold()

    if not text:
        return False

    return text not in {"unknown", "12:00", "12:00:00"}

