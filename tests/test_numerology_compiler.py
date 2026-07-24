"""Tests for corpus -> admissibility -> dictionary compilation.

The dictionary is derived, never authored, so these tests pin the derivation:
only direct denotations from genuinely shared constructs are eligible,
disagreement compiles to silence rather than a reconciled meaning, strata
never merge, and the same corpus under the same rules always produces the same
dictionary.

Every passage here is a **fixture with an invented citation**, present to
exercise the compiler. None is a real transcription, and no fixture meaning
reaches the shipped package.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    compile_dictionary,
)
from atlas.validation.denotation.numerology_corpus import (
    AuthorityScope,
    ConstructEquivalence,
    CorpusError,
    SemanticGranularity,
    SourceEdition,
    SourcePassage,
    SourceType,
    build_corpus,
)
from atlas.validation.denotation.numerology_dictionary import ConflictVerdict
from atlas.validation.denotation.numerology_tradition import (
    SourceRole,
    VerificationStatus,
)


def _edition(
    edition_id: str = "fx-canonical",
    *,
    role: SourceRole = SourceRole.CANONICAL,
    source_type: SourceType = SourceType.MODERN_COMMENTARY,
    scope: AuthorityScope = AuthorityScope.AUTHOR_SPECIFIC,
) -> SourceEdition:
    """Build a fixture edition. Not a real bibliography."""
    return SourceEdition(
        edition_id=edition_id,
        author="Fixture Author",
        title="Fixture Work",
        edition="1st",
        publisher="Fixture Press",
        publication_year=1970,
        copyright_year=1965,
        role=role,
        source_type=source_type,
        authority_scope=scope,
        verification_status=VerificationStatus.DECLARED_UNVERIFIED,
    )


def _passage(
    passage_id: str,
    *,
    edition_id: str = "fx-canonical",
    quantity: str = "life_path",
    value: int = 4,
    axis: str = "dynamic",
    coordinate: str = "stabilization",
    polarity: str = "neutral",
    granularity: SemanticGranularity = (
        SemanticGranularity.DIRECT_DENOTATION
    ),
    equivalence: ConstructEquivalence = ConstructEquivalence.EXACT,
    confidence: float = 0.8,
) -> SourcePassage:
    """Build a fixture passage. Not a real transcription."""
    return SourcePassage(
        passage_id=passage_id,
        edition_id=edition_id,
        page="12",
        chapter_or_heading="Fixture chapter",
        verbatim_excerpt="fixture excerpt for compiler tests",
        quantity_as_named_by_source="fixture term",
        quantity_as_named_by_code=quantity,
        construct_equivalence=equivalence,
        value=value,
        granularity=granularity,
        proposed_axis=axis,
        proposed_coordinate=coordinate,
        polarity=polarity,
        confidence=confidence,
        transcriber="fixture",
    )


def _compile(passages, editions=None, rules=None, role=SourceRole.CANONICAL):
    """Compile fixture passages under default or supplied rules."""
    return compile_dictionary(
        build_corpus("fx-corpus", editions or [_edition()], passages),
        rules or AdmissibilityRules(),
        role=role,
        tradition="fx-tradition",
        version="0.0.1",
    )


# ---------------------------------------------------------------------------
# The corpus is bibliographic evidence
# ---------------------------------------------------------------------------


def test_an_edition_needs_locatable_bibliography() -> None:
    """A citation that cannot be located is not evidence."""
    with pytest.raises(CorpusError, match="missing bibliography"):
        SourceEdition(
            edition_id="fx",
            author="",
            title="Fixture Work",
            edition="1st",
            publisher="Fixture Press",
            publication_year=1970,
            copyright_year=None,
            role=SourceRole.CANONICAL,
            source_type=SourceType.PRIMARY,
            authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
            verification_status=VerificationStatus.DECLARED_UNVERIFIED,
        )


def test_a_passage_needs_a_transcriber_and_locator() -> None:
    """An untranscribed or unlocated passage is not evidence."""
    with pytest.raises(CorpusError, match="missing provenance"):
        SourcePassage(
            passage_id="p1",
            edition_id="fx-canonical",
            page="",
            chapter_or_heading="c",
            verbatim_excerpt="e",
            quantity_as_named_by_source="s",
            quantity_as_named_by_code="life_path",
            construct_equivalence=ConstructEquivalence.EXACT,
            value=4,
            granularity=SemanticGranularity.DIRECT_DENOTATION,
            proposed_axis="dynamic",
            proposed_coordinate="stabilization",
            polarity="neutral",
            confidence=0.8,
            transcriber="",
        )


def test_a_passage_must_cite_a_known_edition() -> None:
    """Evidence must resolve to a specific printing."""
    with pytest.raises(CorpusError, match="unknown edition"):
        build_corpus(
            "fx", [_edition()], [_passage("p1", edition_id="nonexistent")]
        )


def test_corpus_ordering_is_deterministic() -> None:
    """Insertion order must not affect the corpus hash."""
    forward = build_corpus(
        "fx", [_edition()], [_passage("p1"), _passage("p2", value=5)]
    )
    reverse = build_corpus(
        "fx", [_edition()], [_passage("p2", value=5), _passage("p1")]
    )

    assert forward.corpus_hash() == reverse.corpus_hash()


# ---------------------------------------------------------------------------
# Construct equivalence -- a shared phrase is not evidence
# ---------------------------------------------------------------------------


def test_terminology_resemblance_cannot_license_a_mapping() -> None:
    """Both saying "life path" is not evidence they mean the same thing."""
    rules = AdmissibilityRules()

    assert rules.admits(
        _passage("p1", equivalence=ConstructEquivalence.EXACT), _edition()
    )
    assert rules.admits(
        _passage(
            "p2", equivalence=ConstructEquivalence.COMPUTATIONALLY_EQUIVALENT
        ),
        _edition(),
    )

    for equivalence in (
        ConstructEquivalence.TERMINOLOGY_ONLY,
        ConstructEquivalence.PARTIALLY_EQUIVALENT,
        ConstructEquivalence.NOT_EQUIVALENT,
        ConstructEquivalence.UNRESOLVED,
    ):
        assert not rules.admits(
            _passage("p3", equivalence=equivalence), _edition()
        )


def test_construct_mismatch_yields_silence_with_a_reason() -> None:
    """A mismatch is a mismatch, never a reinterpretation."""
    _, report = _compile(
        [_passage("p1", equivalence=ConstructEquivalence.TERMINOLOGY_ONLY)]
    )

    assert report.entries_emitted == 0
    assert "construct equivalence" in report.rejections["life_path=4"][0]


# ---------------------------------------------------------------------------
# Semantic granularity
# ---------------------------------------------------------------------------


def test_only_direct_denotations_are_eligible() -> None:
    """A behavioral claim wearing a denotation's clothes is refused."""
    rules = AdmissibilityRules()

    for granularity in (
        SemanticGranularity.PREDICTION,
        SemanticGranularity.RECOMMENDATION,
        SemanticGranularity.ANALOGY,
        SemanticGranularity.CORRESPONDENCE,
        SemanticGranularity.COMMENTARY,
    ):
        assert not rules.admits(
            _passage("p1", granularity=granularity), _edition()
        )


