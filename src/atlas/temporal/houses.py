"""House calculations for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

import swisseph as swe

from atlas.temporal.config import DEFAULT_HOUSE_SYSTEM
from atlas.temporal.ephemeris import SIGNS, normalize_degrees
from atlas.temporal.models import BirthData, NatalChart, PlanetPosition


HOUSES_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class HouseCusp:
    """One house cusp."""

    house: int
    longitude: float
    sign: str
    sign_index: int
    degree_in_sign: float


@dataclass(frozen=True)
class HousePlacement:
    """Planet placement in a house."""

    planet: str
    house: int
    sign: str
    sign_index: int
    longitude: float
    degree_in_sign: float


@dataclass(frozen=True)
class HouseChart:
    """House calculation result."""

    version: str
    name: str
    house_system: str
    ascendant: HouseCusp
    midheaven: HouseCusp
    cusps: dict[int, HouseCusp]
    placements: dict[str, HousePlacement]
    summary: dict[str, Any]


def build_house_chart(
    chart: NatalChart,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    house_system: str = DEFAULT_HOUSE_SYSTEM,
) -> HouseChart:
    """Build house chart from a natal chart."""

    lat = resolve_latitude(
        chart.birth,
        latitude,
    )

    lon = resolve_longitude(
        chart.birth,
        longitude,
    )

    if house_system != "Whole Sign":
        raise ValueError(f"Unsupported house system: {house_system}")

    ascendant_longitude, midheaven_longitude = calculate_asc_mc(
        julian_day=chart.summary.get("julian_day", 0.0),
        latitude=lat,
        longitude=lon,
    )

    if chart.summary.get("julian_day", 0.0) == 0.0:
        ascendant_longitude = chart.planets["Sun"].longitude
        midheaven_longitude = normalize_degrees(
            ascendant_longitude + 90.0,
        )

    ascendant = build_house_cusp(
        house=1,
        longitude=ascendant_longitude,
    )

    midheaven = build_house_cusp(
        house=10,
        longitude=midheaven_longitude,
    )

    cusps = build_whole_sign_cusps(
        ascendant.sign_index,
    )

    placements = assign_planets_to_whole_sign_houses(
        planets=chart.planets,
        ascendant_sign_index=ascendant.sign_index,
    )

    return HouseChart(
        version=HOUSES_ENGINE_VERSION,
        name=chart.name,
        house_system=house_system,
        ascendant=ascendant,
        midheaven=midheaven,
        cusps=cusps,
        placements=placements,
        summary={
            "planet_count": len(placements),
            "house_system": house_system,
            "ascendant_sign": ascendant.sign,
            "midheaven_sign": midheaven.sign,
            "latitude": lat,
            "longitude": lon,
        },
    )


def calculate_asc_mc(
    *,
    julian_day: float,
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """Calculate tropical ascendant and midheaven from Swiss Ephemeris."""

    if julian_day <= 0.0:
        return 0.0, 90.0

    cusps, ascmc = swe.houses_ex(
        julian_day,
        latitude,
        longitude,
        b"P",
    )

    ascendant = normalize_degrees(
        ascmc[0],
    )

    midheaven = normalize_degrees(
        ascmc[1],
    )

    return ascendant, midheaven


def build_house_cusp(
    *,
    house: int,
    longitude: float,
) -> HouseCusp:
    """Build one house cusp."""

    normalized = normalize_degrees(longitude)
    sign_index = int(normalized // 30)
    degree_in_sign = normalized % 30

    return HouseCusp(
        house=house,
        longitude=normalized,
        sign=SIGNS[sign_index],
        sign_index=sign_index,
        degree_in_sign=degree_in_sign,
    )


def build_whole_sign_cusps(
    ascendant_sign_index: int,
) -> dict[int, HouseCusp]:
    """Build Whole Sign house cusps."""

    cusps: dict[int, HouseCusp] = {}

    for house in range(1, 13):
        sign_index = (
            ascendant_sign_index + house - 1
        ) % 12

        longitude = sign_index * 30.0

        cusps[house] = build_house_cusp(
            house=house,
            longitude=longitude,
        )

    return cusps


def assign_planets_to_whole_sign_houses(
    *,
    planets: dict[str, PlanetPosition],
    ascendant_sign_index: int,
) -> dict[str, HousePlacement]:
    """Assign planets to Whole Sign houses."""

    placements: dict[str, HousePlacement] = {}

    for planet_name, position in planets.items():
        house = whole_sign_house_for_sign(
            sign_index=position.sign_index,
            ascendant_sign_index=ascendant_sign_index,
        )

        placements[planet_name] = HousePlacement(
            planet=planet_name,
            house=house,
            sign=position.sign,
            sign_index=position.sign_index,
            longitude=position.longitude,
            degree_in_sign=position.degree_in_sign,
        )

    return placements


def whole_sign_house_for_sign(
    *,
    sign_index: int,
    ascendant_sign_index: int,
) -> int:
    """Resolve Whole Sign house number."""

    return ((sign_index - ascendant_sign_index) % 12) + 1


def resolve_latitude(
    birth: BirthData,
    latitude: float | None,
) -> float:
    """Resolve latitude."""

    if latitude is not None:
        return latitude

    if birth.latitude is not None:
        return birth.latitude

    return 0.0


def resolve_longitude(
    birth: BirthData,
    longitude: float | None,
) -> float:
    """Resolve longitude."""

    if longitude is not None:
        return longitude

    if birth.longitude is not None:
        return birth.longitude

    return 0.0


def house_cusp_to_dict(
    cusp: HouseCusp,
) -> dict[str, Any]:
    """Convert HouseCusp to dictionary."""

    return asdict(cusp)


def house_placement_to_dict(
    placement: HousePlacement,
) -> dict[str, Any]:
    """Convert HousePlacement to dictionary."""

    return asdict(placement)


def house_chart_to_dict(
    chart: HouseChart,
) -> dict[str, Any]:
    """Convert HouseChart to dictionary."""

    return {
        "version": chart.version,
        "name": chart.name,
        "house_system": chart.house_system,
        "ascendant": house_cusp_to_dict(chart.ascendant),
        "midheaven": house_cusp_to_dict(chart.midheaven),
        "cusps": {
            str(house): house_cusp_to_dict(cusp)
            for house, cusp in chart.cusps.items()
        },
        "placements": {
            planet: house_placement_to_dict(placement)
            for planet, placement in chart.placements.items()
        },
        "summary": chart.summary,
    }