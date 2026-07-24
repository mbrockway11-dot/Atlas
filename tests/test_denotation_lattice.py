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
    ADMISSION_REGISTER,
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
    "gematria_orthography": 0,
    "source_tiers": 0,
    "acquisition_targets": 4,
    # 1 -- source verification: bibliography, corpus, schemes awaiting citation
    "numerology_bibliography": 1,
    "numerology_corpus": 1,
    "numerology_corpus_v1": 1,
    "gematria_transliteration": 1,
    "gematria_hebrew": 1,
    "gematria_value_method": 1,
    "gematria_pipeline": 1,
    "vedic_ayanamsa": 1,
    "gematria_capabilities": 4,
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


def test_no_system_is_left_unclassified() -> None:
    """Every registered system has been decomposed.

    Numerology, gematria and Vedic have each been classified into their own
    layer set; nothing remains at the UNCLASSIFIED default.
    """
    unclassified = [
        layer
        for layer in layers_for("vedic") + layers_for("gematria")
        + layers_for("numerology")
        if layer.admission_class is AdmissionClass.UNCLASSIFIED
    ]

    assert unclassified == []


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


# ---------------------------------------------------------------------------
# Gematria admission (1E-G-CLASSIFY)
# ---------------------------------------------------------------------------


def test_gematria_decomposes_differently_from_numerology() -> None:
    """The methodology test: a different system, a different decomposition.

    If gematria had merely mirrored numerology's layers, that would suggest
    the 1E process was overfit to numerology. It does not: gematria needs a
    transliteration layer and an equivalence relation, neither of which
    numerology has any analogue for.
    """
    gematria = {layer.layer for layer in layers_for("gematria")}
    numerology = {layer.layer for layer in layers_for("numerology")}

    # Layers with no numerology analogue at all.
    assert {"transliteration", "equivalence_relation"} <= gematria
    assert not ({"transliteration", "equivalence_relation"} & numerology)
    # Both legitimately have a denotation layer -- every interpretive system
    # does. The finding is the layers gematria needs and numerology does not.
    assert gematria - numerology >= {
        "transliteration",
        "equivalence_relation",
        "orthographic_scope",
        "letter_value_assignment",
    }
    assert len(gematria) > len(numerology)


def test_english_ordinal_is_registered_apart_from_gematria() -> None:
    """A=1..Z=26 shares no tradition or alphabet with Hebrew gematria."""
    from atlas.validation.denotation.admission import registered_systems

    assert "english_ordinal" in registered_systems()
    assert layers_for("english_ordinal")[0].system != "gematria"


def test_gematria_transliteration_needs_textual_authority() -> None:
    """Which Hebrew letter a Latin letter represents is a convention."""
    (layer,) = [
        item
        for item in layers_for("gematria")
        if item.layer == "transliteration"
    ]

    assert layer.admission_class is AdmissionClass.TEXTUAL_INTERPRETATION
    assert layer.admitted is False
    assert "fused" in layer.note or "welded" in layer.note


def test_the_equivalence_layer_is_hybrid_and_unimplemented() -> None:
    """Gematria's characteristic operation is relational, not denotational."""
    (layer,) = [
        item
        for item in layers_for("gematria")
        if item.layer == "equivalence_relation"
    ]

    assert layer.admission_class is AdmissionClass.HYBRID
    assert layer.admitted is False
    assert "comparison corpus" in layer.note


def test_admission_does_not_launder_inputs() -> None:
    """An admitted layer consuming unlicensed input stays unusable.

    Gematria's numeric computation is reproducible arithmetic, and it is
    admitted. It still contributes nothing, because everything upstream of
    it is inadmissible.
    """
    from atlas.validation.denotation.admission import admissible_in_isolation

    # After 1E-G-REPAIR both the orthographic scope check and the numeric
    # computation are reproducible and admitted in isolation. Neither can
    # feed a denotation, because transliteration and value assignment between
    # them are unlicensed -- so gematria still denotes nothing.
    # After 1E-G-SOURCE-A, Hebrew letter identity is also admitted (sourced
    # to Unicode). Three admitted layers, and gematria still denotes nothing:
    # letter values between identity and computation remain unlicensed.
    assert admissible_in_isolation("gematria") == [
        "orthographic_scope",
        "hebrew_orthography",
        "numeric_computation",
    ]
    assert "gematria" not in admitted_systems()


def test_gematria_denotes_nothing() -> None:
    """No layer of gematria reaches the denotation stage."""
    assert all(
        layer.highest_stage_reached is not LatticeStage.DENOTATION
        for layer in layers_for("gematria")
    )


def test_classification_did_not_change_concordance_readiness() -> None:
    """Classifying a system is not admitting it."""
    assert admitted_systems() == ["kamea"]
    assert concordance_ready() is False


# ---------------------------------------------------------------------------
# Vedic admission (1E-V-CLASSIFY)
# ---------------------------------------------------------------------------


def test_vedic_decomposes_into_more_layers_than_gematria() -> None:
    """The methodology test again: a third system, a third decomposition.

    Numerology had two layers, gematria six, Vedic eight -- and Vedic's
    load-bearing choices (ayanamsa, house system) have no analogue in either
    prior system.
    """
    vedic = {layer.layer for layer in layers_for("vedic")}
    gematria = {layer.layer for layer in layers_for("gematria")}
    numerology = {layer.layer for layer in layers_for("numerology")}

    assert len(vedic) > len(gematria) > len(numerology)
    assert "ayanamsa_framework" in vedic
    assert "house_system" in vedic
    assert not (vedic & gematria) - {"denotation"}


