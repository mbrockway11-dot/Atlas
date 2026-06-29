"""Natal chart assembly for Atlas Temporal Intelligence."""

from __future__ import annotations

from typing import Any

from atlas.temporal.config import (
    DEFAULT_AYANAMSA,
    DEFAULT_ZODIAC,
)
from atlas.temporal.ephemeris import (
    build_ephemeris,
    ephemeris_result_to_dict,
)
from atlas.temporal.models import BirthData, NatalChart
from atlas.temporal.sidereal import (
    convert_ephemeris_to_sidereal,
    sidereal_chart_to_dict,
)


NATAL_CHART_ENGINE_VERSION = "1.0"


def build_natal_chart(
    birth: BirthData,
    *,
    ayanamsa: str = DEFAULT_AYANAMSA,
    zodiac: str = DEFAULT_ZODIAC,
) -> NatalChart:
    """Build canonical natal chart from BirthData."""

    ephemeris = build_ephemeris(birth)

    if zodiac == "sidereal":
        sidereal = convert_ephemeris_to_sidereal(
            ephemeris,
            ayanamsa=ayanamsa,
        )

        planets = sidereal.planets
        selected_zodiac = sidereal.zodiac
        selected_ayanamsa = sidereal.ayanamsa
        ayanamsa_degrees = sidereal.ayanamsa_degrees

    elif zodiac == "tropical":
        planets = ephemeris.planets
        selected_zodiac = ephemeris.zodiac
        selected_ayanamsa = "None"
        ayanamsa_degrees = 0.0

    else:
        raise ValueError(f"Unsupported zodiac: {zodiac}")

    return NatalChart(
        version=NATAL_CHART_ENGINE_VERSION,
        name=birth.name,
        birth=birth,
        ayanamsa=selected_ayanamsa,
        zodiac=selected_zodiac,
        planets=planets,
        summary={
            "planet_count": len(planets),
            "zodiac": selected_zodiac,
            "ayanamsa": selected_ayanamsa,
            "ayanamsa_degrees": ayanamsa_degrees,
            "time_known": birth.time_known,
            "source": "Swiss Ephemeris",
        },
    )


def build_natal_chart_payload(
    birth: BirthData,
    *,
    ayanamsa: str = DEFAULT_AYANAMSA,
) -> dict[str, Any]:
    """Build diagnostic natal chart payload with raw and sidereal layers."""

    ephemeris = build_ephemeris(birth)
    sidereal = convert_ephemeris_to_sidereal(
        ephemeris,
        ayanamsa=ayanamsa,
    )

    chart = NatalChart(
        version=NATAL_CHART_ENGINE_VERSION,
        name=birth.name,
        birth=birth,
        ayanamsa=sidereal.ayanamsa,
        zodiac=sidereal.zodiac,
        planets=sidereal.planets,
        summary={
            "planet_count": len(sidereal.planets),
            "zodiac": sidereal.zodiac,
            "ayanamsa": sidereal.ayanamsa,
            "ayanamsa_degrees": sidereal.ayanamsa_degrees,
            "time_known": birth.time_known,
            "source": "Swiss Ephemeris",
        },
    )

    return {
        "version": NATAL_CHART_ENGINE_VERSION,
        "name": birth.name,
        "birth": birth,
        "ephemeris": ephemeris_result_to_dict(ephemeris),
        "sidereal": sidereal_chart_to_dict(sidereal),
        "natal_chart": chart,
    }