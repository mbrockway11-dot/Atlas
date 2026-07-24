"""Cross-system concordance, with the authentic-vs-control agreement gap.

The primary 1E-A result is not a concordance rate. It is the *gap* between the
rate on authentic subjects and the rate on controls. A broad vocabulary makes
almost any two systems look mutually confirming, so a raw agreement rate is
uninterpretable on its own -- only its excess over shuffled, mismatched and
decoy pairings means anything.

Concordance is scored pairwise between systems, axis by axis, and only over
comparable claims. Pairs that are ``not_comparable`` are excluded from the
denominator rather than counted as disagreement, because a reference mismatch
is an absence of comparison, not a failure of one.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Sequence

import numpy as np

from atlas.validation.denotation.expressions import SubjectDenotation
from atlas.validation.denotation.ontology import ontology_hash
from atlas.validation.denotation.relations import (
    Relation,
    RelationVerdict,
    relate,
)


CONCORDANCE_SCHEMA = "atlas.validation.denotation.concordance.v1"


@dataclass(frozen=True, slots=True)
class ConcordanceResult:
    """Concordance for one set of subjects."""

    subjects: int
    comparable_pairs: int
    agreeing_pairs: int
    contradictory_pairs: int
    relation_counts: dict[str, int]

    @property
    def agreement_rate(self) -> float:
        """Return agreement as a share of comparable pairs."""
        if self.comparable_pairs == 0:
            return float("nan")

        return self.agreeing_pairs / self.comparable_pairs

    @property
    def contradiction_rate(self) -> float:
        """Return contradiction as a share of comparable pairs."""
        if self.comparable_pairs == 0:
            return float("nan")

        return self.contradictory_pairs / self.comparable_pairs

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "subjects": self.subjects,
            "comparable_pairs": self.comparable_pairs,
            "agreeing_pairs": self.agreeing_pairs,
            "contradictory_pairs": self.contradictory_pairs,
            "agreement_rate": self.agreement_rate,
            "contradiction_rate": self.contradiction_rate,
            "relation_counts": self.relation_counts,
        }


def subject_verdicts(subject: SubjectDenotation) -> list[RelationVerdict]:
    """Return every cross-system claim comparison for one subject.

    Within-system pairs are never compared: a system agreeing with itself is
    not evidence of anything. Only distinct-system, same-axis pairs are
    related.
    """
    verdicts: list[RelationVerdict] = []
    systems = subject.systems_present()

    for axis in _axes_present(subject):
        by_system = {
            system: [
                claim
                for claim in subject.claims_by_system.get(system, ())
                if claim.axis == axis
            ]
            for system in systems
        }

        for left_system, right_system in combinations(systems, 2):
            for left in by_system[left_system]:
                for right in by_system[right_system]:
                    verdicts.append(relate(left, right))

    return verdicts


def score_concordance(
    subjects: Sequence[SubjectDenotation],
) -> ConcordanceResult:
    """Score concordance across a set of subjects."""
    relation_counts: dict[str, int] = {r.value: 0 for r in Relation}
    comparable = 0
    agreeing = 0
    contradictory = 0

    for subject in subjects:
        for verdict in subject_verdicts(subject):
            relation_counts[verdict.relation.value] += 1

            if not verdict.comparable:
                continue

            comparable += 1

            if verdict.agrees:
                agreeing += 1
            elif verdict.relation is Relation.CONTRADICTORY:
                contradictory += 1

    return ConcordanceResult(
        subjects=len(subjects),
        comparable_pairs=comparable,
        agreeing_pairs=agreeing,
        contradictory_pairs=contradictory,
        relation_counts=relation_counts,
    )


@dataclass(frozen=True, slots=True)
class AgreementGap:
    """The authentic-vs-control agreement gap -- the primary 1E-A result."""

    ontology_hash: str
    authentic: ConcordanceResult
    controls: dict[str, ConcordanceResult]

    @property
    def gaps(self) -> dict[str, float]:
        """Return authentic minus each control's agreement rate."""
        return {
            name: self.authentic.agreement_rate - result.agreement_rate
            for name, result in self.controls.items()
        }

    @property
    def exceeds_every_control(self) -> bool:
        """Return whether authentic agreement beats every control.

        The bar for any symbolic claim to survive. If authentic pairings do
        not agree more than shuffled and mismatched ones, the concordance is
        an artifact of vocabulary breadth and nothing denotational has been
        shown.
        """
        return all(gap > 0 for gap in self.gaps.values())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": CONCORDANCE_SCHEMA,
            "ontology_hash": self.ontology_hash,
            "authentic": self.authentic.to_dict(),
            "controls": {
                name: result.to_dict()
                for name, result in self.controls.items()
            },
            "gaps": self.gaps,
            "exceeds_every_control": self.exceeds_every_control,
            "interpretation": (
                "The agreement rate alone is uninterpretable: a broad "
                "vocabulary makes almost any pairing look confirming. Only "
                "the excess over shuffled and mismatched controls is "
                "evidence of denotational concordance."
            ),
        }


def measure_agreement_gap(
    authentic: Sequence[SubjectDenotation],
    control_builders: dict[str, Callable[[], Sequence[SubjectDenotation]]],
) -> AgreementGap:
    """Score authentic subjects against every control family.

    Controls are passed as builders rather than as data so that a shuffling
    or mismatching generator runs at scoring time and cannot be confused with
    the authentic set.
    """
    return AgreementGap(
        ontology_hash=ontology_hash(),
        authentic=score_concordance(authentic),
        controls={
            name: score_concordance(list(build()))
            for name, build in control_builders.items()
        },
    )


def _axes_present(subject: SubjectDenotation) -> set[str]:
    """Return the axes any system made a claim on."""
    return {
        claim.axis
        for claims in subject.claims_by_system.values()
        for claim in claims
    }