def test_vedic_ephemeris_is_admitted_by_computation() -> None:
    """The same pinned engine Kamea uses; reproducible, admitted."""
    (ephemeris,) = [
        item for item in layers_for("vedic") if item.layer == "ephemeris"
    ]

    assert ephemeris.admission_class is AdmissionClass.DERIVED_COMPUTATION
    assert ephemeris.admitted is True


def test_ayanamsa_is_a_school_choice_needing_a_source() -> None:
    """Vedic's characteristic fork: which sidereal offset."""
    (ayanamsa,) = [
        item
        for item in layers_for("vedic")
        if item.layer == "ayanamsa_framework"
    ]

    assert ayanamsa.admission_class is AdmissionClass.TEXTUAL_INTERPRETATION
    assert ayanamsa.admitted is False
    assert "Lahiri" in ayanamsa.note


def test_sidereal_computation_admitted_but_not_laundering_ayanamsa() -> None:
    """Nakshatra and vargas are admitted in isolation and still blocked.

    They consume ayanamsa-offset longitudes, so like gematria's numeric
    computation over unlicensed transliteration, they contribute nothing
    while the ayanamsa is unlicensed.
    """
    from atlas.validation.denotation.admission import admissible_in_isolation

    admitted = admissible_in_isolation("vedic")

    assert "nakshatra_assignment" in admitted
    assert "divisional_charts" in admitted
    assert "ayanamsa_framework" not in admitted
    assert "vedic" not in admitted_systems()


def test_dasha_is_hybrid_with_uncited_period_values() -> None:
    """Traditional period lengths, deterministic arithmetic."""
    (dasha,) = [
        item for item in layers_for("vedic") if item.layer == "dasha_system"
    ]

    assert dasha.admission_class is AdmissionClass.HYBRID
    assert dasha.admitted is False
    assert "120" in dasha.note


def test_vedic_denotation_is_uncited_and_quarantined() -> None:
    """The interpretation layer has no provenance and stays out of 1E."""
    from atlas.validation.denotation.admission import (
        INTERPRETATION_QUARANTINE,
    )

    (denotation,) = [
        item for item in layers_for("vedic") if item.layer == "denotation"
    ]

    assert denotation.admitted is False
    assert "uncited" in denotation.note

    vedic_quarantine = [
        entry
        for entry in INTERPRETATION_QUARANTINE
        if entry["system"] == "vedic"
    ]

    assert vedic_quarantine
    assert all(not e["permitted_in_1E"] for e in vedic_quarantine)


def test_no_1e_module_imports_a_quarantined_interpretation() -> None:
    """No denotation module reaches an uncited interpretation entry point."""
    from atlas.validation.denotation.admission import (
        INTERPRETATION_QUARANTINE,
    )

    forbidden = {entry["module"] for entry in INTERPRETATION_QUARANTINE}
    offenders: list[str] = []

    for path in _package_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module in forbidden:
                    offenders.append(f"{path.stem} imports {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden:
                        offenders.append(f"{path.stem} imports {alias.name}")

    assert not offenders, offenders


def test_vedic_denotes_nothing_and_concordance_unchanged() -> None:
    """Classifying Vedic did not admit it; only Kamea still denotes."""
    assert all(
        layer.highest_stage_reached is not LatticeStage.DENOTATION
        for layer in layers_for("vedic")
    )
    assert admitted_systems() == ["kamea"]
    assert concordance_ready() is False


# ---------------------------------------------------------------------------
# Kamea is structurally a measurement system (the 1D->1E through-line)
# ---------------------------------------------------------------------------


def test_kamea_denotes_by_measurement_with_no_textual_layer() -> None:
    """Kamea reaches denotation with zero textual_interpretation layers.

    The permanent structural fact behind Kamea's admission. Applying the same
    source-layer taxonomy to Kamea reveals no 'traditional rule -> meaning'
    branch: 1D showed its structure is directly measurable, and 1E admitted
    it through measurement rather than textual authority. Its source stack is
    thin by construction, not by omission.
    """
    (kamea,) = layers_for("kamea")

    assert kamea.admission_class is AdmissionClass.DIRECT_MEASUREMENT
    assert kamea.highest_stage_reached is LatticeStage.DENOTATION
    assert kamea.admitted is True

    textual = [
        layer
        for layer in layers_for("kamea")
        if layer.admission_class is AdmissionClass.TEXTUAL_INTERPRETATION
    ]

    assert textual == []


def test_every_interpretive_system_has_a_textual_layer() -> None:
    """Numerology, gematria and Vedic all require textual authority.

    The contrast that makes Kamea's shape meaningful: each interpretive system
    develops a 'primary source -> rule -> interpretation' branch that Kamea
    never does.
    """
    for system in ("numerology", "gematria", "vedic"):
        textual = [
            layer
            for layer in layers_for(system)
            if layer.admission_class
            is AdmissionClass.TEXTUAL_INTERPRETATION
        ]

        assert textual, system


def test_the_only_admitted_denotation_is_measurement_licensed() -> None:
    """The acquisition frontier: measurement denotes, text is still blocked.

    This is the invariant that a source event will change. When the first
    verified source admits a textual denotation, this test must be updated to
    name the new denoting system -- which is exactly the acknowledgement a
    capability gain should force. Until then, Kamea alone denotes, by
    measurement.
    """
    admitted_denotations = [
        layer
        for layer in ADMISSION_REGISTER
        if layer.highest_stage_reached is LatticeStage.DENOTATION
        and layer.admitted
    ]

    assert [layer.system for layer in admitted_denotations] == ["kamea"]
    assert all(
        layer.admission_class is AdmissionClass.DIRECT_MEASUREMENT
        for layer in admitted_denotations
    )
    assert admitted_systems() == ["kamea"]
    assert concordance_ready() is False
