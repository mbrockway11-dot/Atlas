"""The Vedic graha denotation scaffold: built, fail-closed, unsourced.

Mirrors the numerology denotation tests. The scaffold exists and its machinery
compiles a fixture, but the declared corpus holds no copy and no passage, so it
compiles to silence -- the correct state until 1E-V-SOURCE-B verifies a copy of
Brihat Parasara Hora Shastra and transcribes the nine karakatvas from it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.validation.denotation.numerology_bibliography import (
    AuthorityScope,
    IdentityStatus,
    Manifestation,
    ProvenanceLevel,
    REQUIRED_FOR_TRANSCRIPTION,
    SourceCopy,
    SourceType,
    Work,
)
from atlas.validation.denotation.numerology_corpus import Transcription
from atlas.validation.denotation.numerology_tradition import SourceRole
from atlas.validation.denotation.vedic_denotation import (
    GrahaPassage,
    GrahaSemanticGranularity,
    VedicCorpusError,
    VedicGrahaCorpus,
    compile_graha_dictionary,
    declared_corpus,
    derive_vedic_capabilities,
)
from atlas.validation.denotation.vedic_grahas import (
    GRAHAS,
    SIGN_RULERS,
    lagna_lord_expression,
)


# ---------------------------------------------------------------------------
# The expression layer: computes a graha, blind to the ontology
# ---------------------------------------------------------------------------


def test_lagna_lord_maps_the_sidereal_sign_to_its_ruler() -> None:
    """The subject-varying quantity: ascendant sign -> ruling graha."""
    # ~215 deg sidereal -> Scorpio (sign 8) -> Mars.
    expression = lagna_lord_expression(215.0)

    assert expression.ascendant_sign == 8
    assert expression.graha == "mars"
    assert expression.ayanamsa_scheme == "lahiri"
    assert SIGN_RULERS[expression.ascendant_sign] == "mars"


def test_every_sign_ruler_is_a_graha() -> None:
    """Rulership only ever names one of the nine grahas."""
    assert set(SIGN_RULERS) == set(range(1, 13))
    assert all(ruler in GRAHAS for ruler in SIGN_RULERS.values())


def test_vedic_expression_layer_is_blind_to_the_ontology() -> None:
    """Computation cannot see the vocabulary it will be scored against.

    The same independence guard numerology's expression layer carries: if the
    graha layer could import the ontology it could shape its output to the
    terms it feeds.
    """
    import ast

    source = Path(
        "src/atlas/validation/denotation/vedic_grahas.py"
    ).read_text(encoding="utf-8")

    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

    forbidden = [
        module
        for module in imported
        if "denotation.ontology" in module
        or "denotation.concordance" in module
    ]

    assert not forbidden, f"graha layer must not import {forbidden}"


# ---------------------------------------------------------------------------
# The declared corpus compiles to silence
# ---------------------------------------------------------------------------


def test_declared_bphs_corpus_compiles_to_an_empty_dictionary() -> None:
    """BPHS is declared, but no copy is verified, so nothing is licensed."""
    corpus = declared_corpus()

    assert corpus.to_dict()["counts"] == {
        "works": 1,
        "manifestations": 1,
        "copies": 0,
        "passages": 0,
    }

    dictionary = compile_graha_dictionary(corpus)

    assert dictionary.entries == ()


def test_declared_scaffold_is_not_concordance_eligible() -> None:
    """The scaffold exists and stays silent: no copy, no denotation."""
    corpus = declared_corpus()
    dictionary = compile_graha_dictionary(corpus)
    capabilities = derive_vedic_capabilities(corpus, dictionary)

    assert capabilities.concordance_eligible is False
    assert "no transcription-eligible manifestation with a source copy" in (
        capabilities.blocking
    )


# ---------------------------------------------------------------------------
# The machinery works when a fixture is admitted
# ---------------------------------------------------------------------------


def _eligible_fixture_corpus(
    passages: tuple[GrahaPassage, ...]
) -> VedicGrahaCorpus:
    """A corpus whose manifestation is transcription-eligible, for plumbing."""
    work = Work(
        work_id="fx-work",
        author="fixture",
        title="fixture",
        work_identity=IdentityStatus.VERIFIED,
    )
    manifestation = Manifestation(
        manifestation_id="fx-manifestation",
        work_id="fx-work",
        edition_statement="fixture",
        publisher="fixture",
        publication_year=2000,
        copyright_year=2000,
        isbn="",
        oclc="",
        pagination="1",
        fmt="paperback",
        role=SourceRole.CANONICAL,
        source_type=SourceType.PRIMARY,
        authority_scope=AuthorityScope.TRADITION_WIDE,
        edition_identity=IdentityStatus.VERIFIED,
        pagination_identity=IdentityStatus.VERIFIED,
        provenance_levels=REQUIRED_FOR_TRANSCRIPTION,
    )
    copy = SourceCopy(
        copy_id="fx-copy",
        manifestation_id="fx-manifestation",
        scan_identifier="fx-scan",
        file_hash="f" * 40,
    )

    return VedicGrahaCorpus(
        corpus_id="fx",
        works=(work,),
        manifestations=(manifestation,),
        copies=(copy,),
        passages=passages,
    )


def _karakatva(graha: str, coordinate: str, text: str) -> GrahaPassage:
    return GrahaPassage(
        passage_id=f"fx-{graha}",
        graha=graha,
        copy_id="fx-copy",
        printed_page="1",
        scan_page="n1",
        chapter_or_heading="fixture",
        transcriptions=(Transcription("a", text), Transcription("b", text)),
        granularity=GrahaSemanticGranularity.KARAKATVA,
        proposed_axis="domain",
        proposed_coordinate=coordinate,
        polarity="positive",
        confidence=0.7,
    )


def test_the_machinery_compiles_when_a_fixture_is_admitted() -> None:
    """Proves the pipeline is correct, not that any mapping is authoritative."""
    corpus = _eligible_fixture_corpus(
        (_karakatva("sun", "spirituality", "the sun signifies the soul"),)
    )

    dictionary = compile_graha_dictionary(corpus)

    assert len(dictionary.entries) == 1
    entry = dictionary.lookup("sun")
    assert entry is not None
    assert entry.axis == "domain"
    assert entry.coordinate == "spirituality"
    assert entry.mapping_kind == "interpretive"

    capabilities = derive_vedic_capabilities(corpus, dictionary)
    assert capabilities.concordance_eligible is True


def test_a_single_transcription_is_not_admitted() -> None:
    """Double transcription is required; one transcriber compiles to silence."""
    passage = GrahaPassage(
        passage_id="fx-sun",
        graha="sun",
        copy_id="fx-copy",
        printed_page="1",
        scan_page="n1",
        chapter_or_heading="fixture",
        transcriptions=(Transcription("solo", "the sun signifies the soul"),),
        granularity=GrahaSemanticGranularity.KARAKATVA,
        proposed_axis="domain",
        proposed_coordinate="spirituality",
        polarity="positive",
        confidence=0.7,
    )
    corpus = _eligible_fixture_corpus((passage,))

    assert compile_graha_dictionary(corpus).entries == ()


def test_conflicting_karakatvas_compile_to_silence() -> None:
    """Two admissible passages that disagree license nothing."""
    corpus = _eligible_fixture_corpus(
        (
            _karakatva("sun", "spirituality", "reading one"),
            GrahaPassage(
                passage_id="fx-sun-2",
                graha="sun",
                copy_id="fx-copy",
                printed_page="2",
                scan_page="n2",
                chapter_or_heading="fixture",
                transcriptions=(
                    Transcription("a", "reading two"),
                    Transcription("b", "reading two"),
                ),
                granularity=GrahaSemanticGranularity.KARAKATVA,
                proposed_axis="domain",
                proposed_coordinate="agency",
                polarity="positive",
                confidence=0.7,
            ),
        )
    )

    assert compile_graha_dictionary(corpus).entries == ()


def test_a_passage_cannot_name_a_graha_outside_the_frozen_set() -> None:
    """A denotation may not address a construct the code does not produce."""
    with pytest.raises(VedicCorpusError, match="not a graha"):
        _karakatva("nibiru", "spirituality", "not a graha")


def test_a_passage_cannot_cite_a_merely_declared_manifestation() -> None:
    """A passage from a copy nobody registered is not evidence."""
    with pytest.raises(VedicCorpusError, match="unknown copy"):
        VedicGrahaCorpus(
            corpus_id="fx",
            works=(
                Work(
                    work_id="w",
                    author="a",
                    title="t",
                    work_identity=IdentityStatus.VERIFIED,
                ),
            ),
            manifestations=(),
            copies=(),
            passages=(_karakatva("sun", "spirituality", "orphan"),),
        )
