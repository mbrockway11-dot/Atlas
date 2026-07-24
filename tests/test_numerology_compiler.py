"""Tests for corpus -> admissibility -> dictionary compilation.

The dictionary is derived, never authored. These tests pin the derivation:
a passage must come from a copy-verified manifestation, be doubly transcribed
with agreement, denote directly, and share a construct with the code. Strata
never merge, silence is explicable by reason, and compilation is
deterministic.

Every passage here is a **fixture with an invented citation**, present to
exercise the compiler. None is a real transcription, and no fixture meaning
reaches the shipped package.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.numerology_bibliography import (
    REQUIRED_FOR_TRANSCRIPTION,
    AuthorityScope,
    BibliographyError,
    IdentityStatus,
    Manifestation,
    ProvenanceLevel,
    SourceCopy,
    SourceType,
    Work,
    excerpt_hash,
)
from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    compile_dictionary,
    completeness_report,
)
from atlas.validation.denotation.numerology_corpus import (
    ConstructEquivalence,
    CorpusError,
    SemanticGranularity,
    SilenceReason,
    SourcePassage,
    Transcription,
    build_corpus,
)
from atlas.validation.denotation.numerology_dictionary import ConflictVerdict
from atlas.validation.denotation.numerology_tradition import SourceRole


VERIFIED_LEVELS = frozenset(REQUIRED_FOR_TRANSCRIPTION)


def _work(work_id: str = "fx-work") -> Work:
    """Build a fixture work."""
    return Work(
        work_id=work_id,
        author="Fixture Author",
        title="Fixture Work",
        work_identity=IdentityStatus.VERIFIED,
    )


def _manifestation(
    manifestation_id: str = "fx-manifestation",
    *,
    role: SourceRole = SourceRole.CANONICAL,
    source_type: SourceType = SourceType.MODERN_COMMENTARY,
    levels: frozenset[ProvenanceLevel] = VERIFIED_LEVELS,
    edition_identity: IdentityStatus = IdentityStatus.VERIFIED,
    pagination_identity: IdentityStatus = IdentityStatus.VERIFIED,
) -> Manifestation:
    """Build a fixture manifestation, copy-verified by default."""
    return Manifestation(
        manifestation_id=manifestation_id,
        work_id="fx-work",
        edition_statement="1st",
        publisher="Fixture Press",
        publication_year=1970,
        copyright_year=1965,
        isbn="",
        oclc="",
        pagination="200 pp",
        fmt="paperback",
        role=role,
        source_type=source_type,
        authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
        edition_identity=edition_identity,
        pagination_identity=pagination_identity,
        provenance_levels=levels,
    )


def _copy(
    copy_id: str = "fx-copy", *, manifestation_id: str = "fx-manifestation"
) -> SourceCopy:
    """Build a fixture source copy."""
    return SourceCopy(
        copy_id=copy_id,
        manifestation_id=manifestation_id,
        scan_identifier="fx-scan-1",
        file_hash="deadbeef",
        page_map={"014": "12"},
    )


def _passage(
    passage_id: str,
    *,
    copy_id: str = "fx-copy",
    quantity: str = "life_path",
    value: int = 4,
    coordinate: str = "stabilization",
    granularity: SemanticGranularity = (
        SemanticGranularity.DIRECT_DENOTATION
    ),
    equivalence: ConstructEquivalence = ConstructEquivalence.EXACT,
    confidence: float = 0.8,
    transcriptions: tuple[Transcription, ...] | None = None,
) -> SourcePassage:
    """Build a fixture passage, doubly transcribed by default."""
    return SourcePassage(
        passage_id=passage_id,
        copy_id=copy_id,
        printed_page="12",
        scan_page="014",
        chapter_or_heading="Fixture chapter",
        # `is None` rather than a falsy check: an explicitly empty tuple must
        # reach the constructor so the no-transcription guard can fire.
        transcriptions=(
            (
                Transcription("transcriber-a", "fixture excerpt"),
                Transcription("transcriber-b", "fixture excerpt"),
            )
            if transcriptions is None
            else transcriptions
        ),
        quantity_as_named_by_source="fixture term",
        quantity_as_named_by_code=quantity,
        construct_equivalence=equivalence,
        value=value,
        granularity=granularity,
        proposed_axis="dynamic",
        proposed_coordinate=coordinate,
        polarity="neutral",
        confidence=confidence,
    )


def _corpus(passages, *, manifestations=None, copies=None):
    """Assemble a fixture corpus."""
    return build_corpus(
        "fx-corpus",
        [_work()],
        manifestations or [_manifestation()],
        copies if copies is not None else [_copy()],
        passages,
    )


def _compile(passages, *, manifestations=None, copies=None, rules=None,
             role=SourceRole.CANONICAL):
    """Compile fixture passages under default or supplied rules."""
    return compile_dictionary(
        _corpus(passages, manifestations=manifestations, copies=copies),
        rules or AdmissibilityRules(),
        role=role,
        tradition="fx-tradition",
        version="0.0.1",
    )


# ---------------------------------------------------------------------------
# Layered bibliographic identity
# ---------------------------------------------------------------------------


def test_work_identity_is_separate_from_manifestation_identity() -> None:
    """A work can be verified while its printing is not.

    Balliett's actual state: the 1908 edition demonstrably exists, but which
    manifestation and pagination remain open. Collapsing these into one
    verdict would throw away the part that is settled.
    """
    manifestation = _manifestation(
        edition_identity=IdentityStatus.UNRESOLVED,
        pagination_identity=IdentityStatus.UNRESOLVED,
    )

    assert _work().work_identity is IdentityStatus.VERIFIED
    assert not manifestation.transcription_eligible
    assert "edition identity unresolved" in manifestation.blocking_reasons()


def test_catalog_assertions_do_not_make_a_manifestation_eligible() -> None:
    """Repeating a claim across catalogs is not inspecting a title page."""
    manifestation = _manifestation(
        levels=frozenset(
            {
                ProvenanceLevel.CATALOG_ASSERTED,
                ProvenanceLevel.CROSS_CATALOG_CORRELATED,
            }
        )
    )

    assert not manifestation.copy_verified
    assert not manifestation.transcription_eligible


def test_all_three_copy_checks_are_required() -> None:
    """Title page, copyright page and pagination, not a subset."""
    for level in REQUIRED_FOR_TRANSCRIPTION:
        assert not _manifestation(
            levels=VERIFIED_LEVELS - {level}
        ).copy_verified


def test_a_copy_needs_a_file_hash() -> None:
    """Without it a later transcription cannot be tied to the same text."""
    with pytest.raises(BibliographyError, match="file hash"):
        SourceCopy(
            copy_id="c",
            manifestation_id="m",
            scan_identifier="s",
            file_hash="",
        )


def test_scan_page_maps_to_printed_page() -> None:
    """A locator that conflates the two cannot be checked by another scan."""
    assert _copy().printed_page_for("014") == "12"
    assert _copy().printed_page_for("999") is None


# ---------------------------------------------------------------------------
# A passage must come from a copy someone held
# ---------------------------------------------------------------------------


def test_a_passage_cannot_cite_a_merely_declared_manifestation() -> None:
    """Without a copy in hand there is nothing to have transcribed."""
    with pytest.raises(CorpusError, match="merely declared"):
        _corpus([_passage("p1")], copies=[])


def test_a_passage_needs_at_least_one_transcription() -> None:
    """A citation nobody transcribed is a claim about a book, not evidence."""
    with pytest.raises(CorpusError, match="at least one transcription"):
        _passage("p1", transcriptions=())


def test_unverified_manifestation_blocks_compilation() -> None:
    """Copy verification gates admission, not just documentation."""
    _, report = _compile(
        [_passage("p1")],
        manifestations=[
            _manifestation(
                levels=frozenset({ProvenanceLevel.CATALOG_ASSERTED})
            )
        ],
    )

    assert report.entries_emitted == 0
    assert "not transcription-eligible" in report.rejections["life_path=4"][0]


# ---------------------------------------------------------------------------
# Double transcription
# ---------------------------------------------------------------------------


def test_transcription_hash_ignores_whitespace_only_differences() -> None:
    """Line-break disagreements are not word disagreements."""
    assert excerpt_hash("four  means\nstability") == excerpt_hash(
        "four means stability"
    )
    assert excerpt_hash("four means stability") != excerpt_hash(
        "four means stillness"
    )


def test_disagreeing_transcriptions_block_compilation() -> None:
    """Resolve against the page image rather than choosing one."""
    passage = _passage(
        "p1",
        transcriptions=(
            Transcription("transcriber-a", "fixture excerpt"),
            Transcription("transcriber-b", "different excerpt"),
        ),
    )

    assert not passage.transcriptions_agree

    _, report = _compile([passage])

    assert report.entries_emitted == 0
    assert "disagree" in report.rejections["life_path=4"][0]


def test_reading_a_disagreed_excerpt_raises() -> None:
    """The disagreement cannot be papered over by reading the first one."""
    passage = _passage(
        "p1",
        transcriptions=(Transcription("a", "one"), Transcription("b", "two")),
    )

    with pytest.raises(CorpusError, match="disagree"):
        _ = passage.verbatim_excerpt


def test_single_transcription_is_refused_by_default() -> None:
    """Double transcription makes a misreading visible."""
    passage = _passage(
        "p1", transcriptions=(Transcription("solo", "fixture excerpt"),)
    )

    assert not passage.doubly_transcribed

    _, report = _compile([passage])

    assert report.entries_emitted == 0

    relaxed, _ = _compile(
        [passage],
        rules=AdmissibilityRules(
            version="1.1.0", require_double_transcription=False
        ),
    )

    assert len(relaxed.entries) == 1


# ---------------------------------------------------------------------------
# Construct equivalence and granularity
# ---------------------------------------------------------------------------


def test_terminology_resemblance_cannot_license_a_mapping() -> None:
    """Both saying "life path" is not evidence they mean the same thing."""
    rules = AdmissibilityRules()

    assert rules.admits(_passage("p1"), _manifestation())

    for equivalence in (
        ConstructEquivalence.TERMINOLOGY_ONLY,
        ConstructEquivalence.PARTIALLY_EQUIVALENT,
        ConstructEquivalence.NOT_EQUIVALENT,
        ConstructEquivalence.UNRESOLVED,
    ):
        assert not rules.admits(
            _passage("p2", equivalence=equivalence), _manifestation()
        )


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
            _passage("p1", granularity=granularity), _manifestation()
        )


def test_secondary_synthesis_is_excluded() -> None:
    """Synthesis is where one system's reading of another enters."""
    _, report = _compile(
        [_passage("p1")],
        manifestations=[
            _manifestation(source_type=SourceType.SECONDARY_SYNTHESIS)
        ],
    )

    assert report.entries_emitted == 0


