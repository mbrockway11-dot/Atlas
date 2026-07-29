"""Does the natal <-> name-kamea overlay carry real signal, or is it null?

The overlay (atlas.overlay.natal_kamea_overlay) computes, per shared classical
planet, alignment = natal_z * kamea_z -- positive when a person's natal dignity
and their name's kamea activity are elevated (or suppressed) together. This
tests the only thing that matters: does the corpus's mean alignment exceed a
null where natal charts are randomly reassigned across profiles (breaking the
name<->birth-date pairing while preserving each distribution)?

This directly extends the existing null result (name-kamea vs birth-Vedic,
Mantel r=+0.007 p=0.11, n=1885): that test used the lagna-lord karakatva; this
uses natal dignity across all seven classical bodies against the population-
relative kamea activity. Different metric, same question. Pre-registered here,
before running: H1 is mean_alignment > 0 beyond the shuffled null; the metric
and test are fixed and reported as null if that is the result.

    .venv/Scripts/python.exe scripts/natal_kamea_overlay_test.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import date

from atlas.overlay.natal_kamea_overlay import build_natal_kamea_overlay
from atlas.temporal.dignity import build_dignity_chart, dignity_chart_to_dict
from atlas.temporal.models import BirthData
from atlas.temporal.natal_chart import build_natal_chart_payload

PROFILES = "output/library/profiles"
SEED = 20260729
PERMUTATIONS = 2000


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except (ValueError, TypeError):
        return None


def build_subjects(limit: int | None):
    """Return [(name, birth_date, ranked_kameas)] for profiles with both."""
    subjects = []
    for key in sorted(os.listdir(PROFILES)):
        if limit is not None and len(subjects) >= limit:
            break
        acf_path = f"{PROFILES}/{key}/profile.acf.json"
        intake_path = f"{PROFILES}/{key}/profile.intake.json"
        if not (os.path.exists(acf_path) and os.path.exists(intake_path)):
            continue
        try:
            intake = json.load(open(intake_path, encoding="utf-8"))
            d = _parse_date(intake.get("birth_date", ""))
            if d is None:
                continue
            acf = json.load(open(acf_path, encoding="utf-8"))
            ranked = acf["invariant_analysis"]["ranked_kameas"]
        except (ValueError, OSError, KeyError):
            continue
        subjects.append((key, d, ranked))
    return subjects


def natal_dignities(d: date) -> dict:
    bd = BirthData(
        name="x", birth_date=d.isoformat(), birth_time="", birth_place="",
        latitude=42.0, longitude=-89.0, timezone="UTC", time_known=False,
    )
    chart = build_natal_chart_payload(bd)
    return dignity_chart_to_dict(build_dignity_chart(chart["natal_chart"]))["dignities"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    subjects = build_subjects(args.limit)
    print(f"subjects with birth_date + kamea: {len(subjects)}")

    dignity_cache: dict[date, dict] = {}
    alignments = []
    for _, d, ranked in subjects:
        if d not in dignity_cache:
            dignity_cache[d] = natal_dignities(d)
        overlay = build_natal_kamea_overlay(dignity_cache[d], ranked)
        if overlay["planets_compared"] == 7:
            alignments.append(overlay["mean_alignment"])

    n = len(alignments)
    observed = sum(alignments) / n
    print(f"comparable subjects (7/7 planets): {n}")
    print(f"observed mean alignment: {observed:+.4f}")

    # Null: shuffle which subject's birth-date-dignity attaches to which
    # subject's kamea ranking, breaking the name<->birth pairing while keeping
    # each side's own distribution intact.
    kamea_lists = [ranked for _, d, ranked in subjects]
    dignity_list = [dignity_cache[d] for _, d, _ in subjects]

    rng = random.Random(SEED)
    null_means = []
    for _ in range(PERMUTATIONS):
        shuffled = dignity_list[:]
        rng.shuffle(shuffled)
        vals = []
        for dign, ranked in zip(shuffled, kamea_lists):
            overlay = build_natal_kamea_overlay(dign, ranked)
            if overlay["planets_compared"] == 7:
                vals.append(overlay["mean_alignment"])
        if vals:
            null_means.append(sum(vals) / len(vals))

    null_mean = sum(null_means) / len(null_means)
    null_sd = (sum((x - null_mean) ** 2 for x in null_means) / len(null_means)) ** 0.5
    p_value = sum(1 for x in null_means if x >= observed) / len(null_means)

    print(f"\nnull (shuffled pairing, {PERMUTATIONS} perms): mean {null_mean:+.4f}  sd {null_sd:.4f}")
    print(f"one-tailed p (null >= observed): {p_value:.4f}")
    print(f"\nVERDICT: {'REJECT H0 -- real signal' if p_value < 0.05 else 'FAIL TO REJECT H0 -- null'}")


if __name__ == "__main__":
    main()
