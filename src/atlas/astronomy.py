"""Astronomy-first physical measurement and planetary topology layer.

This module is deliberately independent of interpretation.  It records raw
geocentric measurements first, then attaches tropical and Lahiri sidereal
labels as non-canonical metadata.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

from atlas.temporal.constellations import build_astronomical_constellation_chart
from atlas.temporal.ephemeris import build_ephemeris, ephemeris_result_to_dict
from atlas.temporal.models import BirthData
from atlas.temporal.sidereal import convert_ephemeris_to_sidereal, sidereal_chart_to_dict


ASTRONOMY_MEASUREMENT_VERSION = "1.1.0"
CANONICAL_BODIES = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)
CLASSICAL_KAMEA_BODIES = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
)
ASTRONOMY_ONLY_BODIES = ("Uranus", "Neptune", "Pluto")
MAJOR_ASPECTS = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


def build_physical_astronomy(birth: BirthData) -> dict[str, Any]:
    """Measure physical coordinates before applying symbolic interpretation."""
    ephemeris = build_ephemeris(birth)
    raw = ephemeris_result_to_dict(ephemeris)
    constellations = build_astronomical_constellation_chart(ephemeris)
    sidereal = sidereal_chart_to_dict(convert_ephemeris_to_sidereal(ephemeris))
    measurements = {}

    for body in CANONICAL_BODIES:
        position = raw["planets"][body]
        sky = constellations["planets"][body]
        sidereal_position = sidereal["planets"][body]
        measurements[body] = {
            "body": body,
            "right_ascension_degrees": sky["right_ascension"],
            "declination_degrees": sky["declination"],
            "ecliptic_longitude_degrees": position["longitude"],
            "ecliptic_latitude_degrees": position["latitude"],
            "distance_au": position["distance"],
            "apparent_longitude_velocity_deg_per_day": position["speed"],
            "retrograde": position["retrograde"],
            "iau_constellation": sky["actual_constellation"],
            "iau_constellation_abbreviation": sky[
                "actual_constellation_abbreviation"
            ],
            "tropical_sign": position["sign"],
            "sidereal_lahiri_sign": sidereal_position["sign"],
            "tropical_coordinates": {
                "longitude_degrees": position["longitude"],
                "latitude_degrees": position["latitude"],
                "sign": position["sign"],
                "degree_in_sign": position["degree_in_sign"],
            },
            "sidereal_lahiri_coordinates": {
                "longitude_degrees": sidereal_position["longitude"],
                "latitude_degrees": sidereal_position["latitude"],
                "sign": sidereal_position["sign"],
                "degree_in_sign": sidereal_position["degree_in_sign"],
                "ayanamsha_degrees": sidereal["ayanamsa_degrees"],
            },
            "symbolic_projection": (
                {
                    "available": True,
                    "basis": "historical_classical_kamea",
                }
                if body in CLASSICAL_KAMEA_BODIES
                else {
                    "available": False,
                    "reason": "no_historical_classical_kamea",
                }
            ),
            "classification_authority": {
                "canonical_astronomical": "IAU Delporte boundary",
                "tropical_metadata": "12 equal 30-degree signs",
                "sidereal_metadata": "Lahiri 12-sign zodiac",
            },
        }

    return {
        "success": True,
        "version": ASTRONOMY_MEASUREMENT_VERSION,
        "measurement_policy": (
            "Physical coordinates are canonical. Tropical and sidereal signs "
            "are downstream metadata and do not alter measurements."
        ),
        "interpretation_applied": False,
        "birth": raw["birth"],
        "julian_day_ut": raw["julian_day"],
        "bodies": measurements,
        "planet_graph": build_planet_graph(measurements),
        "provenance": {
            "ephemeris": "Swiss Ephemeris geocentric calculations",
            "constellations": constellations["boundary_system"],
            "constellation_algorithm": constellations["boundary_algorithm"],
            "sidereal_metadata": "Lahiri ayanamsha",
        },
    }


def build_planet_graph(
    measurements: dict[str, dict[str, Any]],
    *,
    maximum_orb_degrees: float = 8.0,
) -> dict[str, Any]:
    """Build an all-pairs angular graph with optional aspect classification."""
    nodes = [
        {
            "node_id": body,
            "node_type": "astronomical_body",
            "measurement_ref": f"bodies.{body}",
        }
        for body in sorted(measurements)
    ]
    edges = []
    for left, right in combinations(sorted(measurements), 2):
        separation = angular_separation(
            measurements[left]["ecliptic_longitude_degrees"],
            measurements[right]["ecliptic_longitude_degrees"],
        )
        aspect, orb = classify_aspect(separation, maximum_orb_degrees)
        orb_strength = (
            round(1.0 - orb / maximum_orb_degrees, 6)
            if aspect and maximum_orb_degrees
            else 0.0
        )
        edges.append({
            "source": left,
            "target": right,
            "angular_separation_degrees": separation,
            "aspect_type": aspect,
            "orb_degrees": orb,
            "orb_strength": orb_strength,
            "normalized_orb_strength": orb_strength,
            "applying_separating": applying_separating_status(
                left_measurement=measurements[left],
                right_measurement=measurements[right],
                aspect_type=aspect,
            ),
            "visibility": {
                "status": "not_computed",
                "reason": "observer coordinates and horizon model required",
            },
            "gravitational_metadata": {
                "status": "not_computed",
                "reason": "mass/reference-frame model not selected",
            },
        })
    return {
        "success": True,
        "version": ASTRONOMY_MEASUREMENT_VERSION,
        "graph_type": "complete_measured_angular_graph",
        "directed": False,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "aspect_edge_count": sum(bool(row["aspect_type"]) for row in edges),
        "measurement_only": True,
    }


def angular_separation(left: float, right: float) -> float:
    difference = abs((float(left) - float(right)) % 360.0)
    return round(min(difference, 360.0 - difference), 9)


def classify_aspect(
    separation: float,
    maximum_orb_degrees: float,
) -> tuple[str | None, float | None]:
    aspect, exact = min(
        MAJOR_ASPECTS.items(),
        key=lambda item: abs(float(separation) - item[1]),
    )
    orb = abs(float(separation) - exact)
    if orb > maximum_orb_degrees:
        return None, None
    return aspect, round(orb, 9)


def applying_separating_status(
    *,
    left_measurement: dict[str, Any],
    right_measurement: dict[str, Any],
    aspect_type: str | None,
    projection_days: float = 1.0 / 1440.0,
) -> dict[str, Any]:
    """Classify whether a measured major aspect is applying or separating."""
    if not aspect_type:
        return {
            "status": "not_available",
            "reason": "no_classified_major_aspect",
        }

    exact = MAJOR_ASPECTS[aspect_type]
    left_longitude = float(left_measurement["ecliptic_longitude_degrees"])
    right_longitude = float(right_measurement["ecliptic_longitude_degrees"])
    left_velocity = float(
        left_measurement["apparent_longitude_velocity_deg_per_day"]
    )
    right_velocity = float(
        right_measurement["apparent_longitude_velocity_deg_per_day"]
    )
    current_orb = abs(angular_separation(left_longitude, right_longitude) - exact)
    projected_orb = abs(
        angular_separation(
            left_longitude + left_velocity * projection_days,
            right_longitude + right_velocity * projection_days,
        )
        - exact
    )
    difference = projected_orb - current_orb
    if abs(difference) <= 1e-9:
        status = "stationary"
    else:
        status = "applying" if difference < 0 else "separating"
    return {
        "status": status,
        "method": "one-minute apparent-longitude projection",
        "projection_days": projection_days,
    }


__all__ = [
    "ASTRONOMY_MEASUREMENT_VERSION",
    "ASTRONOMY_ONLY_BODIES",
    "CANONICAL_BODIES",
    "CLASSICAL_KAMEA_BODIES",
    "applying_separating_status",
    "angular_separation",
    "build_physical_astronomy",
    "build_planet_graph",
    "classify_aspect",
]