# ---------------------------------------------------------------------------
# Strata never merge
# ---------------------------------------------------------------------------


def _two_strata():
    """Return manifestations and copies for both strata."""
    manifestations = [
        _manifestation("fx-canonical", role=SourceRole.CANONICAL),
        _manifestation("fx-precursor", role=SourceRole.HISTORICAL_PRECURSOR),
    ]
    copies = [
        _copy("copy-canonical", manifestation_id="fx-canonical"),
        _copy("copy-precursor", manifestation_id="fx-precursor"),
    ]

    return manifestations, copies


def test_a_precursor_cannot_join_a_canonical_consensus() -> None:
    """A canonical single passage stays source_specific."""
    manifestations, copies = _two_strata()
    passages = [
        _passage("p1", copy_id="copy-canonical"),
        _passage("p2", copy_id="copy-precursor"),
    ]

    dictionary, report = _compile(
        passages, manifestations=manifestations, copies=copies
    )

    assert report.passages_available == 1
    assert dictionary.entries[0].conflict_verdict is (
        ConflictVerdict.SOURCE_SPECIFIC
    )


def test_the_precursor_stratum_compiles_separately() -> None:
    """Comparison is a later explicit step, not an assumption."""
    manifestations, copies = _two_strata()
    passages = [_passage("p2", copy_id="copy-precursor")]

    _, canonical = _compile(
        passages, manifestations=manifestations, copies=copies
    )
    _, precursor = _compile(
        passages,
        manifestations=manifestations,
        copies=copies,
        role=SourceRole.HISTORICAL_PRECURSOR,
    )

    assert canonical.entries_emitted == 0
    assert precursor.entries_emitted == 1


