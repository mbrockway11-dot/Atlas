"""Admission classification: what evidence a system owes before it speaks.

1E inverted its own default. The early question was "can we derive denotations
from independent systems?"; after the capability gate it is "**can this system
legitimately speak at all?**" Those are different questions -- the first is
semantic, the second epistemic -- and the second changes the default from
*everything speaks unless excluded* to **everything is silent unless
admitted**.

Admission is not one gate, because systems are not alike. A system is admitted
per *layer*, and its layers may fall into different classes::

    direct measurement       observable computation      measurement reproducibility
    derived computation      deterministic algorithm     computational reproducibility
    textual interpretation   source corpus               provenance + construct equivalence
    hybrid                   both                        must satisfy both independently

The classification decides what evidence is owed, so it must be made **before
implementation begins**. Assuming numerology, gematria and Vedic are three
instances of one "interpretive system" would be wrong: gematria plausibly
splits into deterministic letter-to-number computation *and* textual
interpretation of the resulting value, and Vedic into astronomical
computation, rule-based chart construction, *and* textual interpretation.
Each layer is its own admission problem.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


ADMISSION_SCHEMA = "atlas.validation.denotation.admission.v1"


class AdmissionClass(str, Enum):
    """What kind of evidence a layer's admission rests on."""

    DIRECT_MEASUREMENT = "direct_measurement"
    DERIVED_COMPUTATION = "derived_computation"
    TEXTUAL_INTERPRETATION = "textual_interpretation"
    HYBRID = "hybrid"
    # The default. A layer nobody has classified owes unknown evidence, and
    # unknown evidence cannot be supplied.
    UNCLASSIFIED = "unclassified"


PROVENANCE_REQUIREMENT: dict[AdmissionClass, str] = {
    AdmissionClass.DIRECT_MEASUREMENT: "measurement reproducibility",
    AdmissionClass.DERIVED_COMPUTATION: "computational reproducibility",
    AdmissionClass.TEXTUAL_INTERPRETATION: (
        "verified source provenance and construct equivalence"
    ),
    AdmissionClass.HYBRID: (
        "both computational reproducibility and source provenance, satisfied "
        "independently"
    ),
    AdmissionClass.UNCLASSIFIED: (
        "unknown until classified; no layer may be implemented while "
        "unclassified"
    ),
}


class LatticeStage(str, Enum):
    """The frozen provenance lattice.

    Every arrow is a gate with its own evidence requirement, which is
    stronger than a general instruction not to interpret too early::

        measurement -> computation -> construct identity
                    -> source verification -> denotation -> concordance
    """

    MEASUREMENT = "measurement"
    COMPUTATION = "computation"
    CONSTRUCT_IDENTITY = "construct_identity"
    SOURCE_VERIFICATION = "source_verification"
    DENOTATION = "denotation"
    CONCORDANCE = "concordance"


LATTICE_ORDER: tuple[LatticeStage, ...] = (
    LatticeStage.MEASUREMENT,
    LatticeStage.COMPUTATION,
    LatticeStage.CONSTRUCT_IDENTITY,
    LatticeStage.SOURCE_VERIFICATION,
    LatticeStage.DENOTATION,
    LatticeStage.CONCORDANCE,
)


class AdmissionError(ValueError):
    """A layer was described or used invalidly."""


@dataclass(frozen=True, slots=True)
class SystemLayer:
    """One admissible layer of a system.

    Systems are admitted per layer because a single system may owe different
    evidence for different outputs -- gematria's letter-to-number arithmetic
    is reproducible computation, while what the resulting value denotes is
    textual interpretation.
    """

    system: str
    layer: str
    admission_class: AdmissionClass
    highest_stage_reached: LatticeStage
    admitted: bool
    note: str = ""

    def __post_init__(self) -> None:
        if self.admitted and (
            self.admission_class is AdmissionClass.UNCLASSIFIED
        ):
            raise AdmissionError(
                f"{self.system}/{self.layer} cannot be admitted while "
                "unclassified: the evidence it owes is undetermined."
            )

    @property
    def provenance_requirement(self) -> str:
        """Return the evidence this layer must supply."""
        return PROVENANCE_REQUIREMENT[self.admission_class]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "system": self.system,
            "layer": self.layer,
            "admission_class": self.admission_class.value,
            "provenance_requirement": self.provenance_requirement,
            "highest_stage_reached": self.highest_stage_reached.value,
            "admitted": self.admitted,
            "note": self.note,
        }