def test_secondary_synthesis_is_excluded() -> None:
    """Synthesis is where one system's reading of another enters."""
    editions = [_edition(source_type=SourceType.SECONDARY_SYNTHESIS)]
    _, report = _compile([_passage("p1")], editions=editions)

    assert report.entries_emitted == 0


def test_uncomputed_quantities_are_refused() -> None:
    """A source may speak about a construct the code does not produce."""
    rules = AdmissibilityRules()
    passage = _passage("p1", quantity="destiny_gate")

    assert not rules.admits(passage, _edition())
    assert "not computed" in rules.rejection_reason(passage, _edition())


# ---------------------------------------------------------------------------
# Strata never merge
# ---------------------------------------------------------------------------


def test_a_precursor_cannot_join_a_canonical_consensus() -> None:
    """Shared marketing is not evidence that two authors agree.

    A canonical single passage stays source_specific even when a historical
    precursor asserts the same thing -- requiring precursor agreement would
    conflate historical comparison with evidence sufficiency.
    """
    editions = [
        _edition("fx-canonical", role=SourceRole.CANONICAL),
        _edition("fx-precursor", role=SourceRole.HISTORICAL_PRECURSOR),
    ]
    passages = [
        _passage("p1", edition_id="fx-canonical"),
        _passage("p2", edition_id="fx-precursor"),
    ]

    dictionary, report = _compile(passages, editions=editions)

    assert report.passages_available == 1
    assert dictionary.entries[0].conflict_verdict is (
        ConflictVerdict.SOURCE_SPECIFIC
    )


def test_a_precursor_cannot_contradict_the_canonical_stratum() -> None:
    """A disagreeing precursor cannot silence a canonical entry either."""
    editions = [
        _edition("fx-canonical", role=SourceRole.CANONICAL),
        _edition("fx-precursor", role=SourceRole.HISTORICAL_PRECURSOR),
    ]
    passages = [
        _passage("p1", edition_id="fx-canonical"),
        _passage("p2", edition_id="fx-precursor", coordinate="repetition"),
    ]

    dictionary, _ = _compile(passages, editions=editions)

    assert len(dictionary.entries) == 1
    assert dictionary.entries[0].coordinate == "stabilization"


def test_the_precursor_stratum_compiles_separately() -> None:
    """Comparison is a later explicit step, not an assumption."""
    editions = [
        _edition("fx-canonical", role=SourceRole.CANONICAL),
        _edition("fx-precursor", role=SourceRole.HISTORICAL_PRECURSOR),
    ]
    passages = [_passage("p2", edition_id="fx-precursor")]

    _, canonical = _compile(passages, editions=editions)
    _, precursor = _compile(
        passages, editions=editions, role=SourceRole.HISTORICAL_PRECURSOR
    )

    assert canonical.entries_emitted == 0
    assert precursor.entries_emitted == 1


