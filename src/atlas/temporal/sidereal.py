"""Sidereal conversion utilities for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

import swisseph as swe

from atlas.temporal.ephemeris import (
    SIGNS,
    EphemerisResult,
    normalize_degrees,
)
from atlas.temporal.models import PlanetPosition


SIDEREAL_ENGINE_VERSION = "1.0"

DEFAULT_AYANAMSA = "Lahiri"

AYANAMSA_MODES = {
    "Lahiri": swe.SIDM_LAHIRI,
    "Raman": swe.SIDM_RAMAN,
    "Krishnamurti": swe.SIDM_KRISHNAMURTI,
    "Fagan-Bradley": swe.SIDM_FAGAN_BRADLEY,
}


@dataclass(frozen=True)
class SiderealChart:
    """Sidereal conversion result."""

    version: str
    name: str
    ayanamsa: str
    ayanamsa_degrees: float
    zodiac: str
    planets: dict[str, PlanetPosition]
    summary: dict[str, Any]


def convert_ephemeris_to_sidereal(
    ephemeris: EphemerisResult,
    *,
    ayanamsa: str = DEFAULT_AYANAMSA,
) -> SiderealChart:
    """Convert tropical ephemeris result to sidereal positions."""

    ayanamsa_degrees = get_ayanamsa_degrees(
        ephemeris.julian_day,
        ayanamsa=ayanamsa,
    )

    planets = {
        planet_name: convert_position_to_sidereal(
            position,
            ayanamsa_degrees=ayanamsa_degrees,
        )
        for planet_name, position in ephemeris.planets.items()
    }

    return SiderealChart(
        version=SIDEREAL_ENGINE_VERSION,
        name=ephemeris.name,
        ayanamsa=ayanamsa,
        ayanamsa_degrees=ayanamsa_degrees,
        zodiac="sidereal",
        planets=planets,
        summary={
            "planet_count": len(planets),
            "source_zodiac": ephemeris.zodiac,
            "ayanamsa": ayanamsa,
            "ayanamsa_degrees": ayanamsa_degrees,
        },
    )


def get_ayanamsa_degrees(
    julian_day: float,
    *,
    ayanamsa: str = DEFAULT_AYANAMSA,
) -> float:
    """Return ayanamsa in degrees for a Julian Day."""

    mode = resolve_ayanamsa_mode(ayanamsa)

    swe.set_sid_mode(mode)

    return float(
        swe.get_ayanamsa_ut(julian_day)
    )


def resolve_ayanamsa_mode(
    ayanamsa: str,
) -> int:
    """Resolve ayanamsa name to Swiss Ephemeris sidereal mode."""

    if ayanamsa not in AYANAMSA_MODES:
        raise ValueError(f"Unsupported ayanamsa: {ayanamsa}")

    return AYANAMSA_MODES[ayanamsa]


def convert_position_to_sidereal(
    position: PlanetPosition,
    *,
    ayanamsa_degrees: float,
) -> PlanetPosition:
    """Convert one tropical position to sidereal position."""

    sidereal_longitude = normalize_degrees(
        position.longitude - ayanamsa_degrees,
    )

    sign_index = int(sidereal_longitude // 30)
    degree_in_sign = sidereal_longitude % 30

    return PlanetPosition(
        planet=position.planet,
        longitude=sidereal_longitude,
        latitude=position.latitude,
        speed=position.speed,
        sign=SIGNS[sign_index],
        sign_index=sign_index,
        degree_in_sign=degree_in_sign,
        retrograde=position.retrograde,
    )


def sidereal_chart_to_dict(
    chart: SiderealChart,
) -> dict[str, Any]:
    """Convert SiderealChart to dictionary."""

    return {
        "version": chart.version,
        "name": chart.name,
        "ayanamsa": chart.ayanamsa,
        "ayanamsa_degrees": chart.ayanamsa_degrees,
        "zodiac": chart.zodiac,
        "planets": {
            planet: asdict(position)
            for planet, position in chart.planets.items()
        },
        "summary": chart.summary,
    }