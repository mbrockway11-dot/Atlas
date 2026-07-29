"""The acquired Vedic graha corpus is bound to the verified BPHS copy.

Mirrors the numerology canonical tests. The seven classical grahas' karakatva
compile from a copy-verified Brihat Parasara Hora Shastra, the dictionary is
concordance-eligible and deterministic, and it feeds a real cross-system verdict
through the lagna-lord quantity.
"""

from __future__ import annotations

from atlas.validation.denotation.concordance import subject_verdicts
from atlas.validation.denotation.expressions import (
    DenotationClaim,
    assemble_subject,
)
from atlas.validation.denotation.vedic_denotation import claim_from_expression
from atlas.validation.denotation.vedic_denotation_bphs import (
    BPHS_SANTHANAM,
    acquired_corpus,
    canonical_dictionary,
    is_concordance_eligible,
)
from atlas.validation.denotation.vedic_grahas import lagna_lord_expression


def test_acquired_corpus_is_copy_verified() -> None:
    """The BPHS manifestation is transcription-eligible from its own pages."""
    assert BPHS_SANTHANAM.transcription_eligible is True
    assert BPHS_SANTHANAM.publication_year == 1984
    assert BPHS_SANTHANAM.oclc == "12808639"


def test_seven_grahas_compile_from_the_verse() -> None:
    """The defining verse 12-13 yields the seven star-planets' karakatva."""
    dictionary = canonical_dictionary()

    grahas = {entry.graha for entry in dictionary.entries}

    assert grahas == {
        "sun",
        "moon",
        "mars",
        "mercury",
        "jupiter",
        "venus",
        "saturn",
    }
    # The nodes rule no sign, so they never appear as a lagna lord; their
    # absence is complete coverage for v1, not a gap.
    assert "rahu" not in grahas
    assert "ketu" not in grahas


def test_every_graha_mapping_is_interpretive_and_valid() -> None:
    """Each mapping is a flagged interpretive placement on a real coordinate."""
    for entry in canonical_dictionary().entries:
        assert entry.mapping_kind == "interpretive"
        assert entry.polarity in ("positive", "negative", "neutral")


def test_acquired_corpus_is_concordance_eligible() -> None:
    """The health assertion the acquisition exists to make true."""
    assert is_concordance_eligible() is True


def test_canonical_dictionary_is_deterministic() -> None:
    """Same corpus produces a byte-identical dictionary hash."""
    assert (
        canonical_dictionary().dictionary_hash()
        == canonical_dictionary().dictionary_hash()
    )


def test_passages_are_doubly_transcribed_and_agree() -> None:
    """Two independent renderings, hash-agreeing, from the page-11 verse."""
    for passage in acquired_corpus().passages:
        assert passage.doubly_transcribed
        assert passage.transcriptions_agree
        assert passage.printed_page == "11"


def test_lagna_lord_feeds_a_cross_system_verdict() -> None:
    """End to end: a Vedic claim from the sourced dictionary meets a Kamea one.

    A Leo ascendant makes the Sun the lagna lord; the sourced karakatva places
    it on domain=agency. Paired with a Kamea agency claim it produces a genuine
    cross-system relation -- possible only now that a third system denotes.
    """
    dictionary = canonical_dictionary()
    subject_id = "vedic-wiring-check"

    # ~125 deg sidereal ascendant -> Leo -> lord Sun.
    expression = lagna_lord_expression(125.0)
    assert expression.graha == "sun"

    vedic_claim = claim_from_expression(expression, dictionary, subject_id)
    assert vedic_claim is not None
    assert (vedic_claim.axis, vedic_claim.value) == ("domain", "agency")

    kamea_claim = DenotationClaim(
        system="kamea",
        subject_id=subject_id,
        axis="domain",
        value="agency",
        polarity="neutral",
        temporal_scope="natal",
        mapping_kind="direct",
        confidence=0.9,
        source_basis="kamea:measured-trajectory",
    )

    subject = assemble_subject(
        subject_id, {"vedic": [vedic_claim], "kamea": [kamea_claim]}
    )

    verdicts = subject_verdicts(subject)
    domain = [v for v in verdicts if v.axis == "domain"]

    assert domain
    assert any(v.agrees for v in domain)