# ---------------------------------------------------------------------------
# Conflict is derived, not declared
# ---------------------------------------------------------------------------


def test_agreeing_sources_compile_to_consensus() -> None:
    dictionary, _ = _compile([_passage("p1"), _passage("p2")])

    assert dictionary.entries[0].conflict_verdict is ConflictVerdict.CONSENSUS


def test_disagreeing_sources_compile_to_silence() -> None:
    """Conflict licenses nothing; it is never reconciled informally."""
    dictionary, report = _compile(
        [_passage("p1"), _passage("p2", coordinate="repetition")]
    )

    assert dictionary.entries == ()
    assert report.verdicts[ConflictVerdict.CONFLICTING.value] == 1


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


def test_changing_rules_rebuilds_without_touching_citations() -> None:
    """A rule change is a reproducible operation on unchanged evidence."""
    passages = [_passage("p1", confidence=0.6)]

    permissive, _ = _compile(passages)
    strict, _ = _compile(
        passages,
        rules=AdmissibilityRules(version="1.1.0", minimum_confidence=0.7),
    )

    assert len(permissive.entries) == 1
    assert strict.entries == ()


def test_entries_trace_back_to_edition_and_page() -> None:
    """Every denotation cites the printing and page behind it."""
    dictionary, _ = _compile([_passage("p1")])
    citation = dictionary.entries[0].citation

    assert citation.source_id == "p1"
    assert "Fixture Work" in citation.passage
    assert "Fixture Press" in citation.passage
    assert "p. 12" in citation.passage


# ---------------------------------------------------------------------------
# The declared corpus v1
# ---------------------------------------------------------------------------


def test_declared_corpus_has_editions_but_no_passages() -> None:
    """The honest state: sources are scoped, nothing is transcribed yet.

    Transcription needs a paginated copy of each edition, and none has been
    ingested. Inventing excerpts and page numbers would put fabricated
    bibliography into the one artifact whose purpose is traceable provenance.
    """
    from atlas.validation.denotation.numerology_corpus_v1 import (
        declared_corpus,
    )

    corpus = declared_corpus()

    assert len(corpus.editions) == 2
    assert corpus.passages == ()


def test_declared_corpus_compiles_to_an_empty_dictionary() -> None:
    """No admissible evidence, therefore no meanings. Not a failure."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        declared_corpus,
    )

    dictionary, report = compile_dictionary(
        declared_corpus(), AdmissibilityRules()
    )

    assert dictionary.entries == ()
    assert report.entries_emitted == 0
    assert report.passages_available == 0


def test_the_two_editions_sit_in_different_strata() -> None:
    """Jordan is canonical; Balliett is a historical precursor, not
    corroboration."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        BALLIETT_1908,
        JORDAN_1978,
    )

    assert JORDAN_1978.role is SourceRole.CANONICAL
    assert BALLIETT_1908.role is SourceRole.HISTORICAL_PRECURSOR
    assert BALLIETT_1908.authority_scope is AuthorityScope.AUTHOR_SPECIFIC


def test_edition_bibliography_discrepancies_are_recorded() -> None:
    """A provenance artifact must distinguish checked from asserted.

    Neither edition was confirmed cleanly against Open Library, so both
    carry the discrepancy rather than presenting unverified metadata as
    settled.
    """
    from atlas.validation.denotation.numerology_corpus_v1 import (
        BALLIETT_1908,
        JORDAN_1978,
    )

    for edition in (JORDAN_1978, BALLIETT_1908):
        assert edition.verification_status is VerificationStatus.DISCREPANT
        assert edition.verification_note


def test_the_tradition_makes_no_historical_claim() -> None:
    """"Pythagorean" here is a modern lineage, not a claim about antiquity."""
    from atlas.validation.denotation.numerology_tradition import (
        MODERN_AMERICAN_PYTHAGOREAN,
    )

    assert MODERN_AMERICAN_PYTHAGOREAN.historical_claim == "none"
    assert (
        "ancient Pythagorean mathematics"
        in MODERN_AMERICAN_PYTHAGOREAN.not_equivalent_to
    )
    assert (
        "Chaldean numerology"
        in MODERN_AMERICAN_PYTHAGOREAN.not_equivalent_to
    )


def test_reduction_policy_name_asserts_no_endorsement() -> None:
    """Preserving 11/22/33 is arithmetic, not a claim any source licenses
    meanings for them."""
    from atlas.validation.denotation.numerology_expression import (
        REDUCTION_POLICY,
    )

    assert REDUCTION_POLICY == "alphabetic-1to9-preserve-11-22-33-v1"
    assert "pythagorean" not in REDUCTION_POLICY
