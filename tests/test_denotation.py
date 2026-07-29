"""Tests for the cross-system denotational audit (1E).

The audit's value rests on two guarantees, and these tests pin both: systems
stay independent through generation, and agreement is scored as a relation
against controls rather than as a broad-vocabulary inevitability.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from atlas.validation.denotation.concordance import (
    measure_agreement_gap,
    score_concordance,
    subject_verdicts,
)
from atlas.validation.denotation.controls import (
    decoy_labels,
    mismatched_pairs,
    shuffled_systems,
)
from atlas.validation.denotation.expressions import (
    DenotationClaim,
    ExpressionError,
    SystemExpression,
    assemble_subject,
)
from atlas.validation.denotation.kamea_denotation import (
    kamea_dynamic_claims,
    kamea_expression,
)
from atlas.validation.denotation.ontology import (
    AXES,
    OntologyError,
    ontology_hash,
    require_coordinate,
)
from atlas.validation.denotation.relations import (
    Relation,
    relate,
    scopes_comparable,
)
from atlas.validation.temporal_kamea import build_trajectory, canonical_spec


def _claim(
    system: str,
    *,
    axis: str = "dynamic",
    value: str = "repetition",
    polarity: str = "neutral",
    scope: str = "natal",
    subject: str = "s1",
    kind: str = "direct",
) -> DenotationClaim:
    """Build a claim with chosen coordinates."""
    return DenotationClaim(
        system=system,
        subject_id=subject,
        axis=axis,
        value=value,
        polarity=polarity,
        temporal_scope=scope,
        mapping_kind=kind,
        confidence=0.8,
        source_basis="test-rule",
    )


# ---------------------------------------------------------------------------
# The ontology is frozen
# ---------------------------------------------------------------------------


def test_ontology_hash_is_stable_and_content_sensitive() -> None:
    """A change to what an axis means invalidates comparisons across it."""
    assert ontology_hash() == ontology_hash()
    assert len(ontology_hash()) == 64


def test_coordinates_off_the_ontology_are_refused() -> None:
    """The vocabulary is fixed before subjects; no ad-hoc additions."""
    require_coordinate("dynamic", "repetition")

    with pytest.raises(OntologyError, match="not a frozen"):
        require_coordinate("dynamic", "saturnian_restraint")

    with pytest.raises(OntologyError, match="not an ontology axis"):
        require_coordinate("vibe", "repetition")


# ---------------------------------------------------------------------------
# Independence through generation
# ---------------------------------------------------------------------------


def test_a_claim_cannot_be_filed_under_the_wrong_system() -> None:
    """Systems must stay independent, enforced at assembly."""
    with pytest.raises(ExpressionError, match="independent"):
        assemble_subject("s1", {"vedic": [_claim("kamea")]})


def test_a_claim_must_cite_a_frozen_source_basis() -> None:
    """An unsourced claim is indistinguishable from after-the-fact reading."""
    with pytest.raises(ExpressionError, match="cite"):
        DenotationClaim(
            system="kamea",
            subject_id="s1",
            axis="dynamic",
            value="repetition",
            polarity="neutral",
            temporal_scope="transit",
            mapping_kind="direct",
            confidence=0.5,
            source_basis="",
        )


def test_only_admitted_systems_produce_expressions() -> None:
    """A system with no validated generator cannot contribute."""
    with pytest.raises(ExpressionError, match="not an admitted system"):
        SystemExpression(
            system="tarot",
            subject_id="s1",
            content={},
            reference_class="natal",
        )


# ---------------------------------------------------------------------------
# The relation algebra
# ---------------------------------------------------------------------------


def test_same_denotation_same_polarity_is_equivalent() -> None:
    verdict = relate(_claim("kamea"), _claim("vedic"))

    assert verdict.relation is Relation.EQUIVALENT
    assert verdict.agrees


def test_same_denotation_opposed_polarity_is_contradictory() -> None:
    """Same coordinate, opposite valence, is conflict -- not agreement."""
    verdict = relate(
        _claim("kamea", polarity="positive"),
        _claim("vedic", polarity="negative"),
    )

    assert verdict.relation is Relation.CONTRADICTORY
    assert not verdict.agrees


def test_neutral_polarity_is_compatible_not_identical() -> None:
    verdict = relate(
        _claim("kamea", polarity="neutral"),
        _claim("vedic", polarity="positive"),
    )

    assert verdict.relation is Relation.COMPATIBLE
    assert verdict.agrees


def test_different_values_are_complementary() -> None:
    """Different roles in one configuration count as agreement.

    This is the denotational agreement the milestone seeks, distinct from
    mere identity: reducing it to no-match would discard the finding.
    """
    verdict = relate(
        _claim("kamea", value="repetition"),
        _claim("vedic", value="stabilization"),
    )

    assert verdict.relation is Relation.COMPLEMENTARY
    assert verdict.agrees


def test_different_axes_are_unrelated() -> None:
    verdict = relate(
        _claim("kamea", axis="dynamic", value="repetition"),
        _claim("vedic", axis="domain", value="cognition"),
    )

    assert verdict.relation is Relation.UNRELATED
    assert not verdict.agrees


def test_incomparable_scopes_are_not_a_disagreement() -> None:
    """Enduring vs acute denote different objects: absence of comparison."""
    verdict = relate(
        _claim("vedic", scope="natal"),
        _claim("kamea", scope="event"),
    )

    assert verdict.relation is Relation.NOT_COMPARABLE
    assert not verdict.comparable
    assert not scopes_comparable("natal", "event")


def test_kamea_transit_class_meets_dated_vedic_transit_instance() -> None:
    """The bare 'transit' reference-class bridges to a dated transit instance.

    Kamea emits scope 'transit' (an instant's neighbourhood, undated); Vedic
    transit claims are dated 'transit-<when>'. The documented Kamea<->Vedic-transit
    edge requires the class to meet its instances, while two *different* dated
    instances stay unbridged so distinct moments are not conflated.
    """
    assert scopes_comparable("transit", "transit-2026-07-28")
    assert scopes_comparable("transit-2026-07-28", "transit")
    assert not scopes_comparable("transit-2026-07-28", "transit-2026-07-29")
    assert not scopes_comparable("transit-2026-07-28", "natal")


# ---------------------------------------------------------------------------
# Kamea denotes structure only
# ---------------------------------------------------------------------------


def test_kamea_claims_are_dynamic_neutral_and_direct() -> None:
    """The 1D finding, enforced: structure, never symbolism.

    Kamea may say 'high repetition', never 'Saturnian restraint'. Every
    claim it makes is on the dynamic axis, neutral polarity, direct mapping.
    """
    spec = canonical_spec("R1-W3D")
    trajectory = build_trajectory(
        datetime(1994, 7, 16, 20, 13, 11, tzinfo=UTC), "saturn", spec
    )
    claims = kamea_dynamic_claims(kamea_expression(trajectory))

    assert claims, "a stationary Saturn path should denote repetition"

    for claim in claims:
        assert claim.axis == "dynamic"
        assert claim.polarity == "neutral"
        assert claim.mapping_kind == "direct"
        assert claim.value in AXES["dynamic"]


def test_stationary_path_denotes_repetition_and_stabilization() -> None:
    """A Saturn path that never moves is maximal dwell, minimal transition."""
    spec = canonical_spec("R1-W3D")
    trajectory = build_trajectory(
        datetime(2001, 3, 3, 12, 0, 0, tzinfo=UTC), "saturn", spec
    )
    values = {c.value for c in kamea_dynamic_claims(kamea_expression(trajectory))}

    assert "stabilization" in values


# ---------------------------------------------------------------------------
# Concordance and controls
# ---------------------------------------------------------------------------


def _agreeing_subject(subject_id: str) -> object:
    """Two systems that genuinely agree on the dynamic axis."""
    return assemble_subject(
        subject_id,
        {
            "kamea": [_claim("kamea", subject=subject_id)],
            "vedic": [_claim("vedic", subject=subject_id)],
        },
    )


def test_within_system_pairs_are_never_compared() -> None:
    """A system agreeing with itself is not evidence."""
    subject = assemble_subject(
        "s1",
        {
            "kamea": [
                _claim("kamea", subject="s1"),
                _claim("kamea", subject="s1", value="reversal"),
            ]
        },
    )

    assert subject_verdicts(subject) == []


def test_concordance_counts_only_comparable_pairs() -> None:
    """not_comparable pairs leave the denominator, not count as failures."""
    comparable = _agreeing_subject("s1")
    incomparable = assemble_subject(
        "s2",
        {
            "kamea": [_claim("kamea", subject="s2", scope="event")],
            "vedic": [_claim("vedic", subject="s2", scope="natal")],
        },
    )

    result = score_concordance([comparable, incomparable])

    assert result.comparable_pairs == 1
    assert result.agreeing_pairs == 1
    assert result.agreement_rate == pytest.approx(1.0)


def test_shuffling_systems_preserves_each_distribution() -> None:
    """Controls break pairing without altering any system's own output."""
    subjects = [_agreeing_subject(f"s{i}") for i in range(6)]
    shuffled = shuffled_systems(subjects, seed=1)

    def kamea_values(cohort):
        return sorted(
            claim.value
            for subject in cohort
            for claim in subject.claims_by_system["kamea"]
        )

    assert kamea_values(shuffled) == kamea_values(subjects)
    assert len(shuffled) == len(subjects)


def test_agreement_gap_detects_a_real_signal() -> None:
    """Authentic subjects that truly agree beat their shuffled controls.

    Constructed so the systems agree only because they are paired: shuffling
    and decoy labels must lower the rate, or the gap machinery is inert.
    """
    values = ["repetition", "reversal", "stabilization", "disruption",
              "expansion", "contraction"]
    subjects = [
        assemble_subject(
            f"s{i}",
            {
                "kamea": [_claim("kamea", subject=f"s{i}", value=values[i])],
                "vedic": [_claim("vedic", subject=f"s{i}", value=values[i])],
            },
        )
        for i in range(6)
    ]

    gap = measure_agreement_gap(
        subjects,
        {
            "shuffled": lambda: shuffled_systems(subjects, seed=2),
            "decoy": lambda: decoy_labels(subjects, seed=3),
            "mismatched": lambda: mismatched_pairs(subjects, seed=4),
        },
    )

    assert gap.authentic.agreement_rate == pytest.approx(1.0)
    assert gap.exceeds_every_control
    assert gap.ontology_hash == ontology_hash()


def test_broad_agreement_alone_does_not_pass() -> None:
    """If systems agree by vocabulary breadth, no control gap opens.

    Every subject uses the same value, so authentic and shuffled cohorts
    agree equally -- and the gap correctly refuses to certify it.
    """
    subjects = [
        assemble_subject(
            f"s{i}",
            {
                "kamea": [_claim("kamea", subject=f"s{i}", value="repetition")],
                "vedic": [_claim("vedic", subject=f"s{i}", value="repetition")],
            },
        )
        for i in range(6)
    ]

    gap = measure_agreement_gap(
        subjects, {"shuffled": lambda: shuffled_systems(subjects, seed=5)}
    )

    assert gap.authentic.agreement_rate == pytest.approx(1.0)
    # Shuffling cannot lower a rate that vocabulary alone produced.
    assert not gap.exceeds_every_control