# The current admission register. A system absent from this register, or
# present but unclassified, may not be implemented -- classification decides
# what evidence it owes, so it precedes the work rather than describing it
# afterwards.
ADMISSION_REGISTER: tuple[SystemLayer, ...] = (
    SystemLayer(
        system="kamea",
        layer="structural_trajectory",
        admission_class=AdmissionClass.DIRECT_MEASUREMENT,
        highest_stage_reached=LatticeStage.DENOTATION,
        admitted=True,
        note=(
            "Claims are computed from a path's measured geometry by fixed "
            "rule. No source is owed because nothing textual is asserted; "
            "1D established the square contributes only a subtractive "
            "coarsening, so Kamea denotes structure and never symbolism."
        ),
    ),
    SystemLayer(
        system="numerology",
        layer="arithmetic",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "Deterministic and versioned, with the reduction policy and full "
            "trace recorded. Admitted as computation only; it denotes "
            "nothing on its own."
        ),
    ),
    SystemLayer(
        system="numerology",
        layer="denotation",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.SOURCE_VERIFICATION,
        admitted=False,
        note=(
            "Blocked at source verification: no transcription-eligible "
            "manifestation with a source copy. Construct equivalence is "
            "therefore also unestablished. Baseline 07af099."
        ),
    ),
    # Gematria decomposes into six layers -- see
    # docs/GEMATRIA_ADMISSION_CLASSIFICATION.md. Two have no numerology
    # analogue at all, which is the evidence that the 1E process is not
    # overfit to numerology.
    SystemLayer(
        system="gematria",
        layer="orthographic_scope",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=False,
        note=(
            "Blocking defect: normalize_text accepts Hebrew characters "
            "(isalpha is true) and the value tables then drop every one, so "
            "Hebrew input yields an empty sequence silently. A layer that "
            "returns nothing for text it is named after is deterministic but "
            "not reproducible. Fix by refusing out-of-alphabet input and "
            "declaring the Latin-only boundary; needs no source."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="transliteration",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        admitted=False,
        note=(
            "No numerology analogue. Which Hebrew letter a Latin letter "
            "represents is an editorial convention, and it is welded into "
            "HEBREW_LITERAL_VALUES together with the value assignment, so "
            "neither can be checked separately. Non-injective as well: "
            "U/V/W, I/J/Y, C/K, S/X and F/P each collapse onto one value. "
            "Must be split out before any citation could verify it."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="letter_value_assignment",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        admitted=False,
        note=(
            "The Hebrew letter values are well attested, so this is expected "
            "to be the most tractable of the textual layers -- but it cannot "
            "be cited while fused with transliteration."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="numeric_computation",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "Summing a sequence of integers is not in doubt. Admitted in "
            "isolation only: it consumes transliteration output, and a "
            "layer's admission covers its own operation, never its inputs."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="equivalence_relation",
        admission_class=AdmissionClass.HYBRID,
        highest_stage_reached=LatticeStage.MEASUREMENT,
        admitted=False,
        note=(
            "Gematria's characteristic operation and its sharpest difference "
            "from numerology: the semantic move is equivalence between texts "
            "sharing a value, not denotation of a number. Not implemented at "
            "all. Specifying it requires declaring a comparison corpus, "
            "since which texts may be compared determines every equivalence "
            "found -- so corpus selection is textual authority, not "
            "computation."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="denotation",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.MEASUREMENT,
        admitted=False,
        note=(
            "No citation corpus. Blocked behind the same acquisition gate "
            "numerology is blocked on."
        ),
    ),
    # Registered apart from gematria deliberately. A=1..Z=26 over the Latin
    # alphabet shares no tradition, alphabet or value assignment with Hebrew
    # gematria; filing it under gematria would be the category error the
    # tradition boundary exists to prevent.
    SystemLayer(
        system="english_ordinal",
        layer="ordinal_computation",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "A modern English ordinal cipher, not gematria. Deterministic "
            "and admitted as computation; it denotes nothing on its own."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="unclassified",
        admission_class=AdmissionClass.UNCLASSIFIED,
        highest_stage_reached=LatticeStage.MEASUREMENT,
        admitted=False,
        note=(
            "Must be decomposed before implementation. Astronomical "
            "computation, rule-based chart construction and textual "
            "interpretation may each deserve their own capability state."
        ),
    ),
)


def layers_for(system: str) -> list[SystemLayer]:
    """Return every registered layer of one system."""
    return [layer for layer in ADMISSION_REGISTER if layer.system == system]


def registered_systems() -> list[str]:
    """Return every system with a classification, admitted or not."""
    return sorted({layer.system for layer in ADMISSION_REGISTER})


def admissible_in_isolation(system: str) -> list[str]:
    """Return a system's admitted layers.

    Named to prevent the reading it invites. A layer's admission covers its
    own operation, never its inputs -- gematria's numeric computation is
    reproducible arithmetic consuming unlicensed transliteration output, so
    it is admitted and still contributes nothing usable downstream. This is
    the feed-forward invariant applied to data rather than imports.
    """
    return [layer.layer for layer in layers_for(system) if layer.admitted]


def admitted_systems() -> list[str]:
    """Return systems with at least one layer admitted at denotation.

    Concordance needs systems that can *denote*, not merely compute, so a
    system admitted only for arithmetic does not count.
    """
    return sorted(
        {
            layer.system
            for layer in ADMISSION_REGISTER
            if layer.admitted
            and layer.highest_stage_reached is LatticeStage.DENOTATION
        }
    )


def concordance_ready() -> bool:
    """Return whether a cross-system concordance can run at all.

    Two eligible systems are the minimum; one system agreeing with itself is
    not evidence of anything.
    """
    return len(admitted_systems()) >= 2


def admission_report() -> dict[str, Any]:
    """Return the current admission state, for the record."""
    return {
        "schema": ADMISSION_SCHEMA,
        "default": "silent unless admitted",
        "lattice": [stage.value for stage in LATTICE_ORDER],
        "classes": {
            cls.value: requirement
            for cls, requirement in PROVENANCE_REQUIREMENT.items()
        },
        "layers": [layer.to_dict() for layer in ADMISSION_REGISTER],
        "admitted_denoting_systems": admitted_systems(),
        "concordance_ready": concordance_ready(),
        "note": (
            "No symbolic concordance has been performed because only one "
            "system currently denotes. That is a statement about the "
            "evidence, not only about implementation progress."
        ),
    }
