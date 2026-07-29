"""Historical validation on the Gauquelin registry-timed cohort.

The accrued profiles have no birth times, so the previous run could only use the
Moon-sign lord. The Gauquelin datasets (tig12/g5, from French birth registries)
carry exact birth *times* and coordinates for thousands of eminent
professionals -- the classic scientific astrology corpus. With a time, the
sidereal ascendant is computable, so this runs the stronger natal test: the
full lagna lord's karakatva against numerology, null-controlled.

Data: LERRCP A1 (athletes), A2 (physicians/others) and related files from
https://github.com/tig12/g5 -- registry-sourced, public research data. Birth
times are stored in UTC; the sidereal chart uses the admitted Lahiri ayanamsa.

This tests a real, falsifiable question -- do a person's numerology and their
Vedic lagna lord agree about them more than chance? -- and reports the answer
the null controls give, positive or negative.

Usage: .venv/Scripts/python.exe scripts/run_gauquelin_validation.py [--limit N]
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import urllib.request
from datetime import date, datetime

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


RAW = "https://raw.githubusercontent.com/tig12/g5/main/data/db/init/lerrcp-marked"
FILES = {"A1": f"{RAW}/A1.csv", "A2": f"{RAW}/A2.csv"}
CACHE = (
    "C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
    "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad"
)


def _load(name: str, url: str) -> list[dict]:
    path = f"{CACHE}/gauq_{name}.csv"
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sidereal_ascendant_sign(dt: datetime, lat: float, lon: float) -> int:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60 + dt.second / 3600,
    )
    ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)[1]
    return int(ascmc[0] % 360 // 30) + 1


def _numerology_claims(name: str, d: date, sid: str):
    dictionary, _ = numerology_dictionary()
    return [
        c
        for e in build_expressions(name, d).values()
        if (c := numerology_claim(e, dictionary, sid)) is not None
    ]


def _vedic_lagna_claim(sign: int, sid: str):
    entry = vedic_dictionary().lookup(SIGN_RULERS[sign])
    if entry is None:
        return None
    return DenotationClaim(
        system="vedic", subject_id=sid, axis=entry.axis, value=entry.coordinate,
        polarity=entry.polarity, temporal_scope="natal",
        mapping_kind=entry.mapping_kind, confidence=entry.confidence,
        source_basis=(
            f"{entry.tradition}:{entry.source_passage_id}:"
            f"lagna_lord={SIGN_RULERS[sign]}"
        ),
    )


def build_subjects(limit: int | None):
    subjects = []
    occus: dict[str, int] = {}
    read = 0
    for name, url in FILES.items():
        for row in _load(name, url):
            if limit is not None and read >= limit:
                break
            try:
                dt = datetime.fromisoformat(row["DATE"])
                lat = float(row["LAT"])
                lon = float(row["LON"])
            except (ValueError, KeyError, TypeError):
                continue
            person = row.get("NAME", "").strip()
            if not person:
                continue
            read += 1
            sid = f"{name}-{row.get('NUM','?')}"
            occus[row.get("OCCU", "?")] = occus.get(row.get("OCCU", "?"), 0) + 1

            numerology = _numerology_claims(person, dt.date(), sid)
            if not numerology:
                continue
            claims = {"numerology": numerology}
            vedic = _vedic_lagna_claim(
                _sidereal_ascendant_sign(dt, lat, lon), sid
            )
            if vedic is not None:
                claims["vedic"] = [vedic]
            subjects.append(assemble_subject(sid, claims))
    return subjects, occus, read


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    subjects, occus, read = build_subjects(args.limit)
    print("=== Gauquelin cohort (registry-timed) ===")
    print(f"  records read: {read}")
    print(f"  occupations : {dict(sorted(occus.items(), key=lambda x:-x[1]))}")
    print(f"  subjects    : {len(subjects)}")

    gap = measure_agreement_gap(
        subjects,
        {
            "shuffled_systems": lambda: shuffled_systems(subjects, seed=args.seed),
            "decoy_labels": lambda: decoy_labels(subjects, seed=args.seed),
            "mismatched_pairs": lambda: mismatched_pairs(subjects, seed=args.seed),
        },
    )
    a = gap.authentic
    print("\n=== numerology vs Vedic lagna lord (full natal, real ascendant) ===")
    print(f"  comparable pairs : {a.comparable_pairs}")
    print(f"  agreeing pairs   : {a.agreeing_pairs}")
    print(f"  agreement rate   : {a.agreement_rate:.4f}")
    print("\n=== authentic minus each null control ===")
    for name, g in gap.gaps.items():
        print(f"  {name:18} gap {g:+.4f}")
    print(f"\n  EXCEEDS EVERY CONTROL: {gap.exceeds_every_control}")


if __name__ == "__main__":
    main()
