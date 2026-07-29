"""Natal <-> name-kamea overlay: per-planet alignment/difference/complementarity."""

import pytest

from atlas.overlay.natal_kamea_overlay import (
    SHARED_PLANETS,
    build_natal_kamea_overlay,
    build_planet_overlay,
)


def test_reinforcing_when_both_elevated():
    # Both well above their population means -> should reinforce.
    overlay = build_planet_overlay("Saturn", natal_strength=8.0, kamea_z=2.0)
    assert overlay.relation == "reinforcing"
    assert overlay.alignment > 0


def test_jointly_suppressed_when_both_low():
    overlay = build_planet_overlay("Saturn", natal_strength=-6.0, kamea_z=-2.0)
    assert overlay.relation == "jointly-suppressed"
    assert overlay.alignment > 0  # same-sign z's still multiply positive


def test_differing_when_signs_disagree():
    overlay = build_planet_overlay("Saturn", natal_strength=8.0, kamea_z=-2.0)
    assert overlay.relation == "differing"
    assert overlay.alignment < 0
    assert overlay.complementarity > 0


def test_neutral_when_both_near_population_centre():
    overlay = build_planet_overlay("Saturn", natal_strength=1.385, kamea_z=0.0)
    assert overlay.relation == "neutral"


def test_full_overlay_only_compares_shared_planets():
    dignities = {p: {"strength_score": 1.0} for p in SHARED_PLANETS}
    dignities["Rahu"] = {"strength_score": 1.0}  # natal-only, no kamea
    ranked = [{"planet": p, "z_score": 0.5} for p in SHARED_PLANETS]
    ranked.append({"planet": "SomeExtra", "z_score": 0.1})

    overlay = build_natal_kamea_overlay(dignities, ranked)
    assert overlay["planets_compared"] == len(SHARED_PLANETS)
    assert {o["planet"] for o in overlay["overlays"]} == set(SHARED_PLANETS)


def test_empty_overlay_is_safe():
    overlay = build_natal_kamea_overlay({}, [])
    assert overlay["planets_compared"] == 0
    assert overlay["overlays"] == []
    assert overlay["most_reinforcing"] is None
