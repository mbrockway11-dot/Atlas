"""The Gauquelin planetary-sector test on the registry-timed cohort.

The classic, falsifiable astrology claim, tested with a permutation null: does an
eminent-profession cohort over-express a planet in the diurnal "plus zones" --
just after rising and just after culmination -- compared with the same cohort
size drawn at random from the pool?

Plus zones are operationalized as Placidus houses 12 (just risen, above the
eastern horizon) and 9 (just past the Midheaven). House position is a mundane
quantity, independent of the zodiac and the ayanamsa. The null holds each
planet's plus-zone flags fixed and shuffles which subjects belong to the
profession, so the p-value is the fraction of random equal-size cohorts whose
rate meets or beats the authentic one -- the honest test of "more than chance".

Classic hypotheses: sports champions -> Mars; scientists and physicians ->
Saturn; writers -> Moon/Jupiter. Reported for each, positive or negative.

Usage: .venv/Scripts/python.exe scripts/run_gauquelin_sectors.py [--perms N]
"""

from __future__ import annotations

import argparse
import csv
import os
import urllib.request
from datetime import datetime

import numpy as np
import swisseph as swe


RAW = "https://raw.githubusercontent.com/tig12/g5/main/data/db/init/lerrcp-marked"
FILES = {"A1": f"{RAW}/A1.csv", "A2": f"{RAW}/A2.csv"}
CACHE = (
    "C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
    "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad"
)

PLANETS = {
    "Mars": swe.MARS,
    "Saturn": swe.SATURN,
    "Jupiter": swe.JUPITER,
    "Moon": swe.MOON,
    "Venus": swe.VENUS,
}
PLUS_ZONE_HOUSES = {9, 12}

# Occupation codes -> profession category.
SPORT = {
    "CYC", "FOO", "RUG", "BOX", "ATH", "TEN", "BAS", "NAT", "PEL", "SKI",
    "ESC", "HAL", "GYM", "HOC", "EQU", "LUT", "TIR", "BIL", "AVR", "GOL",
    "MAR", "HAN", "GLA", "VOI", "CAN", "VOL",
}
CATEGORY = {**{c: "sports" for c in SPORT}, "SC": "science", "PH": "medicine",
            "AVI": "aviation", "AUT": "writers"}

# Which planet each category is classically predicted to over-express.
HYPOTHESES = [
    ("sports", "Mars"),
    ("aviation", "Mars"),
    ("science", "Saturn"),
    ("medicine", "Saturn"),
    ("writers", "Moon"),
]


def _load(name: str, url: str) -> list[dict]:
    path = f"{CACHE}/gauq_{name}.csv"
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _plus_zones(dt: datetime, lat: float, lon: float) -> dict[str, bool]:
    jd = swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60 + dt.second / 3600,
    )
    armc = swe.houses_ex(jd, lat, lon, b"P")[1][2]
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    out = {}
    for planet, code in PLANETS.items():
        xx = swe.calc_ut(jd, code)[0]
        house = int(swe.house_pos(armc, lat, eps, (xx[0], xx[1]), b"P"))
        out[planet] = house in PLUS_ZONE_HOUSES
    return out


def build() -> tuple[list[str], dict[str, np.ndarray]]:
    categories: list[str] = []
    flags: dict[str, list[bool]] = {p: [] for p in PLANETS}
    for name, url in FILES.items():
        for row in _load(name, url):
            cat = CATEGORY.get(row.get("OCCU", ""))
            if cat is None:
                continue
            try:
                dt = datetime.fromisoformat(row["DATE"])
                lat, lon = float(row["LAT"]), float(row["LON"])
            except (ValueError, KeyError, TypeError):
                continue
            pz = _plus_zones(dt, lat, lon)
            categories.append(cat)
            for p in PLANETS:
                flags[p].append(pz[p])
    return categories, {p: np.array(v, dtype=bool) for p, v in flags.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--perms", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    categories, flags = build()
    cats = np.array(categories)
    n = len(cats)
    rng = np.random.default_rng(args.seed)

    print(f"=== Gauquelin plus-zone test (houses 9,12) | n={n} ===")
    counts = {c: int((cats == c).sum()) for c in set(categories)}
    print(f"  cohorts: {counts}")
    pooled = {p: flags[p].mean() for p in PLANETS}
    print(f"  pooled plus-zone rates: "
          f"{ {p: round(float(r),3) for p,r in pooled.items()} }")

    print("\n  hypothesis            n     rate    pooled   null_mean   p(excess)")
    for cat, planet in HYPOTHESES:
        mask = cats == cat
        size = int(mask.sum())
        if size == 0:
            continue
        f = flags[planet]
        authentic = float(f[mask].mean())
        # Permutation null: random equal-size cohorts from the pool.
        idx = np.arange(n)
        null = np.empty(args.perms)
        for i in range(args.perms):
            null[i] = f[rng.choice(idx, size=size, replace=False)].mean()
        p = float((null >= authentic).mean())
        flag = "  <-- p<0.05" if p < 0.05 else ""
        print(f"  {cat:9}/{planet:7} {size:5d}  {authentic:.4f}  "
              f"{pooled[planet]:.4f}   {null.mean():.4f}    {p:.4f}{flag}")

    print("\nNull = same-size cohort drawn at random from the pool; p is the "
          "fraction meeting/beating the authentic rate. A single p<0.05 among "
          "several hypotheses is not decisive.")


if __name__ == "__main__":
    main()
