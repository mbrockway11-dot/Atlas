"""The canonical acquisition corpus — one source per phase, tied to its gate.

The bottleneck is no longer finding sources; it is choosing a canonical corpus.
This records that choice as a small, checked plan: for each phase, one work,
the tier it must reach, the claim it must license, and the capability gate it
unlocks. The value of a source here is proportional to the gates it unlocks,
not the pages it contains.

Nothing here is acquired. Every target ships ``NOT_ACQUIRED``; the status
advances only as the acquisition protocol is run against a verified copy. What
this module *does* enforce, source-neutrally, is that the plan is coherent:
each target's required tier can actually license the claim its gate needs, so
the corpus cannot name a source that -- even once acquired -- could not
license what it is meant to.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from atlas.validation.denotation.source_tiers import (
    ClaimType,
    SourceTier,
    can_license,
    tier_of,
)


ACQUISITION_SCHEMA = "atlas.validation.denotation.acquisition-targets.v1"


class AcquisitionStatus(str, Enum):
    """How far a target has moved along the protocol.

    The states the acquisition protocol advances through. All targets start
    at ``NOT_ACQUIRED``; each later state is reached only by completing the
    corresponding protocol stages against a real copy.
    """

    NOT_ACQUIRED = "not_acquired"
    LOCATED = "located"              # found via a repository/catalog
    COPY_VERIFIED = "copy_verified"  # title/copyright/pagination checked
    ADMITTED = "admitted"            # compiled and passed the capability gate


@dataclass(frozen=True, slots=True)
class AcquisitionTarget:
    """One canonical acquisition, with the gate it unlocks."""

    target_id: str
    phase: int
    system: str
    layer: str
    work_id: str
    required_tier: SourceTier
    licenses_claim: ClaimType
    unlocks: str
    located_via: str
    verified_via: str
    status: AcquisitionStatus = AcquisitionStatus.NOT_ACQUIRED

    @property
    def plan_is_coherent(self) -> bool:
        """Return whether the required tier can license the needed claim.

        A source-neutral consistency check on the plan itself: a target whose
        tier could not license its claim, even once acquired, is a planning
        error to catch now rather than after a copy is in hand.
        """
        return can_license(self.required_tier, self.licenses_claim)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "target_id": self.target_id,
            "phase": self.phase,
            "system": self.system,
            "layer": self.layer,
            "work_id": self.work_id,
            "work_tier": tier_of(self.work_id).value,
            "required_tier": self.required_tier.value,
            "licenses_claim": self.licenses_claim.value,
            "unlocks": self.unlocks,
            "located_via": self.located_via,
            "verified_via": self.verified_via,
            "status": self.status.value,
            "plan_is_coherent": self.plan_is_coherent,
        }


# The corpus. Three works, one per phase, in dependency order. Deliberately
# narrow: collecting several traditions at once is what turned earlier
# acquisition thinking into an architecture exercise.
CANONICAL_ACQUISITION_CORPUS: tuple[AcquisitionTarget, ...] = (
    AcquisitionTarget(
        target_id="gematria-value-method",
        phase=1,
        system="gematria",
        layer="letter_value_assignment",
        work_id="pardes_rimmonim",
        required_tier=SourceTier.PRIMARY_TRADITIONAL,
        licenses_claim=ClaimType.METHOD,
        unlocks=(
            "value_method_available -> numeric_evaluation_available; the "
            "first non-Kamea move from licensed identity into licensed "
            "traditional computation"
        ),
        located_via="sefaria",
        verified_via="worldcat",
    ),
    AcquisitionTarget(
        target_id="numerology-denotation",
        phase=2,
        system="numerology",
        layer="denotation",
        work_id="juno_jordan_romance_in_your_name",
        required_tier=SourceTier.PRIMARY_TRADITIONAL,
        licenses_claim=ClaimType.MEANING,
        unlocks=(
            "the first sourced numerology denotations; the first path toward "
            "a second independently denoting system"
        ),
        located_via="internet_archive",
        verified_via="worldcat",
    ),
    AcquisitionTarget(
        target_id="vedic-ayanamsa-authority",
        phase=3,
        system="vedic",
        layer="ayanamsa_framework",
        work_id="vedic_ayanamsa_authority_pending",
        required_tier=SourceTier.PRIMARY_TRADITIONAL,
        licenses_claim=ClaimType.RULE,
        unlocks=(
            "ayanamsa admitted -> sidereal quantities become licensed; the "
            "upstream gate that unblocks every downstream Vedic layer "
            "(1E-V-SOURCE-A). House-system authority follows in the same "
            "phase."
        ),
        located_via="gretil",
        verified_via="worldcat",
    ),
)


def acquisition_report() -> dict[str, Any]:
    """Return the acquisition plan, coherence-checked."""
    targets = [target.to_dict() for target in CANONICAL_ACQUISITION_CORPUS]

    return {
        "schema": ACQUISITION_SCHEMA,
        "targets": targets,
        "all_coherent": all(
            target.plan_is_coherent for target in CANONICAL_ACQUISITION_CORPUS
        ),
        "admitted": [
            t["target_id"]
            for t in targets
            if t["status"] == AcquisitionStatus.ADMITTED.value
        ],
        "note": (
            "One source per phase, in dependency order. Every target is "
            "NOT_ACQUIRED: this is a plan, not evidence. A target advances "
            "only by running the acquisition protocol against a verified "
            "copy. The manifest recording edition metadata, page ranges, "
            "hashes and provenance is populated at that point, not now."
        ),
    }
