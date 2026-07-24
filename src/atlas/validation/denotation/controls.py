"""Null and contradiction controls for the concordance audit.

Agreement must not be inevitable. A shared vocabulary of broad words --
"change", "power", "transformation" -- can make nearly every system appear to
confirm every other, so the audit is only meaningful against a floor that
destroys any genuine cross-system correspondence while preserving each
system's own output distribution.

Every generator here breaks the *pairing* between systems without altering
what any single system said. That is the point: if authentic subjects agree no
more than subjects whose systems were shuffled together at random, the
agreement was never about the subject.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence

import numpy as np

from atlas.validation.denotation.expressions import (
    DenotationClaim,
    SubjectDenotation,
    assemble_subject,
)
from atlas.validation.denotation.ontology import AXES


def shuffled_systems(
    subjects: Sequence[SubjectDenotation], *, seed: int
) -> list[SubjectDenotation]:
    """Recombine systems across subjects, breaking authentic pairings.

    Each system's claim block is kept intact but reassigned to a different
    subject, so every system's own distribution is preserved exactly while no
    subject's systems belong together. Agreement here is agreement by
    vocabulary alone.
    """
    rng = np.random.default_rng(seed)
    systems = sorted(
        {system for s in subjects for system in s.systems_present()}
    )

    permutations = {
        system: rng.permutation(len(subjects)) for system in systems
    }

    rebuilt: list[SubjectDenotation] = []

    for index, subject in enumerate(subjects):
        claims_by_system: dict[str, list[DenotationClaim]] = {}

        for system in systems:
            source = subjects[int(permutations[system][index])]
            donated = source.claims_by_system.get(system, ())

            # Re-file the donated claims under this subject's id so assembly
            # accepts them; the content -- and therefore the denotation -- is
            # unchanged.
            claims_by_system[system] = [
                replace(claim, subject_id=subject.subject_id)
                for claim in donated
            ]

        rebuilt.append(
            assemble_subject(subject.subject_id, claims_by_system)
        )

    return rebuilt


def decoy_labels(
    subjects: Sequence[SubjectDenotation], *, seed: int
) -> list[SubjectDenotation]:
    """Replace every claim's value with a random one on the same axis.

    Preserves axis occupancy and polarity but severs the value from what the
    system measured. If authentic agreement does not exceed this, the
    concordance is carried by axis coverage rather than by denotation.
    """
    rng = np.random.default_rng(seed)

    rebuilt: list[SubjectDenotation] = []

    for subject in subjects:
        claims_by_system: dict[str, list[DenotationClaim]] = {}

        for system, claims in subject.claims_by_system.items():
            rebuilt_claims: list[DenotationClaim] = []

            for claim in claims:
                choices = AXES[claim.axis]
                value = choices[int(rng.integers(0, len(choices)))]
                rebuilt_claims.append(replace(claim, value=value))

            claims_by_system[system] = rebuilt_claims

        rebuilt.append(
            assemble_subject(subject.subject_id, claims_by_system)
        )

    return rebuilt


def mismatched_pairs(
    subjects: Sequence[SubjectDenotation], *, seed: int
) -> list[SubjectDenotation]:
    """Pair each subject's first system with a different subject's rest.

    A coarser break than :func:`shuffled_systems`: it keeps one system's block
    authentic and mismatches the remainder, modelling a cohort where names and
    birth records were joined to the wrong person. Included because real data
    errors take this shape more often than a full shuffle.
    """
    rng = np.random.default_rng(seed)

    if len(subjects) < 2:
        return list(subjects)

    donors = rng.permutation(len(subjects))

    rebuilt: list[SubjectDenotation] = []

    for index, subject in enumerate(subjects):
        donor_index = int(donors[index])

        if donor_index == index:
            donor_index = (donor_index + 1) % len(subjects)

        donor = subjects[donor_index]
        systems = subject.systems_present()

        claims_by_system: dict[str, list[DenotationClaim]] = {}

        for position, system in enumerate(systems):
            source = subject if position == 0 else donor
            claims_by_system[system] = [
                replace(claim, subject_id=subject.subject_id)
                for claim in source.claims_by_system.get(system, ())
            ]

        rebuilt.append(
            assemble_subject(subject.subject_id, claims_by_system)
        )

    return rebuilt
