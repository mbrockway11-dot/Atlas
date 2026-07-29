"""Natal chart <-> name-kamea overlay: per-planet alignment, difference, complementarity.

The design this fills in (Phase XII of the external Codex spec, never built):
take the person's *natal* planetary strength (sidereal dignity -- exalted, own
sign, debilitated, friend/enemy) and their *name* planetary activity (the
kamea's population-relative rank, see ``invariant.pipeline.rank_kameas``), and
compare them per planet, for the seven classical bodies both systems share
(Sun through Saturn -- Rahu/Ketu/Uranus/Neptune/Pluto have no kamea).

Both scores are z-scored against a population reference so "high" is
population-relative on both sides, then combined into one signed overlay score
per planet:

    alignment      -- natal and name-activity agree in sign and are both large
                       in magnitude (both elevated, or both suppressed)
    difference     -- the two disagree in sign (elevated in one, suppressed in
                       the other)
    complementarity -- how much one is elevated where the other is not, i.e.
                       |natal_z - kamea_z|, independent of direction

This module does not claim the overlay is meaningful -- that is an empirical
question, tested in ``scripts/natal_kamea_overlay_test.py``. The one existing
population-level test of this pairing (name-kamea vs birth-Vedic, Mantel test,
n=1885) came back null (r=+0.007, p=0.11); a per-person overlay computed from
independent scales does not by itself resolve that, and should be read the same
way -- descriptive until tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The seven classical bodies present in both the natal dignity chart and a
# kamea. Rahu/Ketu/Uranus/Neptune/Pluto are natal-only and have no kamea.
SHARED_PLANETS = (
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
)

# Population reference for the natal dignity_strength score, measured over 300
# uniformly random dates spanning 1900-01-01 .. 2020-01-01 (2026-07-29). Dignity
# strength is driven by sign placement, which cycles with each planet's own
# ephemeris period rather than name structure, so this baseline is date-range
# dependent -- recalibrate if the subject population's era changes materially.
NATAL_STRENGTH_BASELINE: dict[str, tuple[float, float]] = {
    "Sun": (0.903, 3.639), "Moon": (1.043, 3.155), "Mercury": (0.927, 4.240),
    "Venus": (1.387, 3.007), "Mars": (0.990, 3.206), "Jupiter": (1.108, 3.549),
    "Saturn": (1.385, 3.414),
}


def _z(value: float, mean: float, sd: float) -> float:
    return (value - mean) / sd if sd > 0 else 0.0


@dataclass(frozen=True)
class PlanetOverlay:
    """One planet's natal-vs-name-kamea overlay."""

    planet: str
    natal_strength: float
    natal_z: float
    kamea_z: float
    alignment: float
    difference: float
    complementarity: float
    relation: str


def _classify_relation(natal_z: float, kamea_z: float) -> str:
    """Label the pairing from its z-scores; thresholds are on sd units."""
    if abs(natal_z) < 0.35 and abs(kamea_z) < 0.35:
        return "neutral"
    if natal_z >= 0.35 and kamea_z >= 0.35:
        return "reinforcing"
    if natal_z <= -0.35 and kamea_z <= -0.35:
        return "jointly-suppressed"
    return "differing"


def build_planet_overlay(
    planet: str,
    natal_strength: float,
    kamea_z: float,
    natal_baseline: dict[str, tuple[float, float]] = NATAL_STRENGTH_BASELINE,
) -> PlanetOverlay:
    """Overlay one planet's natal dignity against its name-kamea activity."""
    mean, sd = natal_baseline.get(planet, (0.0, 1.0))
    natal_z = _z(natal_strength, mean, sd)

    # Alignment: positive when both point the same way, scaled by how far both
    # sit from the population centre (a strong joint signal), signed by
    # direction. Complementarity: pure magnitude of disagreement.
    alignment = natal_z * kamea_z
    difference = kamea_z - natal_z
    complementarity = abs(difference)

    return PlanetOverlay(
        planet=planet,
        natal_strength=natal_strength,
        natal_z=natal_z,
        kamea_z=kamea_z,
        alignment=alignment,
        difference=difference,
        complementarity=complementarity,
        relation=_classify_relation(natal_z, kamea_z),
    )


def build_natal_kamea_overlay(
    dignities: dict[str, dict[str, Any]],
    ranked_kameas: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the full natal <-> name-kamea overlay for the shared planets.

    ``dignities`` is ``DignityChart.dignities`` (planet -> dict with
    ``strength_score``); ``ranked_kameas`` is the output of
    ``invariant.pipeline.rank_kameas`` (already population-relative z-scores).
    """
    kamea_z_by_planet = {item["planet"]: item["z_score"] for item in ranked_kameas}

    overlays = []
    for planet in SHARED_PLANETS:
        dignity = dignities.get(planet)
        if dignity is None or planet not in kamea_z_by_planet:
            continue
        overlays.append(
            build_planet_overlay(
                planet,
                float(dignity["strength_score"]),
                float(kamea_z_by_planet[planet]),
            )
        )

    if not overlays:
        return {
            "overlays": [],
            "planets_compared": 0,
            "mean_alignment": 0.0,
            "mean_complementarity": 0.0,
            "most_reinforcing": None,
            "most_differing": None,
        }

    by_alignment = sorted(overlays, key=lambda o: o.alignment, reverse=True)
    by_complementarity = sorted(overlays, key=lambda o: o.complementarity, reverse=True)

    return {
        "overlays": [planet_overlay_to_dict(o) for o in overlays],
        "planets_compared": len(overlays),
        "mean_alignment": sum(o.alignment for o in overlays) / len(overlays),
        "mean_complementarity": sum(o.complementarity for o in overlays) / len(overlays),
        "most_reinforcing": by_alignment[0].planet,
        "most_differing": by_complementarity[0].planet,
    }


def planet_overlay_to_dict(overlay: PlanetOverlay) -> dict[str, Any]:
    """Convert a PlanetOverlay to a JSON-safe dictionary."""
    return {
        "planet": overlay.planet,
        "natal_strength": overlay.natal_strength,
        "natal_z": overlay.natal_z,
        "kamea_z": overlay.kamea_z,
        "alignment": overlay.alignment,
        "difference": overlay.difference,
        "complementarity": overlay.complementarity,
        "relation": overlay.relation,
    }