# ---------------------------------------------------------------------------
# Conflict, determinism, traceability
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


def test_compilation_is_deterministic() -> None:
    """Same corpus, same rules, byte-identical dictionary."""
    passages = [_passage("p1"), _passage("p2"), _passage("p3", value=7)]

    first, first_report = _compile(passages)
    second, second_report = _compile(list(reversed(passages)))

    assert first.dictionary_hash() == second.dictionary_hash()
    assert first_report.corpus_hash == second_report.corpus_hash


def test_entries_trace_back_to_manifestation_and_printed_page() -> None:
    """Every denotation cites the printing and the printed page."""
    dictionary, _ = _compile([_passage("p1")])
    citation = dictionary.entries[0].citation

    assert citation.source_id == "p1"
    assert "Fixture Press" in citation.passage
    assert "printed p. 12" in citation.passage


# ---------------------------------------------------------------------------
# Completeness: silence has reasons
# ---------------------------------------------------------------------------


def test_completeness_distinguishes_no_copy_from_no_denotation() -> None:
    """A bare empty dictionary conflates states that are not alike."""
    corpus = build_corpus(
        "fx",
        [_work()],
        [_manifestation(levels=frozenset({ProvenanceLevel.CATALOG_ASSERTED}))],
        [],
        [],
    )

    report = completeness_report(corpus, AdmissibilityRules())

    assert SilenceReason.NO_SOURCE_COPY.value in report["silence_reasons"]
    assert report["manifestations_transcription_eligible"] == 0


