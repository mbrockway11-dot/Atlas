"""Tests for numerology capability gating and legacy quarantine.

Two safeguards close the 1E-N-SOURCE substage.

**Capabilities** must be derived from the corpus, so a downstream caller
cannot gate on a non-empty dictionary -- a check that fails open for fixture
meanings, stale artifacts and partially ingested sources alike.

**Quarantine** keeps the legacy unprovenanced adapter out of every 1E path.
Without it the new provenance architecture and the old interpretation
shortcut coexist, and a later caller may unknowingly take the shortcut.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from atlas.validation.denotation.numerology_bibliography import (
    REQUIRED_FOR_TRANSCRIPTION,
    AuthorityScope,
    IdentityStatus,
    Manifestation,
    ProvenanceLevel,
    SourceCopy,
    SourceType,
    Work,
)
from atlas.validation.denotation.numerology_capabilities import (
    LEGACY_UNPROVENANCED_INTERPRETATION,
    derive_capabilities,
)
from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    compile_dictionary,
)
from atlas.validation.denotation.numerology_corpus import (
    ConstructEquivalence,
    SemanticGranularity,
    SourcePassage,
    Transcription,
    build_corpus,
)
from atlas.validation.denotation.numerology_corpus_v1 import declared_corpus
from atlas.validation.denotation.numerology_tradition import SourceRole


DENOTATION_PACKAGE = Path("src/atlas/validation/denotation")


def _eligible_corpus(passages=None):
    """Return a corpus whose manifestation is fully copy-verified."""
    work = Work(
        work_id="fx-work",
        author="Fixture Author",
        title="Fixture Work",
        work_identity=IdentityStatus.VERIFIED,
    )
    manifestation = Manifestation(
        manifestation_id="fx-m",
        work_id="fx-work",
        edition_statement="1st",
        publisher="Fixture Press",
        publication_year=1970,
        copyright_year=1965,
        isbn="",
        oclc="",
        pagination="200 pp",
        fmt="paperback",
        role=SourceRole.CANONICAL,
        source_type=SourceType.MODERN_COMMENTARY,
        authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
        edition_identity=IdentityStatus.VERIFIED,
        pagination_identity=IdentityStatus.VERIFIED,
        provenance_levels=frozenset(REQUIRED_FOR_TRANSCRIPTION),
    )
    copy = SourceCopy(
        copy_id="fx-c",
        manifestation_id="fx-m",
        scan_identifier="scan",
        file_hash="cafebabe",
        page_map={"014": "12"},
    )

    return build_corpus(
        "fx", [work], [manifestation], [copy], passages or []
    )


def _passage(passage_id: str = "p1") -> SourcePassage:
    """Return an admissible fixture passage."""
    return SourcePassage(
        passage_id=passage_id,
        copy_id="fx-c",
        printed_page="12",
        scan_page="014",
        chapter_or_heading="ch",
        transcriptions=(
            Transcription("a", "fixture excerpt"),
            Transcription("b", "fixture excerpt"),
        ),
        quantity_as_named_by_source="fixture term",
        quantity_as_named_by_code="life_path",
        construct_equivalence=ConstructEquivalence.EXACT,
        value=4,
        granularity=SemanticGranularity.DIRECT_DENOTATION,
        proposed_axis="dynamic",
        proposed_coordinate="stabilization",
        polarity="neutral",
        confidence=0.8,
    )


def _capabilities(corpus, rules=None):
    """Compile a corpus and derive its capabilities."""
    rules = rules or AdmissibilityRules()
    dictionary, report = compile_dictionary(corpus, rules)

    return derive_capabilities(corpus, rules, dictionary, report)


# ---------------------------------------------------------------------------
# Capabilities are derived, and fail closed
# ---------------------------------------------------------------------------


def test_declared_corpus_is_not_concordance_eligible() -> None:
    """The current, correct state: bibliography without textual evidence."""
    capabilities = _capabilities(declared_corpus())

    assert capabilities.source_copy_verified is False
    assert capabilities.construct_equivalence_established is False
    assert capabilities.direct_denotations_available is False
    assert capabilities.concordance_eligible is False
    assert capabilities.blocking


def test_every_upstream_state_is_required() -> None:
    """Any one false blocks concordance; none is individually sufficient."""
    # Eligible manifestation and copy, but nothing transcribed.
    no_passages = _capabilities(_eligible_corpus())

    assert no_passages.source_copy_verified is True
    assert no_passages.construct_equivalence_established is False
    assert no_passages.concordance_eligible is False


def test_full_pipeline_becomes_eligible() -> None:
    """The flags do turn on -- the gate is not merely always-false."""
    capabilities = _capabilities(_eligible_corpus([_passage()]))

    assert capabilities.source_copy_verified is True
    assert capabilities.construct_equivalence_established is True
    assert capabilities.direct_denotations_available is True
    assert capabilities.hashes_agree is True
    assert capabilities.concordance_eligible is True
    assert capabilities.blocking == ()


def test_a_stale_dictionary_is_not_eligible() -> None:
    """A non-empty dictionary compiled against different evidence fails.

    This is what gating on "dictionary is non-empty" would have missed: the
    entries exist, but they describe a corpus that has since changed.
    """
    original = _eligible_corpus([_passage()])
    rules = AdmissibilityRules()
    dictionary, report = compile_dictionary(original, rules)

    # The corpus gains a passage after the dictionary was compiled.
    changed = _eligible_corpus([_passage(), _passage("p2")])

    capabilities = derive_capabilities(changed, rules, dictionary, report)

    assert dictionary.entries  # non-empty, and still not eligible
    assert capabilities.hashes_agree is False
    assert capabilities.concordance_eligible is False


def test_changed_rules_invalidate_eligibility() -> None:
    """A dictionary compiled under superseded rules cannot be reused."""
    corpus = _eligible_corpus([_passage()])
    dictionary, report = compile_dictionary(corpus, AdmissibilityRules())

    capabilities = derive_capabilities(
        corpus,
        AdmissibilityRules(version="9.9.9", minimum_confidence=0.99),
        dictionary,
        report,
    )

    assert capabilities.hashes_agree is False
    assert capabilities.concordance_eligible is False


def test_capabilities_state_what_cannot_be_claimed() -> None:
    """The boundary stays prominent in the artifact itself."""
    payload = _capabilities(declared_corpus()).to_dict()

    assert payload["concordance_eligible"] is False
    assert any("11, 22 or 33" in claim for claim in payload["cannot_claim"])
    assert any(
        "agrees or disagrees with Kamea" in claim
        for claim in payload["cannot_claim"]
    )


# ---------------------------------------------------------------------------
# Legacy quarantine
# ---------------------------------------------------------------------------


def _imported_modules(path: Path) -> list[str]:
    """Return every module imported by one source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)

    return modules


