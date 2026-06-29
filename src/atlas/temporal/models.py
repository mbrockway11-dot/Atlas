"""Atlas Temporal Intelligence models."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


TEMPORAL_MODEL_VERSION = "1.0"


@dataclass(frozen=True)
class BirthData:
    """Normalized birth data for temporal calculations."""

    name: str
    birth_date: str
    birth_time: str
    birth_place: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = ""
    source_file: str = ""
    row_number: int = 0
    time_known: bool = False


@dataclass(frozen=True)
class PlanetPosition:
    """Raw or sidereal planetary position."""

    planet: str
    longitude: float
    latitude: float
    speed: float
    sign: str
    sign_index: int
    degree_in_sign: float
    retrograde: bool


@dataclass(frozen=True)
class NatalChart:
    """Natal chart result."""

    version: str
    name: str
    birth: BirthData
    ayanamsa: str
    zodiac: str
    planets: dict[str, PlanetPosition]
    summary: dict[str, Any]


@dataclass(frozen=True)
class NakshatraPosition:
    """Nakshatra placement for a planet or point."""

    body: str
    nakshatra: str
    nakshatra_index: int
    pada: int
    longitude: float
    degree_in_nakshatra: float


@dataclass(frozen=True)
class TemporalOverlay:
    """Atlas structural profile with temporal layer attached."""

    version: str
    name: str
    structural_profile_path: str
    natal_chart: NatalChart
    nakshatras: dict[str, NakshatraPosition]
    summary: dict[str, Any]


def birth_data_to_dict(
    birth: BirthData,
) -> dict[str, Any]:
    """Convert BirthData to dictionary."""
    return asdict(birth)


def planet_position_to_dict(
    position: PlanetPosition,
) -> dict[str, Any]:
    """Convert PlanetPosition to dictionary."""
    return asdict(position)


def natal_chart_to_dict(
    chart: NatalChart,
) -> dict[str, Any]:
    """Convert NatalChart to dictionary."""
    return {
        "version": chart.version,
        "name": chart.name,
        "birth": birth_data_to_dict(chart.birth),
        "ayanamsa": chart.ayanamsa,
        "zodiac": chart.zodiac,
        "planets": {
            planet: planet_position_to_dict(position)
            for planet, position in chart.planets.items()
        },
        "summary": chart.summary,
    }


def nakshatra_position_to_dict(
    position: NakshatraPosition,
) -> dict[str, Any]:
    """Convert NakshatraPosition to dictionary."""
    return asdict(position)


def temporal_overlay_to_dict(
    overlay: TemporalOverlay,
) -> dict[str, Any]:
    """Convert TemporalOverlay to dictionary."""
    return {
        "version": overlay.version,
        "name": overlay.name,
        "structural_profile_path": overlay.structural_profile_path,
        "natal_chart": natal_chart_to_dict(overlay.natal_chart),
        "nakshatras": {
            body: nakshatra_position_to_dict(position)
            for body, position in overlay.nakshatras.items()
        },
        "summary": overlay.summary,
    }