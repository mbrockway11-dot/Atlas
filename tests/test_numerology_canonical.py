"""The canonical numerology binding is bound to the verified corpus.

These pin that "the numerology dictionary" is a discoverable artifact bound to
the admitted, copy-verified corpus (v2) -- not something each caller re-derives
-- and that it is concordance-eligible and deterministic.
"""

from __future__ import annotations

from datetime import date

from atlas.validation.denotation.expressions import (
    DenotationClaim,
    assemble_subject,
)
from atlas.validation.denotation.concordance import subject_verdicts
from atlas.validation.denotation.numerology_canonical import (
    CANONICAL_CORPUS_ID,
    canonical_corpus,
    canonical_dictionary,
    canonical_manifest,
    is_concordance_eligible,
)
from atlas.validation.denotation.numerology_dictionary import (
    claim_from_expression,
)
from atlas.validation.denotation.numerology_expression import (
    build_expressions,
)


def test_canonical_corpus_is_the_admitted_v2() -> None:
    """The binding points at the copy-verified corpus, by id."""
    assert canonical_corpus().corpus_id == "numerology-corpus-v2"
    assert CANONICAL_CORPUS_ID == "numerology-corpus-v2"


def test_canonical_dictionary_binds_nine_sourced_denotations() -> None:
    """Compiling the bound corpus yields the nine Jordan denotations."""
    dictionary, report = canonical_dictionary()

    assert report.entries_emitted == 9
    assert report.rejections == {}
    assert len(dictionary.entries) == 9


def test_canonical_binding_is_concordance_eligible() -> None:
    """The health assertion the wiring exists to make true."""
    assert is_concordance_eligible() is True

    manifest = canonical_manifest()

    assert manifest["concordance_eligible"] is True
    assert manifest["entries"] == 9
    assert manifest["blocking"] == []


def test_canonical_dictionary_is_deterministic() -> None:
    """Same corpus and rules produce a byte-identical dictionary hash."""
    first, _ = canonical_dictionary()
    second, _ = canonical_dictionary()

    assert first.dictionary_hash() == second.dictionary_hash()


def test_bound_dictionary_drives_a_cross_system_verdict() -> None:
    """End to end: the bound dictionary feeds a real concordance verdict.

    A subject whose life path reduces to 5 lands on dynamic=expansion via the
    bound numerology dictionary; paired with a Kamea dynamic claim it produces
    a genuine cross-system relation, which only became possible once a second
    system was admitted at denotation.
    """
    dictionary, _ = canonical_dictionary()
    subject_id = "canonical-wiring-check"

    numerology_claims = [
        claim
        for expression in build_expressions(
            "Ada Lovelace", date(2000, 1, 2)
        ).values()
        if (
            claim := claim_from_expression(
                expression, dictionary, subject_id
            )
        )
        is not None
    ]

    assert any(
        claim.axis == "dynamic" and claim.value == "expansion"
        for claim in numerology_claims
    )

    kamea_claim = DenotationClaim(
        system="kamea",
        subject_id=subject_id,
        axis="dynamic",
        value="expansion",
        polarity="positive",
        temporal_scope="natal",
        mapping_kind="direct",
        confidence=0.9,
        source_basis="kamea:measured-trajectory",
    )

    subject = assemble_subject(
        subject_id,
        {"numerology": numerology_claims, "kamea": [kamea_claim]},
    )

    verdicts = subject_verdicts(subject)
    dynamic = [v for v in verdicts if v.axis == "dynamic"]

    assert dynamic
    assert any(v.agrees for v in dynamic)
