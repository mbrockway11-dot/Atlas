"""Generic Varga framework for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from atlas.temporal.models import NatalChart


VARGA_ENGINE_VERSION = "1.0"

SIGNS = (
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
)


@dataclass(frozen=True)
class VargaPosition:
    """One planetary position in a divisional chart."""

    planet: str
    longitude: float
    sign: str
    sign_index: int
    division: int
    division_number: int
    degree_in_division: float


@dataclass(frozen=True)
class VargaChart:
    """Generic divisional chart."""

    version: str
    name: str
    division: int
    positions: dict[str, VargaPosition]
    summary: dict[str, Any]


Strategy = Callable[[float], tuple[int, int, float]]

_STRATEGIES: dict[int, Strategy] = {}


def register_varga_strategy(
    division: int,
    strategy: Strategy,
) -> None:
    """Register a divisional chart strategy."""

    _STRATEGIES[division] = strategy


def build_varga_chart(
    natal: NatalChart,
    *,
    division: int,
) -> VargaChart:
    """Build a divisional chart using a registered strategy."""

    if division not in _STRATEGIES:
        raise ValueError(f"No strategy registered for D{division}")

    strategy = _STRATEGIES[division]

    positions: dict[str, VargaPosition] = {}

    for planet, position in natal.planets.items():
        sign_index, division_number, degree = strategy(
            position.longitude,
        )

        positions[planet] = VargaPosition(
            planet=planet,
            longitude=position.longitude,
            sign=SIGNS[sign_index],
            sign_index=sign_index,
            division=division,
            division_number=division_number,
            degree_in_division=degree,
        )

    return VargaChart(
        version=VARGA_ENGINE_VERSION,
        name=natal.name,
        division=division,
        positions=positions,
        summary={
            "planet_count": len(positions),
        },
    )


def varga_chart_to_dict(
    chart: VargaChart,
) -> dict[str, Any]:
    """Convert VargaChart to dictionary."""

    return {
        "version": chart.version,
        "name": chart.name,
        "division": chart.division,
        "positions": {
            planet: asdict(position)
            for planet, position in chart.positions.items()
        },
        "summary": chart.summary,
    }