"""The cross-system synthesis runner: three systems, one subject, scored.

Pulls each admitted system's claims from its canonical binding, assembles them,
and scores concordance against the null controls. Verifies the scope structure
(numerology meets Vedic-natal, Kamea meets Vedic-transit, numerology never meets
Kamea) and that the runner produces an agreement gap.
"""

from __future__ import annotations

from datetime import date

from atlas.validation.denotation.expressions import SystemExpression
from atlas.validation.denotation.synthesis import (
    SynthesisSubject,
    run_synthesis,
    subject_claims,
    synthesize,
)


def _kamea_expression(subject_id: str) -> SystemExpression:
    """A frozen Kamea structural output that yields dynamic-axis claims."""
    return SystemExpression(
        system="kamea",
        subject_id=subject_id,
        content={
            "kamea_key": "fx",
            "distinct_cells": 3,       # revisit_fraction 0.7 -> repetition
            "transition_count": 2,     # transition_fraction 0.22 -> stabilization
            "longest_stationary_run": 4,
            "reversal_count": 0,
            "samples": 10,
            "stationary": False,
        },
        reference_class="transit",
    )


def test_synthesize_assembles_every_contributing_system() -> None:
    """All three systems contribute claims to one subject."""
    subject = SynthesisSubject(
        subject_id="s1",
        name="Ada Lovelace",
        birth_date=date(2000, 1, 2),
        natal_ascendant_sign=5,          # Leo -> Sun lord
        natal_moon_sign=1,
        transit_when="2026-07-27",
        graha_transit_signs={"saturn": 3, "venus": 1},
        kamea_expression=_kamea_expression("s1"),
    )

    denotation = synthesize(subject)

    assert set(denotation.systems_present()) == {"numerology", "vedic", "kamea"}


def test_numerology_meets_vedic_natal_kamea_meets_vedic_transit() -> None:
    """The scope structure: same-scope claims exist to be compared."""
    claims = subject_claims(
        SynthesisSubject(
            subject_id="s1",
            name="Ada Lovelace",
            birth_date=date(2000, 1, 2),
            natal_ascendant_sign=5,
            natal_moon_sign=1,
            transit_when="2026-07-27",
            graha_transit_signs={"saturn": 3},
            kamea_expression=_kamea_expression("s1"),
        )
    )

    scopes = {
        system: {claim.temporal_scope for claim in system_claims}
        for system, system_claims in claims.items()
    }

    assert scopes["numerology"] == {"natal"}
    assert scopes["kamea"] == {"transit"}
    # Vedic bridges: a natal lagna-lord claim and transit claims.
    assert "natal" in scopes["vedic"]
    assert any(s.startswith("transit") for s in scopes["vedic"])


def test_numerology_and_vedic_natal_can_agree() -> None:
    """A subject on whom numerology and Vedic land on the same coordinate.

    Leo ascendant makes the Sun the lagna lord -> domain=agency; this subject's
    numerology also reaches domain=agency, so the natal pair agrees.
    """
    subject = SynthesisSubject(
        subject_id="s1",
        name="Ada Lovelace",
        birth_date=date(2000, 1, 2),
        natal_ascendant_sign=5,
    )

    denotation = synthesize(subject)
    agency = [
        claim
        for claims in denotation.claims_by_system.values()
        for claim in claims
        if claim.axis == "domain" and claim.value == "agency"
    ]

    # Both numerology and Vedic asserted domain=agency for this subject.
    assert {c.system for c in agency} == {"numerology", "vedic"}


def test_run_synthesis_produces_an_agreement_gap() -> None:
    """The runner scores authentic agreement against every null control."""
    subjects = [
        SynthesisSubject(
            subject_id="s1",
            name="Ada Lovelace",
            birth_date=date(2000, 1, 2),
            natal_ascendant_sign=5,
            natal_moon_sign=1,
            transit_when="t",
            graha_transit_signs={"saturn": 3, "venus": 1},
        ),
        SynthesisSubject(
            subject_id="s2",
            name="Grace Hopper",
            birth_date=date(1906, 12, 9),
            natal_ascendant_sign=1,
            natal_moon_sign=4,
            transit_when="t",
            graha_transit_signs={"saturn": 6, "mars": 1},
        ),
    ]

    gap = run_synthesis(subjects, seed=7)

    assert set(gap.controls) == {
        "shuffled_systems",
        "decoy_labels",
        "mismatched_pairs",
    }
    assert gap.authentic.subjects == 2
    # A boolean verdict is produced; two synthetic subjects do not clear it.
    assert isinstance(gap.exceeds_every_control, bool)
    assert gap.ontology_hash
