"""Tests for corpus -> admissibility -> dictionary compilation.

The dictionary is derived, never authored, so these tests pin the derivation:
only direct denotations are eligible, disagreement compiles to silence rather
than to a reconciled meaning, and the same corpus under the same rules always
produces the same dictionary.

Every passage here is a **fixture with an invented citation**, present to
exercise the compiler. None is a real numerological source, and no fixture
meaning reaches the shipped package.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    compile_dictionary,
)
from atlas.validation.denotation.numerology_corpus import (
    AuthorityScope,
    CorpusError,
    SemanticGranularity,
    SourcePassage,
    SourceType,
    build_corpus,
)
from atlas.validation.denotation.numerology_dictionary import ConflictVerdict


def _passage(
    passage_id: str,
    *,
    quantity: str = "life_path",
    value: int = 4,
    axis: str = "dynamic",
    coordinate: str = "stabilization",
    polarity: str = "neutral",
    granularity: SemanticGranularity = (
        SemanticGranularity.DIRECT_DENOTATION
    ),
    source_type: SourceType = SourceType.PRIMARY,
    scope: AuthorityScope = AuthorityScope.TRADITION_WIDE,
    confidence: float = 0.8,
    tradition: str = "fixture-tradition",
) -> SourcePassage:
    """Build a fixture passage. Not a real citation."""
    return SourcePassage(
        passage_id=passage_id,
        tradition=tradition,
        author="Fixture Author",
        work="Fixture Work",
        edition="1st",
        locator="p. 1",
        quotation="fixture quotation for compiler tests",
        granularity=granularity,
        source_type=source_type,
        authority_scope=scope,
        quantity=quantity,
        value=value,
        axis=axis,
        coordinate=coordinate,
        polarity=polarity,
        confidence=confidence,
    )


def _compile(passages, rules=None):
    """Compile fixture passages under default or supplied rules."""
    return compile_dictionary(
        build_corpus(passages),
        rules or AdmissibilityRules(),
        tradition="fixture-tradition",
        version="0.0.1",
    )


# ---------------------------------------------------------------------------
# The corpus is bibliographic evidence
# ---------------------------------------------------------------------------


def test_a_passage_needs_locatable_bibliography() -> None:
    """A citation that cannot be located is not evidence."""
    with pytest.raises(CorpusError, match="missing bibliography"):
        SourcePassage(
            passage_id="p1",
            tradition="fixture-tradition",
            author="",
            work="Fixture Work",
            edition="1st",
            locator="p. 1",
            quotation="fixture quotation",
            granularity=SemanticGranularity.DIRECT_DENOTATION,
            source_type=SourceType.PRIMARY,
            authority_scope=AuthorityScope.TRADITION_WIDE,
            quantity="life_path",
            value=4,
            axis="dynamic",
            coordinate="stabilization",
            polarity="neutral",
            confidence=0.8,
        )


def test_passage_ids_are_unique() -> None:
    """Each citation must be individually addressable."""
    with pytest.raises(CorpusError, match="duplicate passage_id"):
        build_corpus([_passage("p1"), _passage("p1", value=5)])


def test_corpus_ordering_is_deterministic() -> None:
    """Insertion order must not affect compilation."""
    forward = build_corpus([_passage("p1"), _passage("p2", value=5)])
    reverse = build_corpus([_passage("p2", value=5), _passage("p1")])

    assert forward.corpus_hash() == reverse.corpus_hash()


# ---------------------------------------------------------------------------
# Semantic granularity
# ---------------------------------------------------------------------------


def test_only_direct_denotations_are_eligible() -> None:
    """A behavioral claim wearing a denotation's clothes is refused.

    "4 signifies stability" is eligible; "people with 4 become reliable
    administrators" is a prediction and waits for 1E-B.
    """
    rules = AdmissibilityRules()

    assert rules.admits(_passage("p1"))

    for granularity in (
        SemanticGranularity.PREDICTION,
        SemanticGranularity.RECOMMENDATION,
        SemanticGranularity.ANALOGY,
        SemanticGranularity.CORRESPONDENCE,
        SemanticGranularity.COMMENTARY,
    ):
        assert not rules.admits(_passage("p1", granularity=granularity))


def test_inadmissible_granularity_yields_silence_with_a_reason() -> None:
    """Sparse coverage must be explicable, not mysterious."""
    dictionary, report = _compile(
        [_passage("p1", granularity=SemanticGranularity.PREDICTION)]
    )

    assert dictionary.entries == ()
    assert report.verdicts[ConflictVerdict.INSUFFICIENT.value] == 1
    assert "not eligible" in report.rejections["life_path=4"][0]


def test_secondary_synthesis_is_excluded_by_default() -> None:
    """Synthesis is where one system's reading of another enters."""
    assert not AdmissibilityRules().admits(
        _passage("p1", source_type=SourceType.SECONDARY_SYNTHESIS)
    )


