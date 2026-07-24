"""1E-G-SOURCE-A: direct Hebrew orthography and value method.

The first admitted path runs on Hebrew script, sources letter identity to the
Unicode standard (verified here against unicodedata), and stops at identity.
Values are a traditional claim with no source yet, so the pipeline emits
licensed letter identities and fail-closes at the value stage.

The value-method fixtures below are structural: no real gematria source backs
them, and the only admitted method in any assertion is an explicit test
fixture, never the shipped candidate.
"""

from __future__ import annotations

import unicodedata

import pytest

from atlas.validation.denotation.gematria_hebrew import (
    HEBREW_LETTER_IDENTITY,
    HebrewOrthographyError,
    read_hebrew,
)
from atlas.validation.denotation.gematria_orthography import ScopeStatus
from atlas.validation.denotation.gematria_pipeline import direct_hebrew_value
from atlas.validation.denotation.gematria_transliteration import HebrewLetter
from atlas.validation.denotation.gematria_value_method import (
    MISPAR_HECHRACHI_CANDIDATE,
    FinalLetterPolicy,
    NumberComposition,
    ValueMethod,
    ValueMethodError,
    admitted_methods,
)


def _hebrew(*codepoints: int) -> str:
    """Build a Hebrew string from code points, keeping tests ASCII-safe."""
    return "".join(chr(cp) for cp in codepoints)


ALEPH, BET, GIMEL = 0x05D0, 0x05D1, 0x05D2
FINAL_MEM, MEM = 0x05DD, 0x05DE


def _admitted_method() -> ValueMethod:
    """A fixture value method flagged admitted, with a fake source.

    Present only to drive the licensed path end to end. Not a real source.
    """
    return ValueMethod(
        method_id="fixture-admitted",
        alphabet="hebrew-22",
        letter_values={
            HebrewLetter.ALEPH: 1,
            HebrewLetter.BET: 2,
            HebrewLetter.GIMEL: 3,
            HebrewLetter.MEM: 40,
        },
        final_letter_policy=FinalLetterPolicy.SAME_AS_BASE,
        final_values={},
        normalization_policy="strip_niqqud_and_marks",
        word_boundary_policy="whitespace_separated",
        number_composition=NumberComposition.SUM,
        admitted=True,
        source_copy_hash="fixturehash",
        source_locator="fixture p. 1",
    )


# ---------------------------------------------------------------------------
# Letter identity is sourced to Unicode, and verified against it
# ---------------------------------------------------------------------------


# Where the project's letter name differs from Unicode's spelling. Only one:
# the standard spells aleph "ALEF". Recorded explicitly rather than papered
# over, so the verification stays exact.
UNICODE_SPELLING = {"ALEPH": "ALEF"}


def test_identity_table_matches_the_unicode_standard() -> None:
    """The source is executable: every entry checked against unicodedata.

    This is what lets the identity layer be admitted without a paginated
    copy -- the standard it cites verifies it at runtime.
    """
    for char, letter in HEBREW_LETTER_IDENTITY.items():
        name = unicodedata.name(char)
        expected = UNICODE_SPELLING.get(letter.name, letter.name)

        assert "HEBREW LETTER" in name
        # The Unicode name ends in the letter (optionally "FINAL <letter>").
        assert name.split("HEBREW LETTER ")[1].split(" ")[-1] == expected


def test_all_twenty_two_letters_are_present() -> None:
    """The alphabet is complete, finals included."""
    identities = set(HEBREW_LETTER_IDENTITY.values())

    assert len(identities) == 22
    assert len(HEBREW_LETTER_IDENTITY) == 27  # 22 + 5 final forms


def test_final_forms_resolve_to_their_base_letter() -> None:
    """A final mem is a mem -- identity does not distinguish them."""
    reading = read_hebrew(_hebrew(FINAL_MEM))

    assert reading.letters == (HebrewLetter.MEM,)
    assert reading.final_forms == (True,)


# ---------------------------------------------------------------------------
# Scope: Hebrew only, fail-closed
# ---------------------------------------------------------------------------


def test_latin_input_is_blocked_in_the_direct_hebrew_path() -> None:
    """The first admitted Hebrew path cannot be fed Latin by accident."""
    reading = read_hebrew("abc")

    assert reading.orthography.scope_status is (
        ScopeStatus.NO_LICENSED_SYMBOLS
    )
    assert not reading.usable
    assert reading.letters == ()


def test_niqqud_are_stripped_not_valued() -> None:
    """Vowel points carry no letter identity and must not survive."""
    # Aleph followed by a combining qamats (U+05B8).
    reading = read_hebrew(_hebrew(ALEPH, 0x05B8))

    assert reading.letters == (HebrewLetter.ALEPH,)


def test_a_hebrew_nonletter_is_refused_not_skipped() -> None:
    """A Hebrew-block punctuation mark has no identity, so it raises."""
    # U+05C3 HEBREW PUNCTUATION SOF PASUQ -- in block, not a letter.
    with pytest.raises(HebrewOrthographyError, match="no letter identity"):
        read_hebrew(_hebrew(ALEPH, 0x05C3))


# ---------------------------------------------------------------------------
# Values are a separate, unadmitted claim
# ---------------------------------------------------------------------------


def test_no_value_method_is_admitted() -> None:
    """Unicode sources identity, not value; values await a traditional source."""
    assert admitted_methods() == []
    assert MISPAR_HECHRACHI_CANDIDATE.admitted is False


