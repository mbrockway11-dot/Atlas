"""The ayanamsa choice: computed and verifiable, but not licensed.

Pins the distinction 1E-V-CLASSIFY drew and 1E-V-SOURCE-A will resolve: the
offset is reproducible computation, the choice among schemes is a
school-specific claim. The recorded offsets are verified against swisseph, the
same executable-source pattern the Hebrew identity table uses, and the
data-level laundering guard refuses a sidereal result that does not name its
ayanamsa.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.vedic_ayanamsa import (
    AYANAMSA_REGISTRY,
    EPHEMERIS_PROVIDER_VERSION,
    KRISHNAMURTI,
    LAHIRI,
    RAMAN,
    REFERENCE_EPOCH_JD,
    AyanamsaChoice,
    AyanamsaError,
    admitted_ayanamsa_choices,
    require_sidereal_provenance,
)


# ---------------------------------------------------------------------------
# The offsets are computed and verifiable
# ---------------------------------------------------------------------------


def test_recorded_offsets_match_swisseph() -> None:
    """The source is executable: recompute every offset and compare.

    This is what lets the offset be treated as reproducible computation --
    the pinned engine reproduces it at runtime, so the recorded value cannot
    silently drift from swisseph.
    """
    import swisseph as swe

    constants = {
        "lahiri": swe.SIDM_LAHIRI,
        "raman": swe.SIDM_RAMAN,
        "krishnamurti": swe.SIDM_KRISHNAMURTI,
    }

    assert swe.version == EPHEMERIS_PROVIDER_VERSION

    for choice in AYANAMSA_REGISTRY:
        swe.set_sid_mode(constants[choice.scheme_id], 0, 0)
        recomputed = swe.get_ayanamsa_ut(REFERENCE_EPOCH_JD)

        assert recomputed == pytest.approx(
            choice.computed_offset_degrees, abs=1e-6
        )


def test_schemes_disagree_enough_to_move_boundaries() -> None:
    """The reason the choice matters: more than a nakshatra pada apart.

    A pada is 3.333 degrees; Lahiri and Raman differ by ~1.45, which shifts
    nakshatra and pada assignments near boundaries.
    """
    spread = LAHIRI.computed_offset_degrees - RAMAN.computed_offset_degrees

    assert spread > 1.0


# ---------------------------------------------------------------------------
# ... but no choice is licensed
# ---------------------------------------------------------------------------


def test_only_lahiri_is_admitted() -> None:
    """Lahiri is licensed by the Govt of India standard; Raman and KP are not.

    A computed offset is reproducible; choosing the scheme is a source claim.
    Lahiri now has one (1E-V-SOURCE-A, Calendar Reform Committee 1955); the
    other schemes stay unlicensed.
    """
    assert [c.scheme_id for c in admitted_ayanamsa_choices()] == ["lahiri"]
    assert LAHIRI.admitted is True
    assert [
        c.scheme_id for c in AYANAMSA_REGISTRY if not c.admitted
    ] == ["raman", "krishnamurti"]


def test_admitted_lahiri_carries_verified_provenance() -> None:
    """The admitted choice names a hashed, located Government of India source."""
    assert LAHIRI.source_copy_hash
    assert "Calendar Reform Committee" in LAHIRI.source_locator
    assert "23 deg 15'" in LAHIRI.source_locator
    assert "committee's own recommendation" in LAHIRI.source_locator


def test_a_choice_cannot_be_admitted_without_a_source() -> None:
    """Selecting an ayanamsa is a school claim needing a source."""
    with pytest.raises(AyanamsaError, match="school-specific claim"):
        AyanamsaChoice(
            scheme_id="lahiri",
            provider="swiss_ephemeris",
            provider_constant="SIDM_LAHIRI",
            epoch_label="J2000.0",
            epoch_jd=REFERENCE_EPOCH_JD,
            computed_offset_degrees=23.857092,
            computation_library_version=EPHEMERIS_PROVIDER_VERSION,
            admitted=True,
            source_copy_hash="",
            source_locator="",
        )


def test_choice_hash_tracks_the_computation_not_the_licensing() -> None:
    """Two builds computing the same offset describe the same choice.

    Licensing is tracked by ``admitted``, not by the offset's identity, so a
    later source that admits Lahiri does not change its choice hash.
    """
    licensed = AyanamsaChoice(
        scheme_id=LAHIRI.scheme_id,
        provider=LAHIRI.provider,
        provider_constant=LAHIRI.provider_constant,
        epoch_label=LAHIRI.epoch_label,
        epoch_jd=LAHIRI.epoch_jd,
        computed_offset_degrees=LAHIRI.computed_offset_degrees,
        computation_library_version=LAHIRI.computation_library_version,
        admitted=True,
        source_copy_hash="realhash",
        source_locator="real p. 1",
    )

    assert licensed.choice_hash() == LAHIRI.choice_hash()
    assert LAHIRI.choice_hash() != RAMAN.choice_hash()


# ---------------------------------------------------------------------------
# The data-level laundering guard
# ---------------------------------------------------------------------------


def test_a_sidereal_result_must_name_its_ayanamsa() -> None:
    """Nakshatra, sign, longitude, divisional, dasha all require provenance."""
    for quantity in (
        "sidereal_longitude",
        "nakshatra",
        "sidereal_sign",
        "divisional_placement",
        "dasha",
    ):
        with pytest.raises(AyanamsaError, match="ayanamsa_choice_hash"):
            require_sidereal_provenance({quantity: "anything"})


def test_a_fully_provenanced_sidereal_result_passes() -> None:
    """The guard permits a result that names every required hash."""
    require_sidereal_provenance(
        {
            "nakshatra": "Ashwini",
            "ayanamsa_choice_hash": LAHIRI.choice_hash(),
            "ephemeris_input_hash": "abc",
            "ephemeris_provider_version": EPHEMERIS_PROVIDER_VERSION,
        }
    )


def test_a_tropical_result_is_unaffected() -> None:
    """A quantity reproducible from the ephemeris alone needs no ayanamsa."""
    require_sidereal_provenance({"tropical_longitude": 123.4})


def test_a_partial_provenance_is_refused() -> None:
    """Every required hash, not just the choice hash."""
    with pytest.raises(AyanamsaError, match="ephemeris_input_hash"):
        require_sidereal_provenance(
            {
                "nakshatra": "Bharani",
                "ayanamsa_choice_hash": LAHIRI.choice_hash(),
                "ephemeris_provider_version": EPHEMERIS_PROVIDER_VERSION,
            }
        )
