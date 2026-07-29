"""1E-G-REPAIR: the pre-denotational gematria pipeline is fail-closed.

Freezes the defects 1E-G-CLASSIFY found, as regressions. The pipeline must
never again silently truncate in-domain input, never present the legacy fused
table as authoritative, and never resolve an ambiguous token by quietly taking
the first candidate.

For inputs like CHAIM, no "correct" Hebrew result is asserted -- no sourced
scheme exists. The assertions are only that the machinery fail-closes and that
the legacy mapping cannot pass itself off as literal or authoritative Hebrew.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.gematria_orthography import (
    HEBREW_ONLY,
    LATIN_ONLY,
    GematriaScopeError,
    Script,
    ScopeStatus,
    check_scope,
    classify_char,
)
from atlas.validation.denotation.gematria_pipeline import (
    LEGACY_CIPHER_QUARANTINE,
    StageStatus,
    english_ordinal,
    hebrew_gematria,
)
from atlas.validation.denotation.gematria_transliteration import (
    CANDIDATE_STANDARD_VALUES,
    LEGACY_LATIN_TRANSLITERATION,
    HebrewLetter,
    Resolution,
    TransliterationError,
    TransliterationScheme,
    ValueAssignment,
    admitted_transliteration_schemes,
    admitted_value_schemes,
)


HEBREW_SHALOM = "".join(chr(c) for c in (0x05E9, 0x05DC, 0x05D5, 0x05DD))


# ---------------------------------------------------------------------------
# Orthographic scope, fail-closed
# ---------------------------------------------------------------------------


def test_hebrew_input_to_a_latin_scheme_is_not_silently_empty() -> None:
    """The headline defect: Hebrew in, empty out, no signal. No more.

    The legacy hebrew_literal_sequence returned [] here. The scope check now
    reports NO_LICENSED_SYMBOLS with every rejected character named.
    """
    result = check_scope(HEBREW_SHALOM, LATIN_ONLY)

    assert result.scope_status is ScopeStatus.NO_LICENSED_SYMBOLS
    assert result.accepted_symbol_count == 0
    assert result.input_length == 4
    assert len(result.rejected_symbols) == 4
    assert all(script == "hebrew" for _, script in result.rejected_symbols)

    with pytest.raises(GematriaScopeError, match="none within scope"):
        result.require_usable()


def test_empty_and_zero_licensed_are_distinct_states() -> None:
    """Two states the legacy code serialized identically."""
    empty = check_scope("", LATIN_ONLY)
    punctuation = check_scope("!!! ??? ...", LATIN_ONLY)

    assert empty.scope_status is ScopeStatus.EMPTY_INPUT
    assert punctuation.scope_status is ScopeStatus.NO_LICENSED_SYMBOLS
    assert empty.to_dict() != punctuation.to_dict()

    with pytest.raises(GematriaScopeError, match="empty"):
        empty.require_usable()
    with pytest.raises(GematriaScopeError, match="none within scope"):
        punctuation.require_usable()


def test_godel_is_accepted_without_dropping_the_diacritic() -> None:
    """The identity-encoder defect (Godel == Gdel), refused here.

    Normalization strips the combining mark so o-umlaut counts as a Latin o,
    rather than being dropped as out-of-scope. The character survives instead
    of vanishing.
    """
    result = check_scope("Gödel", LATIN_ONLY)

    assert result.scope_status is ScopeStatus.OK
    assert result.accepted_symbol_count == 5
    assert result.rejected_symbols == ()


def test_mixed_script_input_reports_each_rejection() -> None:
    """A Latin+Hebrew string keeps the Latin, names the Hebrew rejections."""
    result = check_scope("ab" + HEBREW_SHALOM, LATIN_ONLY)

    assert result.scope_status is ScopeStatus.OK
    assert result.accepted_symbol_count == 2
    assert len(result.rejected_symbols) == 4


def test_char_classification_uses_unicode_names() -> None:
    """Classification is legible, not a codepoint guess."""
    assert classify_char("a") is Script.LATIN
    assert classify_char(HEBREW_SHALOM[0]) is Script.HEBREW
    assert classify_char("7") is Script.DIGIT
    assert classify_char("!") is Script.OTHER


# ---------------------------------------------------------------------------
# The split: transliteration separate from value, and unsourced
# ---------------------------------------------------------------------------


def test_base_value_assignment_admitted_transliteration_not() -> None:
    """1E-G-SOURCE-A: base values are CLDR-licensed; transliteration stays uncited."""
    assert admitted_transliteration_schemes() == []
    assert admitted_value_schemes() == [CANDIDATE_STANDARD_VALUES]


def test_admitted_base_values_carry_verified_provenance() -> None:
    """The admitted value assignment must name a hashed, located normative source."""
    assert LEGACY_LATIN_TRANSLITERATION.admitted is False
    assert CANDIDATE_STANDARD_VALUES.admitted is True
    assert len(CANDIDATE_STANDARD_VALUES.source_copy_hash) == 64
    assert "CLDR" in CANDIDATE_STANDARD_VALUES.source_locator
    assert "non-injective" in LEGACY_LATIN_TRANSLITERATION.note


def test_transliteration_and_value_are_separately_hashed() -> None:
    """Two artifacts, so each can be cited independently later."""
    translit = LEGACY_LATIN_TRANSLITERATION.scheme_hash()
    value = CANDIDATE_STANDARD_VALUES.scheme_hash()

    assert translit != value
    assert len(translit) == 64 and len(value) == 64


def test_ambiguity_stops_computation_without_a_resolution() -> None:
    """A token with several candidates and no declared choice fail-closes.

    This is how the legacy code manufactured certainty: silent first-match.
    Here it raises.
    """
    ambiguous = TransliterationScheme(
        scheme_id="fx-ambiguous",
        version="0.0.1",
        admitted=False,
        token_map={"x": (HebrewLetter.SAMEKH, HebrewLetter.TAV)},
        canonical={},
        resolution=Resolution.NONE,
        note="fixture",
    )

    assert ambiguous.candidates("x") == (
        HebrewLetter.SAMEKH,
        HebrewLetter.TAV,
    )

    with pytest.raises(TransliterationError, match="ambiguous"):
        ambiguous.resolve("x")


def test_declared_resolution_permits_a_deterministic_choice() -> None:
    """Ambiguity may be resolved only when the scheme says how."""
    resolved = TransliterationScheme(
        scheme_id="fx-resolved",
        version="0.0.1",
        admitted=False,
        token_map={"x": (HebrewLetter.SAMEKH, HebrewLetter.TAV)},
        canonical={"x": HebrewLetter.SAMEKH},
        resolution=Resolution.DECLARED_CANONICAL,
        note="fixture",
    )

    assert resolved.resolve("x") is HebrewLetter.SAMEKH


def test_canonical_must_be_among_candidates() -> None:
    """A declared resolution cannot invent a letter off the candidate list."""
    with pytest.raises(TransliterationError, match="not among its candidates"):
        TransliterationScheme(
            scheme_id="fx-bad",
            version="0.0.1",
            admitted=False,
            token_map={"x": (HebrewLetter.SAMEKH,)},
            canonical={"x": HebrewLetter.TAV},
            resolution=Resolution.DECLARED_CANONICAL,
        )


def test_legacy_collisions_are_visible_in_the_split() -> None:
    """U/V/W -> vav and I/J/Y -> yod, now inspectable rather than hidden."""
    for token in ("u", "v", "w"):
        assert LEGACY_LATIN_TRANSLITERATION.candidates(token) == (
            HebrewLetter.VAV,
        )
    for token in ("i", "j", "y"):
        assert LEGACY_LATIN_TRANSLITERATION.candidates(token) == (
            HebrewLetter.YOD,
        )


# ---------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------


def test_english_ordinal_is_admitted_and_self_contained() -> None:
    """A=1..Z=26 needs no transliteration and no external authority."""
    result = english_ordinal("abc")

    assert result.complete
    assert result.values == (1, 2, 3)
    assert result.total == 6


def test_english_ordinal_fail_closes_on_hebrew() -> None:
    """Even the admitted path refuses out-of-scope input."""
    result = english_ordinal(HEBREW_SHALOM)

    assert not result.complete
    assert result.stage_status is StageStatus.BLOCKED_SCOPE
    assert result.total is None


def test_hebrew_gematria_blocks_without_an_admitted_scheme() -> None:
    """The default Hebrew path produces no number today, by design.

    The registries are empty of admitted schemes, so the pipeline
    fail-closes rather than compute a value no source licenses.
    """
    result = hebrew_gematria(
        "chaim", LEGACY_LATIN_TRANSLITERATION, CANDIDATE_STANDARD_VALUES
    )

    assert not result.complete
    assert result.stage_status is StageStatus.BLOCKED_NO_ADMITTED_SCHEME
    assert result.total is None
    assert "1E-G-SOURCE" in result.detail


def test_chaim_yields_no_authoritative_hebrew_result() -> None:
    """The classification example: no sourced scheme, so no number.

    We do not assert a "correct" Hebrew value -- none is licensed. We assert
    only that the legacy mapping cannot present one.
    """
    result = hebrew_gematria(
        "chaim", LEGACY_LATIN_TRANSLITERATION, CANDIDATE_STANDARD_VALUES
    )

    assert result.total is None


def test_the_machinery_can_compute_when_a_scheme_is_admitted() -> None:
    """Proves the pipeline is correct, not that any scheme is authoritative.

    A fixture scheme flagged admitted lets the Hebrew path run end to end, so
    the block above is the admission gate at work rather than broken plumbing.
    """
    translit = TransliterationScheme(
        scheme_id="fx-admitted",
        version="0.0.1",
        admitted=True,
        token_map={
            "a": (HebrewLetter.ALEPH,),
            "b": (HebrewLetter.BET,),
        },
        canonical={},
        resolution=Resolution.NONE,
    )
    value_scheme = ValueAssignment(
        scheme_id="fx-values",
        version="0.0.1",
        admitted=True,
        values={HebrewLetter.ALEPH: 1, HebrewLetter.BET: 2},
        source_copy_hash="f" * 64,
        source_locator="fixture source; not a real citation",
    )

    result = hebrew_gematria("ab", translit, value_scheme)

    assert result.complete
    assert result.letters == ("aleph", "bet")
    assert result.total == 3


# ---------------------------------------------------------------------------
# Legacy quarantine
# ---------------------------------------------------------------------------


def test_legacy_ciphers_are_quarantined_from_1e() -> None:
    """The misnamed legacy functions are recorded present but forbidden."""
    assert LEGACY_CIPHER_QUARANTINE["present"] is True
    assert LEGACY_CIPHER_QUARANTINE["permitted_in_1E"] is False
    assert "hebrew_literal_sequence" in LEGACY_CIPHER_QUARANTINE["symbols"]


def test_the_legacy_module_still_exists_for_other_callers() -> None:
    """Quarantine is a boundary, not a deletion.

    atlas.ciphers feeds kamea/identity_graph and others; removing it is out
    of scope. If it is ever removed, remove this test with it.
    """
    from atlas import ciphers

    assert hasattr(ciphers, "hebrew_literal_sequence")
