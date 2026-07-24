"""The feed-forward invariant, enforced against the real import graph.

> No stage may satisfy a downstream gate by importing an artifact produced by
> a downstream stage.

Obvious when stated, and it forbids an entire class of accidental
circularity: construct equivalence inferred from ontology agreement, ontology
agreement inferred from concordance, concordance used to justify dictionary
entries, dictionary entries rewritten because concordance "looked wrong".

Stated as a rule it is advice. Checked against the module graph it is a
constraint that fails a build, which is what makes it worth having.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from atlas.validation.denotation.admission import (
    LATTICE_ORDER,
    AdmissionClass,
    AdmissionError,
    LatticeStage,
    SystemLayer,
    admission_report,
    admitted_systems,
    concordance_ready,
    layers_for,
)


DENOTATION_PACKAGE = Path("src/atlas/validation/denotation")


# Each module's position in the lattice. Imports may point at the same stage
# or an earlier one, never a later one.
MODULE_STAGE: dict[str, int] = {
    # 0 -- base vocabulary and pure computation; import nothing internal
    "ontology": 0,
    "numerology_tradition": 0,
    "numerology_expression": 0,
    # 1 -- source verification: bibliography, corpus, declared corpus
    "numerology_bibliography": 1,
    "numerology_corpus": 1,
    "numerology_corpus_v1": 1,
    # 2 -- denotation: claims, dictionary, compilation
    "expressions": 2,
    "numerology_dictionary": 2,
    "numerology_compiler": 2,
    "kamea_denotation": 2,
    # 3 -- concordance: relations and scoring
    "relations": 3,
    "concordance": 3,
    "controls": 3,
    # 4 -- governance gates, which read artifacts in order to authorize them
    "numerology_capabilities": 4,
    "admission": 4,
}


def _internal_imports(path: Path) -> list[str]:
    """Return denotation-package modules imported by one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if "denotation." in node.module:
                modules.append(node.module.split("denotation.")[1])

    return modules


def _package_modules() -> list[Path]:
    """Return every non-init module in the denotation package."""
    return [
        path
        for path in sorted(DENOTATION_PACKAGE.glob("*.py"))
        if path.stem != "__init__"
    ]


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------


def test_every_module_has_a_declared_stage() -> None:
    """A new module must be placed in the lattice, not left unplaced.

    Without this the invariant would silently stop covering new code.
    """
    unplaced = [
        path.stem for path in _package_modules()
        if path.stem not in MODULE_STAGE
    ]

    assert not unplaced, f"place these in MODULE_STAGE: {unplaced}"


def test_no_module_imports_a_later_stage() -> None:
    """The feed-forward invariant, checked against the real graph."""
    violations: list[str] = []

    for path in _package_modules():
        stage = MODULE_STAGE[path.stem]

        for imported in _internal_imports(path):
            imported_stage = MODULE_STAGE.get(imported)

            if imported_stage is None:
                violations.append(
                    f"{path.stem} imports unplaced {imported}"
                )
            elif imported_stage > stage:
                violations.append(
                    f"{path.stem} (stage {stage}) imports {imported} "
                    f"(stage {imported_stage})"
                )

    assert not violations, violations


def test_source_layers_cannot_see_the_ontology() -> None:
    """Construct identity may not be inferred from ontology agreement.

    The corpus records a proposed coordinate as a plain string precisely so
    that transcription cannot be steered by the vocabulary it will later be
    checked against.
    """
    for module in (
        "numerology_corpus",
        "numerology_bibliography",
        "numerology_corpus_v1",
    ):
        imports = _internal_imports(DENOTATION_PACKAGE / f"{module}.py")

        assert "ontology" not in imports, module


def test_denotation_layers_cannot_see_concordance() -> None:
    """Dictionary entries may not be justified by, or rewritten from, results."""
    for module in (
        "numerology_dictionary",
        "numerology_compiler",
        "kamea_denotation",
        "expressions",
    ):
        imports = _internal_imports(DENOTATION_PACKAGE / f"{module}.py")

        for downstream in ("concordance", "controls", "relations"):
            assert downstream not in imports, f"{module} -> {downstream}"


def test_computation_imports_nothing_internal() -> None:
    """Numerology arithmetic sits at the base and depends on nothing here."""
    assert (
        _internal_imports(DENOTATION_PACKAGE / "numerology_expression.py")
        == []
    )


# ---------------------------------------------------------------------------
# Admission classification
# ---------------------------------------------------------------------------


def test_the_lattice_is_ordered_and_complete() -> None:
    """Every stage appears exactly once, in order."""
    assert LATTICE_ORDER[0] is LatticeStage.MEASUREMENT
    assert LATTICE_ORDER[-1] is LatticeStage.CONCORDANCE
    assert len(set(LATTICE_ORDER)) == len(LatticeStage)


def test_an_unclassified_layer_cannot_be_admitted() -> None:
    """Classification decides what evidence is owed, so it comes first."""
    with pytest.raises(AdmissionError, match="unclassified"):
        SystemLayer(
            system="gematria",
            layer="whatever",
            admission_class=AdmissionClass.UNCLASSIFIED,
            highest_stage_reached=LatticeStage.DENOTATION,
            admitted=True,
        )


def test_kamea_is_admitted_by_measurement_not_by_source() -> None:
    """Direct measurement owes reproducibility, not provenance."""
    (layer,) = layers_for("kamea")

    assert layer.admission_class is AdmissionClass.DIRECT_MEASUREMENT
    assert layer.admitted
    assert "measurement reproducibility" == layer.provenance_requirement


def test_numerology_is_admitted_for_arithmetic_but_not_denotation() -> None:
    """One system, two layers, two different verdicts.

    The arithmetic is reproducible and admitted; the denotation is blocked at
    source verification. Treating the system as a single admission unit would
    have let the second inherit the first's standing.
    """
    layers = {layer.layer: layer for layer in layers_for("numerology")}

    assert layers["arithmetic"].admitted is True
    assert layers["arithmetic"].admission_class is (
        AdmissionClass.DERIVED_COMPUTATION
    )
    assert layers["denotation"].admitted is False
    assert layers["denotation"].highest_stage_reached is (
        LatticeStage.SOURCE_VERIFICATION
    )


def test_gematria_and_vedic_are_unclassified_and_undecomposed() -> None:
    """They may not inherit numerology's classification by analogy."""
    for system in ("gematria", "vedic"):
        (layer,) = layers_for(system)

        assert layer.admission_class is AdmissionClass.UNCLASSIFIED
        assert layer.admitted is False
        assert "decomposed before implementation" in layer.note


def test_only_kamea_currently_denotes() -> None:
    """Computation alone does not make a system eligible to concord."""
    assert admitted_systems() == ["kamea"]


def test_concordance_is_not_ready() -> None:
    """A scientific statement about the evidence, not only about progress.

    One system agreeing with itself is not evidence of anything, so 1E-A
    cannot run until a second system is admitted at denotation.
    """
    assert concordance_ready() is False

    report = admission_report()

    assert report["default"] == "silent unless admitted"
    assert report["admitted_denoting_systems"] == ["kamea"]
    assert "only one system currently denotes" in report["note"]
