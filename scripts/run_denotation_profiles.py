"""Run the cross-system denotation concordance over the accrued profiles.

The accrued profiles carry name + birth date but almost never a birth time
(3,624 profiles, 12 with a time), so the Vedic lagna lord -- which needs the
ascendant -- is uncomputable. This run uses the classical fallback Vedic
astrology itself uses when the time is unknown: the **Moon sign (Chandra
lagna)**, computed from the date, whose ruling graha's karakatva is a natal
Vedic claim. Numerology contributes its natal claims from name + date. Both are
natal, so they are comparable.

The scored result is the authentic-vs-control agreement gap. It is reported
with its caveats, not as a conclusion:

* No birth times -> Vedic is the Moon-sign lord, not the lagna lord.
* The Moon sign is taken at noon UT; subjects whose Moon is within 7 deg of a
  sign boundary that day are flagged and Vedic is withheld for them.
* Numerology's *date-derived* quantities (life path, birthday) share an input
  with the Moon sign, a confound that could inflate the gap; the *name-derived*
  quantities (expression, soul urge, personality) do not.

Usage:  .venv/Scripts/python.exe scripts/run_denotation_profiles.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date

import swisseph as swe

from atlas.validation.denotation.concordance import measure_agreement_gap
from atlas.validation.denotation.controls import (
    decoy_labels,
    mismatched_pairs,
    shuffled_systems,
)
from atlas.validation.denotation.expressions import (
    DenotationClaim,
    assemble_subject,
)
from atlas.validation.denotation.numerology_canonical import (
    canonical_dictionary as numerology_dictionary,
)
from atlas.validation.denotation.numerology_dictionary import (
    claim_from_expression as numerology_claim,
)
from atlas.validation.denotation.numerology_expression import build_expressions
from atlas.validation.denotation.vedic_denotation_bphs import (
    canonical_dictionary as vedic_dictionary,
)
from atlas.validation.denotation.vedic_grahas import SIGN_RULERS


PROFILES = "output/library/profiles"
BOUNDARY_MARGIN_DEG = 7.0


def _sidereal_moon_sign(d: date) -> tuple[int, bool]:
    """Return (sidereal Moon sign 1-12 at noon UT, boundary-uncertain flag)."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    signs = []
    for hour in (0.0, 12.0, 24.0):
        jd = swe.julday(d.year, d.month, d.day, hour)
        lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        signs.append(lon)

    noon = signs[1]
    sign = int(noon % 360 // 30) + 1
    # Uncertain if the sign differs across the day, or noon is near a cusp.
    day_signs = {int(x % 360 // 30) for x in signs}
    near_cusp = min(noon % 30, 30 - (noon % 30)) < BOUNDARY_MARGIN_DEG
    return sign, (len(day_signs) > 1 or near_cusp)


def _numerology_claims(name: str, d: date, subject_id: str):
    dictionary, _ = numerology_dictionary()
    return [
        claim
        for expression in build_expressions(name, d).values()
        if (
            claim := numerology_claim(expression, dictionary, subject_id)
        )
        is not None
    ]


def _vedic_moon_lord_claim(d: date, subject_id: str):
    sign, uncertain = _sidereal_moon_sign(d)
    if uncertain:
        return None

    entry = vedic_dictionary().lookup(SIGN_RULERS[sign])
    if entry is None:
        return None

    return DenotationClaim(
        system="vedic",
        subject_id=subject_id,
        axis=entry.axis,
        value=entry.coordinate,
        polarity=entry.polarity,
        temporal_scope="natal",
        mapping_kind=entry.mapping_kind,
        confidence=entry.confidence,
        source_basis=(
            f"{entry.tradition}:{entry.source_passage_id}:"
            f"moon_sign_lord={SIGN_RULERS[sign]}"
        ),
    )


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip()[:10])
    except (ValueError, AttributeError):
        return None


def build_subjects(limit: int | None):
    subjects = []
    counts = {"read": 0, "numerology_only": 0, "both": 0, "moon_uncertain": 0}

    for key in sorted(os.listdir(PROFILES)):
        if limit is not None and counts["read"] >= limit:
            break
        path = f"{PROFILES}/{key}/profile.intake.json"
        if not os.path.exists(path):
            continue
        try:
            intake = json.load(open(path, encoding="utf-8"))
        except (ValueError, OSError):
            continue

        name = intake.get("name")
        d = _parse_date(str(intake.get("birth_date", "")))
        if not name or d is None:
            continue

        counts["read"] += 1
        sid = key

        numerology = _numerology_claims(name, d, sid)
        if not numerology:
            continue

        vedic = _vedic_moon_lord_claim(d, sid)
        claims = {"numerology": numerology}
        if vedic is not None:
            claims["vedic"] = [vedic]
            counts["both"] += 1
        else:
            counts["numerology_only"] += 1
            _, uncertain = _sidereal_moon_sign(d)
            if uncertain:
                counts["moon_uncertain"] += 1

        subjects.append(assemble_subject(sid, claims))

    return subjects, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    subjects, counts = build_subjects(args.limit)
    print("=== profile intake ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"  assembled subjects: {len(subjects)}")

    # Only subjects with both systems contribute a comparable pair.
    gap = measure_agreement_gap(
        subjects,
        {
            "shuffled_systems": lambda: shuffled_systems(
                subjects, seed=args.seed
            ),
            "decoy_labels": lambda: decoy_labels(subjects, seed=args.seed),
            "mismatched_pairs": lambda: mismatched_pairs(
                subjects, seed=args.seed
            ),
        },
    )

    a = gap.authentic
    print("\n=== authentic concordance (numerology vs Vedic Moon-sign lord) ===")
    print(f"  comparable pairs : {a.comparable_pairs}")
    print(f"  agreeing pairs   : {a.agreeing_pairs}")
    print(f"  contradictory    : {a.contradictory_pairs}")
    print(f"  agreement rate   : {a.agreement_rate:.4f}")
    print("\n=== authentic minus each null control ===")
    for name, g in gap.gaps.items():
        print(f"  {name:18} gap {g:+.4f}")
    print(f"\n  EXCEEDS EVERY CONTROL: {gap.exceeds_every_control}")
    print(
        "\nCaveats: no birth times -> Moon-sign lord (not lagna); date-derived "
        "numerology shares an input with the Moon sign; a positive gap here is "
        "a first data point, not a demonstrated denotation."
    )


if __name__ == "__main__":
    main()
