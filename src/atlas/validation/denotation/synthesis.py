"""Cross-system synthesis -- run the admitted denoting systems in conjunction.

The wiring built each denoting system a canonical dictionary; this runs them
together. For one subject it pulls every admitted system's claims from its
canonical binding, assembles them into a single ``SubjectDenotation``, and --
over a set of subjects -- scores the concordance against the null controls. The
gap between authentic agreement and shuffled/mismatched agreement is the primary
1E-A result: agreement that does not beat the controls is vocabulary breadth,
not denotation.

The three systems do not all meet on one axis or scope, and the runner does not
force them to. Their reference scopes are what each system honestly supplies:

* **numerology** -- natal claims (name and birth date), on domain / dynamic /
  behavioral axes.
* **Vedic** -- both natal (the lagna lord's karakatva) and transit (each
  transiting graha's karakatva with its sourced gochara polarity). Vedic is the
  bridge: its natal claims meet numerology, its transit claims meet Kamea.
* **Kamea** -- transit claims on the dynamic axis only (a trajectory is an
  instant's structure), polarity neutral.

The concordance layer compares only same-scope, same-axis pairs, so numerology
meets Vedic-natal and Kamea meets Vedic-transit, while numerology and Kamea --
natal against transit -- are correctly never compared. The runner assembles the
whole picture; the scorer decides what is comparable.

This module generates no meanings. Every claim comes from a canonical
dictionary that a verified source licensed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, Mapping, Sequence

from atlas.validation.denotation.concordance import (
    AgreementGap,
    measure_agreement_gap,
)
from atlas.validation.denotation.controls import (
    decoy_labels,
    mismatched_pairs,
    shuffled_systems,
)
from atlas.validation.denotation.expressions import (
    DenotationClaim,
    SubjectDenotation,
    SystemExpression,
    assemble_subject,
)
from atlas.validation.denotation.kamea_denotation import kamea_dynamic_claims
from atlas.validation.denotation.numerology_canonical import (
    canonical_dictionary as _numerology_dictionary,
)
from atlas.validation.denotation.numerology_dictionary import (
    claim_from_expression as _numerology_claim,
)
from atlas.validation.denotation.numerology_expression import build_expressions
from atlas.validation.denotation.vedic_denotation import (
    claim_from_expression as _vedic_claim,
)
from atlas.validation.denotation.vedic_denotation_bphs import (
    canonical_dictionary as _vedic_dictionary,
)
from atlas.validation.denotation.vedic_grahas import (
    LAGNA_LORD,
    SIGN_RULERS,
    VedicExpression,
)
from atlas.validation.denotation.vedic_transits import transit_claims


@dataclass(frozen=True, slots=True)
class SynthesisSubject:
    """One subject's inputs for every system that can speak about it.

    Each system consumes what it honestly needs; a field left ``None`` means
    that system simply does not contribute, which is silence, not a default.
    Vedic's sidereal inputs (ascendant sign, transit signs) are computed
    upstream under the admitted Lahiri ayanamsa; the Kamea expression is the
    frozen structural output of a birth-moment trajectory.
    """

    subject_id: str
    name: str
    birth_date: date
    natal_ascendant_sign: int | None = None
    natal_moon_sign: int | None = None
    graha_transit_signs: Mapping[str, int] | None = None
    transit_when: str | None = None
    kamea_expression: SystemExpression | None = None


def _refiled(
    claims: Sequence[DenotationClaim], subject_id: str
) -> list[DenotationClaim]:
    """Re-file claims under the subject id assembly will expect."""
    return [replace(claim, subject_id=subject_id) for claim in claims]


def subject_claims(
    subject: SynthesisSubject,
) -> dict[str, list[DenotationClaim]]:
    """Return each system's claims for a subject, from its canonical binding."""
    claims: dict[str, list[DenotationClaim]] = {}

    # Numerology -- natal, from the canonical Jordan dictionary.
    numerology_dictionary, _ = _numerology_dictionary()
    numerology = [
        claim
        for expression in build_expressions(
            subject.name, subject.birth_date
        ).values()
        if (
            claim := _numerology_claim(
                expression, numerology_dictionary, subject.subject_id
            )
        )
        is not None
    ]
    if numerology:
        claims["numerology"] = numerology

    # Vedic -- natal lagna lord, plus transits, from the canonical BPHS
    # dictionary and the sourced gochara polarity.
    vedic_dictionary = _vedic_dictionary()
    vedic: list[DenotationClaim] = []

    if subject.natal_ascendant_sign is not None:
        expression = VedicExpression(
            quantity=LAGNA_LORD,
            graha=SIGN_RULERS[subject.natal_ascendant_sign],
            ascendant_sign=subject.natal_ascendant_sign,
            ayanamsa_scheme="lahiri",
        )
        claim = _vedic_claim(expression, vedic_dictionary, subject.subject_id)
        if claim is not None:
            vedic.append(claim)

    if (
        subject.graha_transit_signs is not None
        and subject.natal_moon_sign is not None
        and subject.transit_when
    ):
        vedic.extend(
            transit_claims(
                subject.graha_transit_signs,
                subject.natal_moon_sign,
                vedic_dictionary,
                subject.subject_id,
                when=subject.transit_when,
            )
        )

    if vedic:
        claims["vedic"] = vedic

    # Kamea -- transit, dynamic axis, from the frozen structural expression.
    if subject.kamea_expression is not None:
        kamea = _refiled(
            kamea_dynamic_claims(subject.kamea_expression),
            subject.subject_id,
        )
        if kamea:
            claims["kamea"] = kamea

    return claims


def synthesize(subject: SynthesisSubject) -> SubjectDenotation:
    """Assemble one subject's claims from every contributing system."""
    return assemble_subject(subject.subject_id, subject_claims(subject))


def run_synthesis(
    subjects: Sequence[SynthesisSubject], *, seed: int = 0
) -> AgreementGap:
    """Score cross-system concordance against the null controls.

    The controls are built at scoring time from the authentic subjects, so a
    shuffling or mismatching generator cannot be confused with the real set.
    ``exceeds_every_control`` on the result is the bar any denotational claim
    must clear.
    """
    authentic = [synthesize(subject) for subject in subjects]

    return measure_agreement_gap(
        authentic,
        {
            "shuffled_systems": lambda: shuffled_systems(authentic, seed=seed),
            "decoy_labels": lambda: decoy_labels(authentic, seed=seed),
            "mismatched_pairs": lambda: mismatched_pairs(
                authentic, seed=seed
            ),
        },
    )


def synthesis_report(
    subjects: Sequence[SynthesisSubject], *, seed: int = 0
) -> dict[str, Any]:
    """Return a JSON-safe synthesis result over a subject set."""
    gap = run_synthesis(subjects, seed=seed)

    return {
        "subjects": len(subjects),
        "systems_available": ["kamea", "numerology", "vedic"],
        "agreement_gap": gap.to_dict(),
        "note": (
            "Only same-scope, same-axis cross-system pairs are comparable: "
            "numerology meets Vedic-natal, Kamea meets Vedic-transit. The "
            "result is meaningful only as the excess over the null controls; "
            "a small or synthetic subject set does not establish denotation."
        ),
    }
