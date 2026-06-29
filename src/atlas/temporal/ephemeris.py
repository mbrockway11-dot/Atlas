"""Swiss Ephemeris wrapper for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import swisseph as swe

from atlas.temporal.models import BirthData, PlanetPosition


EPHEMERIS_ENGINE_VERSION = "1.0"

DEFAULT_EPHEMERIS_PATH = "data/ephemeris"

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


@dataclass(frozen=True)
class EphemerisResult:
    """Raw tropical ephemeris result."""

    version: str
    name: str
    birth: BirthData
    julian_day: float
    zodiac: str
    planets: dict[str, PlanetPosition]
    summary: dict[str, Any]


def build_ephemeris(
    birth: BirthData,
    *,
    ephemeris_path: str | Path = DEFAULT_EPHEMERIS_PATH,
) -> EphemerisResult:
    """Build tropical planetary positions from BirthData."""

    configure_ephemeris_path(ephemeris_path)

    julian_day = birth_data_to_julian_day(birth)

    planets = calculate_planets(julian_day)

    return EphemerisResult(
        version=EPHEMERIS_ENGINE_VERSION,
        name=birth.name,
        birth=birth,
        julian_day=julian_day,
        zodiac="tropical",
        planets=planets,
        summary={
            "planet_count": len(planets),
            "time_known": birth.time_known,
            "ephemeris_path": str(ephemeris_path),
        },
    )


def configure_ephemeris_path(
    ephemeris_path: str | Path,
) -> None:
    """Configure Swiss Ephemeris data path."""

    path = Path(ephemeris_path)

    if path.exists():
        swe.set_ephe_path(str(path))


def birth_data_to_julian_day(
    birth: BirthData,
) -> float:
    """Convert BirthData to Julian Day."""

    if not birth.birth_date:
        raise ValueError("Birth date is required for ephemeris calculations.")

    year, month, day = parse_birth_date(birth.birth_date)
    hour = parse_birth_time_to_decimal_hours(birth.birth_time)

    return swe.julday(
        year,
        month,
        day,
        hour,
    )


def parse_birth_date(
    birth_date: str,
) -> tuple[int, int, int]:
    """Parse YYYY-MM-DD birth date."""

    parts = birth_date.strip().split("-")

    if len(parts) == 4 and parts[0] == "":
        year = -int(parts[1])
        month = int(parts[2])
        day = int(parts[3])
        return year, month, day

    if len(parts) != 3:
        raise ValueError(f"Invalid birth date: {birth_date}")

    return int(parts[0]), int(parts[1]), int(parts[2])


def parse_birth_time_to_decimal_hours(
    birth_time: str,
) -> float:
    """Parse HH:MM birth time into decimal hours."""

    if not birth_time or birth_time.casefold() == "unknown":
        return 12.0

    parts = birth_time.strip().split(":")

    if len(parts) < 2:
        raise ValueError(f"Invalid birth time: {birth_time}")

    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) >= 3 else 0

    return hour + (minute / 60.0) + (second / 3600.0)


def calculate_planets(
    julian_day: float,
) -> dict[str, PlanetPosition]:
    """Calculate planetary positions."""

    planets: dict[str, PlanetPosition] = {}

    for planet_name, planet_id in PLANET_IDS.items():
        longitude, latitude, _distance, speed = calculate_body(
            julian_day,
            planet_id,
        )

        planets[planet_name] = build_planet_position(
            planet=planet_name,
            longitude=longitude,
            latitude=latitude,
            speed=speed,
        )

    rahu = planets.get("Rahu")

    if rahu is not None:
        ketu_longitude = normalize_degrees(
            rahu.longitude + 180.0,
        )

        planets["Ketu"] = build_planet_position(
            planet="Ketu",
            longitude=ketu_longitude,
            latitude=-rahu.latitude,
            speed=rahu.speed,
        )

    return planets


def calculate_body(
    julian_day: float,
    planet_id: int,
) -> tuple[float, float, float, float]:
    """Calculate one Swiss Ephemeris body."""

    values, _flags = swe.calc_ut(
        julian_day,
        planet_id,
    )

    longitude = normalize_degrees(values[0])
    latitude = values[1]
    distance = values[2]
    speed = values[3]

    return longitude, latitude, distance, speed


def build_planet_position(
    *,
    planet: str,
    longitude: float,
    latitude: float,
    speed: float,
) -> PlanetPosition:
    """Build PlanetPosition from ecliptic longitude."""

    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30

    return PlanetPosition(
        planet=planet,
        longitude=longitude,
        latitude=latitude,
        speed=speed,
        sign=SIGNS[sign_index],
        sign_index=sign_index,
        degree_in_sign=degree_in_sign,
        retrograde=speed < 0,
    )


def normalize_degrees(
    degrees: float,
) -> float:
    """Normalize degrees to 0 <= x < 360."""

    return degrees % 360.0


def ephemeris_result_to_dict(
    result: EphemerisResult,
) -> dict[str, Any]:
    """Convert EphemerisResult to dictionary."""

    return {
        "version": result.version,
        "name": result.name,
        "birth": asdict(result.birth),
        "julian_day": result.julian_day,
        "zodiac": result.zodiac,
        "planets": {
            planet: asdict(position)
            for planet, position in result.planets.items()
        },
        "summary": result.summary,
    }