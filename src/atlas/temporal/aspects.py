"""Graha Drishti (planetary aspects) for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.temporal.houses import HouseChart


ASPECT_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class Aspect:
    """One Graha Drishti aspect."""

    source: str
    target: str

    source_house: int
    target_house: int

    aspect_type: str
    strength: float


@dataclass(frozen=True)
class AspectChart:
    """Complete planetary aspect chart."""

    version: str
    name: str
    aspects: list[Aspect]
    summary: dict[str, Any]

GRAHA_DRISHTI = {
    "Sun": {7},
    "Moon": {7},
    "Mercury": {7},
    "Venus": {7},
    "Rahu": {7},
    "Ketu": {7},

    "Mars": {4, 7, 8},

    "Jupiter": {5, 7, 9},

    "Saturn": {3, 7, 10},
}

def house_distance(
    source: int,
    target: int,
) -> int:
    """Return forward Whole Sign distance."""

    return ((target - source) % 12) + 1

def build_aspect_chart(
    house_chart: HouseChart,
) -> AspectChart:
    """Build Graha Drishti aspect chart."""

    aspects: list[Aspect] = []

    placements = house_chart.placements

    for source_name, source in placements.items():

        source_rules = GRAHA_DRISHTI.get(
            source_name,
            {7},
        )

        for target_name, target in placements.items():

            if source_name == target_name:
                continue

            distance = house_distance(
                source.house,
                target.house,
            )

            if distance not in source_rules:
                continue

            aspects.append(
                Aspect(
                    source=source_name,
                    target=target_name,
                    source_house=source.house,
                    target_house=target.house,
                    aspect_type=f"{distance}th",
                    strength=1.0,
                )
            )

    return AspectChart(
        version=ASPECT_ENGINE_VERSION,
        name=house_chart.name,
        aspects=aspects,
        summary={
            "aspect_count": len(aspects),
            "planet_count": len(placements),
        },
    )

def outgoing_aspects(
    chart: AspectChart,
    planet: str,
) -> list[Aspect]:
    """Return all aspects cast by a planet."""

    return [
        aspect
        for aspect in chart.aspects
        if aspect.source == planet
    ]


def incoming_aspects(
    chart: AspectChart,
    planet: str,
) -> list[Aspect]:
    """Return all aspects received by a planet."""

    return [
        aspect
        for aspect in chart.aspects
        if aspect.target == planet
    ]

def aspect_chart_to_dict(
    chart: AspectChart,
) -> dict[str, Any]:
    """Convert AspectChart to a dictionary."""

    return {
        "version": chart.version,
        "name": chart.name,
        "aspects": [
            asdict(aspect)
            for aspect in chart.aspects
        ],
        "summary": chart.summary,
    }