def test_completeness_reports_construct_mismatch() -> None:
    """We have the book, but it is not talking about our quantity."""
    report = completeness_report(
        _corpus(
            [_passage("p1", equivalence=ConstructEquivalence.TERMINOLOGY_ONLY)]
        ),
        AdmissibilityRules(),
    )

    assert (
        SilenceReason.NO_MATCHING_CONSTRUCT.value in report["silence_reasons"]
    )


def test_completeness_reports_absent_direct_denotation() -> None:
    """The source discusses the value but never denotes it."""
    report = completeness_report(
        _corpus([_passage("p1", granularity=SemanticGranularity.PREDICTION)]),
        AdmissibilityRules(),
    )

    assert (
        SilenceReason.NO_DIRECT_DENOTATION.value in report["silence_reasons"]
    )


def test_completeness_reports_conflicting_denotations() -> None:
    """Admissible sources that disagree are their own silence reason."""
    report = completeness_report(
        _corpus([_passage("p1"), _passage("p2", coordinate="repetition")]),
        AdmissibilityRules(),
    )

    assert (
        SilenceReason.CONFLICTING_DENOTATIONS.value
        in report["silence_reasons"]
    )


# ---------------------------------------------------------------------------
# The declared corpus v1
# ---------------------------------------------------------------------------


def test_declared_corpus_has_no_copies_and_no_passages() -> None:
    """The honest state: bibliography exists, textual evidence does not."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        declared_corpus,
    )

    corpus = declared_corpus()

    assert len(corpus.works) == 2
    assert len(corpus.manifestations) == 2
    assert corpus.copies == ()
    assert corpus.passages == ()


def test_declared_corpus_compiles_to_an_empty_dictionary() -> None:
    """No verified copy, therefore no meanings. Not a failure."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        declared_corpus,
    )

    dictionary, report = compile_dictionary(
        declared_corpus(), AdmissibilityRules()
    )

    assert dictionary.entries == ()
    assert report.entries_emitted == 0


def test_balliett_work_is_verified_but_manifestation_is_not() -> None:
    """The sharpened distinction: existence settled, printing open."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        BALLIETT_MANIFESTATION,
        BALLIETT_WORK,
    )

    assert BALLIETT_WORK.work_identity is IdentityStatus.VERIFIED
    assert BALLIETT_MANIFESTATION.edition_identity is (
        IdentityStatus.UNRESOLVED
    )
    assert not BALLIETT_MANIFESTATION.transcription_eligible


def test_jordan_manifestation_records_the_catalog_conflict() -> None:
    """Not resolved by preferring a catalog; resolved from the copy."""
    from atlas.validation.denotation.numerology_corpus_v1 import (
        JORDAN_MANIFESTATION,
    )

    assert JORDAN_MANIFESTATION.edition_identity is IdentityStatus.DISCREPANT
    assert JORDAN_MANIFESTATION.isbn == "0875162274"
    assert "title and copyright pages" in JORDAN_MANIFESTATION.identity_note
    assert not JORDAN_MANIFESTATION.transcription_eligible


def test_the_tradition_makes_no_historical_claim() -> None:
    """"Pythagorean" here is a modern lineage, not a claim about antiquity."""
    from atlas.validation.denotation.numerology_tradition import (
        MODERN_AMERICAN_PYTHAGOREAN,
    )

    assert MODERN_AMERICAN_PYTHAGOREAN.historical_claim == "none"
    assert (
        "Chaldean numerology"
        in MODERN_AMERICAN_PYTHAGOREAN.not_equivalent_to
    )


def test_reduction_policy_name_asserts_no_endorsement() -> None:
    """Preserving 11/22/33 is arithmetic, not a source claim."""
    from atlas.validation.denotation.numerology_expression import (
        REDUCTION_POLICY,
    )

    assert REDUCTION_POLICY == "alphabetic-1to9-preserve-11-22-33-v1"
    assert "pythagorean" not in REDUCTION_POLICY
