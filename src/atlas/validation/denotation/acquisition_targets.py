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
    # Set when an integration test against the real source revises the plan.
    finding: str = ""

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
            "finding": self.finding,
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
        # Re-scoped by the P1 integration test. Left visible rather than
        # silently repointed, with the finding attached.
        work_id="hebrew_alphabetic_numeral_system_pending",
        required_tier=SourceTier.NORMATIVE_STANDARD,
        licenses_claim=ClaimType.COMPUTATION,
        unlocks=(
            "value_method_available -> numeric_evaluation_available; the "
            "first non-Kamea move from licensed identity into licensed "
            "traditional computation"
        ),
        located_via="worldcat",
        verified_via="worldcat",
        finding=(
            "Reclassified by the P1 integration test. Pardes Rimmonim has no "
            "Gate of Gematria (Sefaria index: 32 gates), and no DEFINING "
            "primary passage was identified -- the inspected scholarly "
            "reference presupposes the Hebrew alphabetic numeral system "
            "rather than establishing it (not a claim of universal "
            "nonexistence). So the value table is a normative computation "
            "claim, sourced by a Hebrew numeral-system authority that is "
            "DISTINCT from Unicode: Unicode licenses identity/normalization "
            "and explicitly omits Hebrew numeric values as out of scope. "
            "Admission stays closed until a source covers "
            "MANDATORY_NUMERAL_REQUIREMENTS (see 1E-G-P1-NORMATIVE-SOURCE-"
            "EVALUATION). Pardes Rimmonim retained for equivalence/denotation "
            "research (1E-G-SOURCE-B/-C), not P1 computation. "
            "UPDATE 2026-07-27 (docs/GEMATRIA_P1_CLDR_INSPECTION.md): the value "
            "table SPLITS by tier. The base 22-letter map + additive above-400 "
            "is normative and now ADMITTED as a VALUE ASSIGNMENT "
            "(standard-hebrew-values-cldr, Unicode CLDR release-46, verified "
            "copy). The final-form READING value is provably primary_traditional "
            "(writing standards run integer->letters, never meeting a sofit). "
            "This target (the value METHOD) stays NOT_ACQUIRED: the method needs "
            "the finals. Eleazar of Worms (eleazar_of_worms_gematria, "
            "primary_traditional) is LOCATED as the finals candidate, but his "
            "works USE the values without a DEFINING passage, so admission "
            "awaits an offline verified edition."
        ),
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
        status=AcquisitionStatus.ADMITTED,
        finding=(
            "ADMITTED 2026-07-27 (1E-N-SOURCE-A, numerology_corpus_v2). Unlike "
            "the gematria value method, Jordan DEFINES rather than "
            "presupposes: the 'Significance and Meaning of Numbers' chapter "
            "states each number's denotation outright ('Number One is the "
            "number of action', watchword Courage; ... Nine, Forgiveness). "
            "COPY VERIFIED from the copy's own page images (a digital "
            "surrogate, the Internet Archive scan, recorded as such): title "
            "page (leaf n4), copyright page (leaf n5: ISBN 0875162274, DeVorss "
            "Eleventh Printing 2003, (c)1965 J.F. Rowny Press), and pagination "
            "(scan->printed map) -- resolving the edition/pagination "
            "discrepancy v1 flagged, and corroborated by OpenLibrary (ISBN "
            "0875162274, DeVorss, work OL6095808W, 297pp). Repository file "
            "hash locked (jp2.zip sha1 62fa426f...). The nine denotations were "
            "DOUBLY TRANSCRIBED (repository OCR + a page-image read, resolved "
            "against the image where the OCR erred), keyed quantity-"
            "independent (the value itself), construct-equivalent to the "
            "code's Pythagorean reduction, and mapped onto the shared ontology "
            "interpretively and blind to Kamea. Compiles to nine source-"
            "specific denotations; numerology_capabilities.concordance_"
            "eligible is True; admission.py flips numerology/denotation to "
            "DENOTATION+admitted, so concordance_ready() is now True -- the "
            "second denoting system 1E-A needed. The letter-VALUE chart Jordan "
            "credits upstream to L. Dow Balliett (provenance, not a "
            "disqualifier). Refines the repository rule: access alone is still "
            "not verification, but the completed title/copyright/pagination "
            "checks plus hash and independent catalog corroboration are."
        ),
    ),
    AcquisitionTarget(
        target_id="vedic-ayanamsa-authority",
        phase=3,
        system="vedic",
        layer="ayanamsa_framework",
        work_id="calendar_reform_committee_report",
        # Reclassified by the real source, like gematria's P1 target. The
        # placeholder guessed primary_traditional/RULE; the actual authority is
        # a Government of India standards body defining a computational
        # constant, so it is normative and licenses a COMPUTATION.
        required_tier=SourceTier.NORMATIVE_STANDARD,
        licenses_claim=ClaimType.COMPUTATION,
        unlocks=(
            "ayanamsa admitted -> sidereal quantities become licensed; the "
            "upstream gate that unblocks every downstream Vedic layer "
            "(1E-V-SOURCE-A). House-system authority follows in the same "
            "phase."
        ),
        located_via="internet_archive",
        verified_via="internet_archive",
        status=AcquisitionStatus.ADMITTED,
        finding=(
            "ADMITTED 2026-07-27 (1E-V-SOURCE-A). The ayanamsa authority is a "
            "governmental NORMATIVE standard, not a traditional RULE text -- a "
            "real-source reclassification of the placeholder. Source: Report "
            "of the Calendar Reform Committee, Government of India (CSIR, New "
            "Delhi, 1955). The committee's OWN recommendation (p.7, "
            "'Recommendations for Religious Calendar', items 5 and 7 -- "
            "distinguished from correspondents' letters elsewhere in the "
            "report) adopts a variable ayanamsa of 23 deg 15' 0\" at 21 Mar "
            "1956, precessing ~50\".27/yr, zero-point 180 deg from Spica "
            "(Chitra-paksa); N.C. Lahiri was the committee's Secretary. "
            "COPY VERIFIED against the page image (IA "
            "calendar_reform_comittee_report leaf n18, printed p.7) and OCR; "
            "citeable edition IA dli.ministry.19933 (CSIR 1955). Construct "
            "equivalence: Swiss Ephemeris SIDM_LAHIRI implements this official "
            "ayanamsa. Admitted in vedic_ayanamsa.py (LAHIRI.admitted=True, "
            "hash + locator); admission.py ayanamsa_framework -> "
            "SOURCE_VERIFICATION + admitted. This licenses the sidereal OFFSET "
            "(computation), unblocking sidereal quantities that name the "
            "Lahiri choice; it does NOT make Vedic denote -- denotation needs "
            "a separate Jyotisha source and a scaffold not yet built."
        ),
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