def test_a_method_cannot_be_admitted_without_a_source() -> None:
    """Letter values are a traditional claim and need a traditional source."""
    with pytest.raises(ValueMethodError, match="source copy hash"):
        ValueMethod(
            method_id="x",
            alphabet="hebrew-22",
            letter_values={HebrewLetter.ALEPH: 1},
            final_letter_policy=FinalLetterPolicy.SAME_AS_BASE,
            final_values={},
            normalization_policy="n",
            word_boundary_policy="w",
            number_composition=NumberComposition.SUM,
            admitted=True,
            source_copy_hash="",
            source_locator="",
        )


def test_method_hash_covers_every_choice() -> None:
    """Two methods differing in any field are different objects."""
    base = MISPAR_HECHRACHI_CANDIDATE

    extended = ValueMethod(
        method_id=base.method_id,
        alphabet=base.alphabet,
        letter_values=base.letter_values,
        final_letter_policy=FinalLetterPolicy.EXTENDED_500_900,
        final_values={HebrewLetter.KAF: 500},
        normalization_policy=base.normalization_policy,
        word_boundary_policy=base.word_boundary_policy,
        number_composition=base.number_composition,
        admitted=False,
        source_copy_hash="",
        source_locator="",
    )

    assert base.method_hash() != extended.method_hash()
    assert len(base.method_hash()) == 64


# ---------------------------------------------------------------------------
# The endpoint: identities licensed, value fail-closed
# ---------------------------------------------------------------------------


def test_default_path_licenses_identity_but_not_value() -> None:
    """The honest first result of 1E-G-SOURCE-A."""
    result = direct_hebrew_value(
        _hebrew(ALEPH, BET, GIMEL), MISPAR_HECHRACHI_CANDIDATE
    )

    assert result["letters"] == ["aleph", "bet", "gimel"]
    assert result["letter_identity_licensed"] is True
    assert result["complete"] is False
    assert result["total"] is None
    assert "no admitted value method" in result["detail"]


def test_acceptance_licensed_path_is_reproducible() -> None:
    """The acceptance test, run with a fixture-admitted method.

    Given verified Hebrew input and a source-backed value method, the pipeline
    reproducibly emits the same letter identities, values, total, method hash
    and provenance. This proves the block above is the admission gate at work,
    not broken plumbing.
    """
    text = _hebrew(ALEPH, BET, GIMEL)
    method = _admitted_method()

    first = direct_hebrew_value(text, method)
    second = direct_hebrew_value(text, method)

    assert first == second
    assert first["complete"] is True
    assert first["letters"] == ["aleph", "bet", "gimel"]
    assert first["values"] == [1, 2, 3]
    assert first["total"] == 6
    assert first["method_provenance"]["method_hash"] == method.method_hash()
    assert first["method_provenance"]["admitted"] is True


def test_licensed_path_fail_closes_on_latin() -> None:
    """Even with an admitted method, Latin input is out of scope."""
    result = direct_hebrew_value("abc", _admitted_method())

    assert result["complete"] is False
    assert result["total"] is None


# ---------------------------------------------------------------------------
# Capability distinction: identity vs evaluability
# ---------------------------------------------------------------------------


def test_capabilities_separate_identity_from_value() -> None:
    """The key result as a flag set, not a general availability status."""
    from atlas.validation.denotation.gematria_capabilities import (
        derive_gematria_capabilities,
    )

    caps = derive_gematria_capabilities()

    assert caps.hebrew_letter_identity_available is True
    assert caps.value_method_available is False
    assert caps.numeric_evaluation_available is False
    assert caps.equivalence_search_available is False
    assert caps.denotation_available is False


def test_downstream_flags_require_upstream_ones() -> None:
    """Numeric evaluation cannot be available while value is not."""
    from atlas.validation.denotation.gematria_capabilities import (
        derive_gematria_capabilities,
    )

    caps = derive_gematria_capabilities()

    # value is false, so everything that depends on it must be false too.
    assert not caps.value_method_available
    assert not caps.numeric_evaluation_available
    assert not caps.equivalence_search_available


def test_capabilities_carry_the_boundary_statement() -> None:
    """The identity/value boundary travels in the artifact."""
    from atlas.validation.denotation.gematria_capabilities import (
        derive_gematria_capabilities,
    )

    payload = derive_gematria_capabilities().to_dict()

    assert "what a tradition says that symbol is worth" in payload["boundary"]
    assert len(payload["orthography_standard_hash"]) == 64


# ---------------------------------------------------------------------------
# A total never serializes without both hashes
# ---------------------------------------------------------------------------


def test_a_total_carries_both_provenance_hashes() -> None:
    """The licensed path names both the standard and the tradition."""
    result = direct_hebrew_value(_hebrew(ALEPH, BET, GIMEL), _admitted_method())

    assert result["total"] == 6
    assert len(result["orthography_standard_hash"]) == 64
    assert len(result["value_method_hash"]) == 64


def test_a_blocked_result_carries_identity_hash_but_no_total() -> None:
    """Unicode-only: an identity hash, and never a number."""
    result = direct_hebrew_value(
        _hebrew(ALEPH, BET, GIMEL), MISPAR_HECHRACHI_CANDIDATE
    )

    assert result["total"] is None
    assert "value_method_hash" not in result
    assert len(result["orthography_standard_hash"]) == 64


def test_a_total_without_both_hashes_is_refused() -> None:
    """The structural guard fires if a total ever loses a hash.

    Simulates a future edit that produces a total while dropping the value
    method hash; the pipeline refuses to present it.
    """
    from atlas.validation.denotation.gematria_pipeline import (
        GematriaPipelineError,
        _assert_dual_provenance,
    )

    with pytest.raises(GematriaPipelineError, match="value method hash"):
        _assert_dual_provenance(
            {"total": 6, "orthography_standard_hash": "abc"}
        )

    with pytest.raises(GematriaPipelineError, match="identity source"):
        _assert_dual_provenance({"total": 6})
