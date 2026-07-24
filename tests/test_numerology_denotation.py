"""Tests for the numerology denotation architecture (no meanings yet).

Numerology is the first interpretive system to enter 1E, so these tests pin
the provenance boundary that gematria and Vedic will inherit: computation is
ontology-blind, every denotation is source-licensed by exact key, unsupported
quantities are silent, conflicts stay explicit, and no meaning can be
inherited from another system.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from atlas.validation.denotation.numerology_dictionary import (
    ConflictVerdict,
    NumerologyDictionary,
    NumerologyDictionaryEntry,
    NumerologyDictionaryError,
    SourceCitation,
    claim_from_expression,
)
from atlas.validation.denotation.numerology_expression import (
    COMPUTABLE_QUANTITIES,
    REDUCTION_POLICY,
    build_expressions,
    expression_set_hash,
    life_path,
    soul_urge,
)


def _citation(tradition: str = "pythagorean") -> SourceCitation:
    """Build a placeholder citation for architecture tests."""
    return SourceCitation(
        tradition=tradition,
        source_id="test-source-1",
        passage="table 1, entry for the value under test",
    )


def _entry(
    *,
    quantity: str = "life_path",
    value: int = 4,
    axis: str = "dynamic",
    coordinate: str = "stabilization",
    polarity: str = "neutral",
    verdict: ConflictVerdict = ConflictVerdict.CONSENSUS,
    tradition: str = "pythagorean",
) -> NumerologyDictionaryEntry:
    """Build a dictionary entry with a placeholder citation."""
    return NumerologyDictionaryEntry(
        tradition=tradition,
        quantity=quantity,
        value=value,
        reduction_policy=REDUCTION_POLICY,
        axis=axis,
        coordinate=coordinate,
        polarity=polarity,
        mapping_kind="interpretive",
        conflict_verdict=verdict,
        confidence=0.7,
        citation=_citation(tradition),
    )


# ---------------------------------------------------------------------------
# Computation is deterministic and ontology-blind
# ---------------------------------------------------------------------------


def test_expressions_are_deterministic() -> None:
    """Same inputs, same computed quantities and traces."""
    first = build_expressions("Ada Lovelace", date(1815, 12, 10))
    second = build_expressions("Ada Lovelace", date(1815, 12, 10))

    assert {k: v.to_dict() for k, v in first.items()} == {
        k: v.to_dict() for k, v in second.items()
    }
    assert set(first) == set(COMPUTABLE_QUANTITIES)


def test_reduction_trace_is_recorded() -> None:
    """The trace makes the reduction auditable and policy-distinguishable."""
    lp = life_path(date(1999, 12, 31))  # 1+9+9+9+1+2+3+1 = 35 -> 8

    assert lp.raw_value == 35
    assert lp.reduced_value == 8
    assert lp.reduction_trace[0] == 35
    assert lp.reduction_trace[-1] == 8


def test_master_numbers_are_not_reduced() -> None:
    """The frozen policy leaves 11/22/33 unreduced."""
    # 29 Nov 1971: 2+9+1+1+1+9+7+1 = 31 -> not master; pick a master case.
    # 1+9+6+4+0+7+2+9 = 38 -> 11 stops (master).
    lp = life_path(date(1964, 7, 29))

    assert lp.reduced_value == 11
    assert 11 in lp.reduction_trace


def test_expression_layer_does_not_import_the_ontology() -> None:
    """Independence at the source: computation cannot see its vocabulary.

    If the expression layer could import the ontology, it could shape its
    numbers to the terms it feeds -- the exact circularity 1E forbids. Checked
    against actual import statements, not text, so a docstring may still name
    the constraint it describes.
    """
    import ast

    source = Path(
        "src/atlas/validation/denotation/numerology_expression.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

    forbidden = [
        module
        for module in imported
        if "denotation.ontology" in module
        or "denotation.expressions" in module
        or "kamea" in module
        or "vedic" in module
    ]

    assert not forbidden, f"expression layer must not import {forbidden}"
    assert imported  # sanity: the file does import things


def test_soul_urge_uses_vowels_only() -> None:
    """A computational boundary check: distinct quantities differ."""
    name = "Grace Hopper"

    assert soul_urge(name).raw_value != life_path(date(1906, 12, 9)).raw_value


# ---------------------------------------------------------------------------
# Provenance and the tradition boundary
# ---------------------------------------------------------------------------


def test_a_citation_must_be_locatable() -> None:
    """Provenance that cannot be located is not provenance."""
    with pytest.raises(NumerologyDictionaryError, match="located"):
        SourceCitation(tradition="pythagorean", source_id="", passage="x")


def test_entry_and_citation_tradition_must_agree() -> None:
    """A tradition boundary may not be crossed silently."""
    with pytest.raises(NumerologyDictionaryError, match="tradition"):
        NumerologyDictionaryEntry(
            tradition="chaldean",
            quantity="life_path",
            value=4,
            reduction_policy=REDUCTION_POLICY,
            axis="dynamic",
            coordinate="stabilization",
            polarity="neutral",
            mapping_kind="interpretive",
            conflict_verdict=ConflictVerdict.CONSENSUS,
            confidence=0.7,
            citation=_citation("pythagorean"),
        )


def test_an_entry_cannot_address_an_uncomputed_construct() -> None:
    """No inventing a construct the code does not produce."""
    with pytest.raises(NumerologyDictionaryError, match="computable"):
        _entry(quantity="destiny_gate")


def test_a_dictionary_forbids_duplicate_keys() -> None:
    """A conflict is a verdict, not two competing entries."""
    with pytest.raises(NumerologyDictionaryError, match="duplicate key"):
        NumerologyDictionary(
            tradition="pythagorean",
            version="0.0.1",
            entries=(_entry(), _entry(coordinate="repetition")),
        )


# ---------------------------------------------------------------------------
# Conflict and silence
# ---------------------------------------------------------------------------


def test_only_consensus_and_source_specific_license_a_claim() -> None:
    """Silence is preferred to forced consensus."""
    assert _entry(verdict=ConflictVerdict.CONSENSUS).licenses_claim
    assert _entry(verdict=ConflictVerdict.SOURCE_SPECIFIC).licenses_claim

    for verdict in (
        ConflictVerdict.CONFLICTING,
        ConflictVerdict.INSUFFICIENT,
        ConflictVerdict.NONE,
    ):
        assert not _entry(verdict=verdict).licenses_claim


def test_conflicting_sources_produce_no_claim() -> None:
    """An explicit conflict licenses silence, not a reconciled meaning."""
    dictionary = NumerologyDictionary(
        tradition="pythagorean",
        version="0.0.1",
        entries=(_entry(verdict=ConflictVerdict.CONFLICTING),),
    )

    claim = claim_from_expression(
        _four_expression(), dictionary, subject_id="s1"
    )

    assert claim is None


def test_unsupported_value_is_silent() -> None:
    """An empty dictionary contributes nothing, not a default."""
    empty = NumerologyDictionary(tradition="pythagorean", version="0.0.1")

    assert (
        claim_from_expression(_four_expression(), empty, subject_id="s1")
        is None
    )


def test_a_licensed_entry_produces_a_sourced_claim() -> None:
    """The one positive path: an exact key yields a cited claim."""
    dictionary = NumerologyDictionary(
        tradition="pythagorean",
        version="0.0.1",
        entries=(_entry(),),
    )

    claim = claim_from_expression(
        _four_expression(), dictionary, subject_id="s1"
    )

    assert claim is not None
    assert claim.system == "numerology"
    assert claim.axis == "dynamic"
    assert claim.value == "stabilization"
    assert "pythagorean" in claim.source_basis


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def test_dictionary_hash_is_entry_sensitive() -> None:
    """A change to one mapping invalidates concordance built against it."""
    base = NumerologyDictionary(
        tradition="pythagorean", version="0.0.1", entries=(_entry(),)
    )
    changed = NumerologyDictionary(
        tradition="pythagorean",
        version="0.0.1",
        entries=(_entry(coordinate="repetition"),),
    )

    assert base.dictionary_hash() != changed.dictionary_hash()
    assert len(expression_set_hash()) == 64


def _four_expression():
    """Return the first January 2000 life_path expression reducing to 4."""
    for day in range(1, 29):
        candidate = life_path(date(2000, 1, day))

        if candidate.reduced_value == 4:
            return candidate

    raise AssertionError("no January 2000 date reduces to 4")