def test_no_1e_module_imports_the_legacy_adapter() -> None:
    """The largest accidental-entry path, closed.

    evidence_from_number maps numbers to structural evidence with no source,
    tradition, edition, page or construct-equivalence verdict. If a 1E module
    could reach it, the provenance architecture and the interpretation
    shortcut would coexist and a later caller could unknowingly take the
    shortcut.
    """
    offenders: list[str] = []

    for path in sorted(DENOTATION_PACKAGE.glob("*.py")):
        for module in _imported_modules(path):
            if "synthesis.adapters" in module or "synthesis" == module:
                offenders.append(f"{path.name} imports {module}")

    assert not offenders, offenders


def test_no_1e_module_references_evidence_from_number() -> None:
    """Not imported, and not called by any other route."""
    offenders: list[str] = []

    for path in sorted(DENOTATION_PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Name)
                and node.id == "evidence_from_number"
            ) or (
                isinstance(node, ast.Attribute)
                and node.attr == "evidence_from_number"
            ):
                offenders.append(path.name)

    assert not offenders, offenders


def test_the_legacy_shortcut_is_recorded_as_present_but_forbidden() -> None:
    """Documented rather than silently avoided, so it stays visible."""
    assert LEGACY_UNPROVENANCED_INTERPRETATION["present"] is True
    assert LEGACY_UNPROVENANCED_INTERPRETATION["permitted_in_1E"] is False
    assert "no source" in LEGACY_UNPROVENANCED_INTERPRETATION["reason"]


def test_the_legacy_adapter_still_exists_outside_1e() -> None:
    """The quarantine is a boundary, not a deletion.

    Other callers may still use it; the assertion is only that 1E does not.
    If it is ever removed, this test should be removed with it rather than
    left asserting a stale fact.
    """
    from atlas.synthesis.adapters import numerology as legacy

    assert hasattr(legacy, "evidence_from_number")


# ---------------------------------------------------------------------------
# The expression layer stays independent
# ---------------------------------------------------------------------------


def test_expression_layer_imports_nothing_interpretive() -> None:
    """Computation must not see the vocabulary it feeds."""
    modules = _imported_modules(
        DENOTATION_PACKAGE / "numerology_expression.py"
    )

    for module in modules:
        assert "ontology" not in module
        assert "synthesis" not in module
        assert "kamea" not in module
