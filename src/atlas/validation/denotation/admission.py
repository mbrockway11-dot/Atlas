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
        highest_stage_reached=LatticeStage.DENOTATION,
        admitted=True,
        note=(
            "Admitted 1E-N-SOURCE-A. numerology_corpus_v2 copy-verifies the "
            "Jordan DeVorss 11th printing (2003, ISBN 0875162274) from its own "
            "title, copyright and pagination pages -- a digital surrogate (IA "
            "scan), recorded as such -- and doubly transcribes the nine "
            "general number-denotations of the 'Significance and Meaning of "
            "Numbers' chapter (OCR plus page-image read). Each denotes the "
            "reduced value itself (quantity-independent), construct-"
            "equivalent to the code's Pythagorean reduction, mapped onto the "
            "shared ontology interpretively and blind to Kamea. Compiles to "
            "nine source-specific entries; concordance_eligible is True. The "
            "first non-Kamea denoting system -- so concordance_ready flips."
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
        # Repaired in 1E-G-REPAIR: check_scope is fail-closed and reports
        # every rejected symbol, so the silent-truncation defect is gone and
        # the layer is now reproducible.
        admitted=True,
        note=(
            "Repaired. gematria_orthography.check_scope declares accepted "
            "scripts and distinguishes EMPTY_INPUT from NO_LICENSED_SYMBOLS, "
            "so Hebrew input to a Latin scheme raises instead of returning an "
            "empty sequence. Admitted as reproducible computation; the legacy "
            "atlas.ciphers path stays for its other callers and is "
            "quarantined from 1E."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="hebrew_orthography",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        # Admitted in 1E-G-SOURCE-A. Letter identity is sourced to the Unicode
        # standard, which is normative and machine-verifiable -- unlike a
        # gematria value, a letter's identity is fixed by the orthographic
        # standard and checked at runtime against unicodedata. The first
        # genuinely source-backed non-measurement layer in the system.
        admitted=True,
        note=(
            "Direct Hebrew, no transliteration. Code point -> letter identity "
            "sourced to The Unicode Standard, Hebrew block, verified against "
            "unicodedata. Latin input is blocked in this path. Licenses "
            "identity only: Unicode assigns Hebrew letters no numeric value."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="transliteration",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        # Split out in 1E-G-REPAIR, so it CAN now be cited -- but no scheme is
        # admitted, so it stays inadmissible pending 1E-G-SOURCE. Superseded
        # as the first path by direct Hebrew, which needs no convention.
        admitted=False,
        note=(
            "No numerology analogue. Split from value assignment in "
            "1E-G-REPAIR into gematria_transliteration, so the Latin->Hebrew "
            "editorial convention is now separately representable and "
            "hashable. Zero admitted schemes: the legacy fused mapping is "
            "registered as a candidate only, non-injective and uncited. A "
            "convenience layer, secondary to direct Hebrew; admission awaits "
            "1E-G-SOURCE."
        ),
    ),
    SystemLayer(
        system="gematria",
        layer="letter_value_assignment",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.SOURCE_VERIFICATION,
        admitted=False,
        note=(
            "1E-G-SOURCE-A structured this as a named ValueMethod "
            "(mispar-hechrachi-candidate) carrying every choice that affects "
            "the number, but no method is admitted: Unicode assigns Hebrew "
            "letters no value, so this is a traditional claim needing a "
            "traditional source, and admission requires a source copy hash "
            "and locator this phase does not have. Same acquisition wall as "
            "numerology, one layer along."
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
    # Vedic decomposes into eight layers -- see
    # docs/VEDIC_ADMISSION_CLASSIFICATION.md. More than gematria's six and
    # numerology's two, and with two school-specific choices (ayanamsa, house
    # system) that neither prior system has any analogue for.
    SystemLayer(
        system="vedic",
        layer="ephemeris",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "Tropical geocentric positions from Swiss Ephemeris, the same "
            "pinned engine Kamea and Temporal use. Deterministic and "
            "reproducible, admitted in isolation. It underlies everything "
            "but denotes nothing."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="ayanamsa_framework",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.SOURCE_VERIFICATION,
        admitted=True,
        note=(
            "Admitted 1E-V-SOURCE-A. Vedic is sidereal, so which ayanamsa is a "
            "school-specific claim; Lahiri is now licensed by the Government "
            "of India standard -- the Calendar Reform Committee (1955), whose "
            "Secretary N.C. Lahiri gives it its name -- verified against the "
            "committee's own recommendation (p.7: ayanamsa 23 deg 15' at 21 "
            "Mar 1956, precessing ~50\".27/yr; zero-point 180 deg from Spica), "
            "page-image checked, with Swiss Ephemeris SIDM_LAHIRI as the "
            "construct-equivalent implementation. Raman and Krishnamurti stay "
            "unadmitted. This licenses the sidereal OFFSET (a computation), so "
            "sidereal quantities naming the Lahiri choice hash are now "
            "unblocked; it does NOT make Vedic denote -- the denotation layer "
            "is still unbuilt and unsourced."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="house_system",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        admitted=False,
        note=(
            "A second school-specific choice. build_house_chart implements "
            "Whole Sign only and raises on others, so the default is baked in "
            "without being declared as one of several traditions. Needs a "
            "source for the selected system before admission."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="nakshatra_assignment",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "The 27-fold division of the ecliptic is a deterministic function "
            "of sidereal longitude. Admitted in isolation only: it consumes "
            "ayanamsa-offset longitudes, and a layer's admission covers its "
            "own operation never its inputs, so it contributes nothing while "
            "the ayanamsa is unlicensed."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="divisional_charts",
        admission_class=AdmissionClass.DERIVED_COMPUTATION,
        highest_stage_reached=LatticeStage.COMPUTATION,
        admitted=True,
        note=(
            "Vargas and navamsa are deterministic transforms of longitude. "
            "Admitted in isolation, and inherit the same unlicensed-input "
            "block as nakshatra assignment."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="dasha_system",
        admission_class=AdmissionClass.HYBRID,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        admitted=False,
        note=(
            "Vimshottari period lengths (Ketu 7, Venus 20, ... summing to 120 "
            "years) are traditional VALUES hardcoded with no source, while "
            "the period arithmetic is deterministic. Hybrid: the arithmetic "
            "is reproducible but the values are a traditional claim, and "
            "Vimshottari is itself one dasha system among several. Not "
            "admitted."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="dignity_and_yoga_rules",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.CONSTRUCT_IDENTITY,
        admitted=False,
        note=(
            "Exaltation and debilitation signs, and yoga formation rules, are "
            "traditional classifications hardcoded without citation. Textual "
            "authority, not admitted."
        ),
    ),
    SystemLayer(
        system="vedic",
        layer="denotation",
        admission_class=AdmissionClass.TEXTUAL_INTERPRETATION,
        highest_stage_reached=LatticeStage.DENOTATION,
        admitted=True,
        note=(
            "Admitted 1E-V-SOURCE-B. vedic_denotation_bphs copy-verifies R. "
            "Santhanam's translation of Brihat Parasara Hora Shastra (Ranjan "
            "Publications, 1984, Vol. I) from its title page, dated preface "
            "and pagination -- a digital surrogate (IA scan) -- and doubly "
            "transcribes the seven classical grahas' karakatva from the "
            "defining verse 12-13 ('Planetary Governances', p.11: the Sun is "
            "the soul, the Moon the mind, ... Saturn denotes grief), OCR plus "
            "page-image read. Each graha maps onto the shared ontology "
            "interpretively and blind to Kamea; the seven cover exactly the "
            "set the lagna-lord quantity produces (nodes rule no sign). "
            "Compiles to seven source-specific entries; concordance_eligible "
            "is True. The THIRD denoting system, reached through the Lahiri "
            "ayanamsa it depends on. The legacy knowledge/planets and "
            "vedic_interpreter stay quarantined and untouched."
        ),
    ),
)


# Uncited interpretive modules that must stay out of every 1E path, one entry
# per system. Each maps computed structure straight to meaning with no source,
# so a 1E caller reaching for one would inherit unprovenanced denotation. The
# quarantine is a boundary, not a deletion: other callers keep these.
INTERPRETATION_QUARANTINE: tuple[dict[str, Any], ...] = (
    {
        "system": "numerology",
        "module": "atlas.synthesis.adapters.numerology",
        "symbol": "evidence_from_number",
        "permitted_in_1E": False,
    },
    {
        "system": "gematria",
        "module": "atlas.ciphers",
        "symbol": "hebrew_literal_sequence",
        "permitted_in_1E": False,
    },
    {
        "system": "vedic",
        "module": "atlas.knowledge.planets",
        "symbol": "PLANETS",
        "permitted_in_1E": False,
    },
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
            "Three systems now denote -- Kamea by direct measurement, "
            "numerology through a verified source (1E-N-SOURCE-A, Jordan) and "
            "Vedic through another (1E-V-SOURCE-B, BPHS, on the admitted "
            "Lahiri ayanamsa) -- so a cross-system concordance can run. That "
            "readiness is a statement about the evidence; whether a particular "
            "concordance study has been performed is a separate question."
        ),
    }