def test_uncomputed_quantities_are_refused() -> None:
    """A source may speak about a construct the code does not produce."""
    rules = AdmissibilityRules()
    passage = _passage("p1", quantity="destiny_gate")

    assert not rules.admits(passage)
    assert "not computed" in rules.rejection_reason(passage)


# ---------------------------------------------------------------------------
# Conflict is derived, not declared
# ---------------------------------------------------------------------------


def test_agreeing_sources_compile_to_consensus() -> None:
    dictionary, report = _compile([_passage("p1"), _passage("p2")])

    assert len(dictionary.entries) == 1
    assert dictionary.entries[0].conflict_verdict is ConflictVerdict.CONSENSUS
    assert dictionary.entries[0].licenses_claim


def test_a_single_source_compiles_to_source_specific() -> None:
    dictionary, _ = _compile([_passage("p1")])

    assert dictionary.entries[0].conflict_verdict is (
        ConflictVerdict.SOURCE_SPECIFIC
    )


def test_disagreeing_sources_compile_to_silence() -> None:
    """Conflict licenses nothing; it is never reconciled informally."""
    dictionary, report = _compile(
        [_passage("p1"), _passage("p2", coordinate="repetition")]
    )

    assert dictionary.entries == ()
    assert report.verdicts[ConflictVerdict.CONFLICTING.value] == 1


def test_opposed_polarity_is_also_a_conflict() -> None:
    """Same coordinate with opposite valence is disagreement."""
    dictionary, _ = _compile(
        [
            _passage("p1", polarity="positive"),
            _passage("p2", polarity="negative"),
        ]
    )

    assert dictionary.entries == ()


def test_compiled_confidence_is_the_weakest_admissible_source() -> None:
    """A chain is no stronger than its weakest admitted citation."""
    dictionary, _ = _compile(
        [_passage("p1", confidence=0.9), _passage("p2", confidence=0.6)]
    )

    assert dictionary.entries[0].confidence == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Determinism and traceability
# ---------------------------------------------------------------------------


def test_compilation_is_deterministic() -> None:
    """Same corpus, same rules, byte-identical dictionary."""
    passages = [_passage("p1"), _passage("p2"), _passage("p3", value=7)]

    first, first_report = _compile(passages)
    second, second_report = _compile(list(reversed(passages)))

    assert first.dictionary_hash() == second.dictionary_hash()
    assert first_report.corpus_hash == second_report.corpus_hash


def test_changing_rules_changes_the_dictionary_deterministically() -> None:
    """A rule change rebuilds without touching a single citation."""
    passages = [_passage("p1", confidence=0.6)]

    permissive, _ = _compile(passages, AdmissibilityRules())
    strict, _ = _compile(
        passages, AdmissibilityRules(version="1.1.0", minimum_confidence=0.7)
    )

    assert len(permissive.entries) == 1
    assert strict.entries == ()
    assert (
        AdmissibilityRules().rules_hash()
        != AdmissibilityRules(
            version="1.1.0", minimum_confidence=0.7
        ).rules_hash()
    )


def test_entries_trace_back_to_a_specific_passage() -> None:
    """Every denotation cites the work, edition and locator behind it."""
    dictionary, _ = _compile([_passage("p1")])
    citation = dictionary.entries[0].citation

    assert citation.source_id == "p1"
    assert "Fixture Work" in citation.passage
    assert "1st" in citation.passage


def test_report_records_axis_coverage() -> None:
    """Sparse coverage is reported as a fact, not hidden."""
    _, report = _compile([_passage("p1"), _passage("p2", value=7)])

    assert report.axis_coverage == {"dynamic": 2}
    assert report.entries_emitted == 2
    assert report.keys_seen == 2
