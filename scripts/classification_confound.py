"""Is the above-chance classification a confound? Localize it.

The vedic fast-planet signal (balanced acc 0.264, p=0.002) could be birth-SEASON
(Sun = birth month; occupations have uneven birth-month distributions), not the
chart. Mars barely tracks season (2-yr cycle). If the signal lives in Sun /
day-of-year and Mars-only collapses to chance, it is seasonal -- a sociological
confound, not vocation-in-the-chart. Same nearest-centroid CV + label-permutation
null as compare_by_classification.py.
"""

from __future__ import annotations

import glob
import json
import os
from datetime import datetime, timezone

import numpy as np
import swisseph as swe

IV = "output/compiled/identity_vectors"
PROF = "output/library/profiles"
SEED, FOLDS, PERMS, MIN_CLASS = 20260728, 5, 500, 30
DROP = {"prominent_figure", ""}
swe.set_sid_mode(swe.SIDM_LAHIRI)
FAST = {"sun": swe.SUN, "mercury": swe.MERCURY, "venus": swe.VENUS, "mars": swe.MARS}


def _meta(key, field):
    for path in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(path):
            v = (json.load(open(path, encoding="utf-8")).get(field) or "").strip()
            if v:
                return v
    return ""


def load():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    LON, DOY, Y = [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        cat = _meta(key, "category").lower()
        if cat in DROP:
            continue
        bd = _meta(key, "birth_date")
        if not (len(bd) == 10 and bd[:4].isdigit()):
            continue
        try:
            y, m, d = (int(x) for x in bd.split("-"))
            jd = swe.julday(y, m, d, 12.0, swe.GREG_CAL)
        except (ValueError, TypeError):
            continue
        LON.append([swe.calc_ut(jd, b, swe.FLG_SIDEREAL)[0][0] for b in FAST.values()])
        DOY.append((jd - swe.julday(y, 1, 1, 12.0, swe.GREG_CAL)) / 365.25 * 360.0)
        Y.append(cat)
    return np.array(LON), np.array(DOY), np.array(Y)


def circ(cols):
    out = []
    for lon in cols:
        r = np.radians(lon)
        out += [np.sin(r), np.cos(r)]
    return out


def bal_acc(X, y, classes, rng):
    n = len(y)
    fid = np.zeros(n, int); fid[rng.permutation(n)] = np.arange(n) % FOLDS
    rec = {c: [] for c in classes}
    for f in range(FOLDS):
        tr, te = fid != f, fid == f
        cs = [c for c in classes if (tr & (y == c)).sum()]
        C = np.stack([X[tr & (y == c)].mean(0) for c in cs])
        pred = np.array(cs)[((X[te][:, None] - C[None]) ** 2).sum(2).argmin(1)]
        for c in classes:
            m = y[te] == c
            if m.sum():
                rec[c].append(float((pred[m] == c).mean()))
    return float(np.mean([np.mean(v) if v else 0.0 for v in rec.values()]))


def test(name, X, y, classes):
    sd = X.std(0); Xz = (X[:, sd > 0] - X[:, sd > 0].mean(0)) / sd[sd > 0]
    obs = bal_acc(Xz, y, classes, np.random.default_rng(SEED))
    rng = np.random.default_rng(SEED)
    null = np.array([bal_acc(Xz, rng.permutation(y), classes, np.random.default_rng(1000 + i)) for i in range(PERMS)])
    p = ((null >= obs).sum() + 1) / (PERMS + 1)
    print(f"  {name:26} acc={obs:.4f}  null={null.mean():.4f}  p={p:.4f}  {'*' if p < 0.05 else ''}")


def main():
    LON, DOY, Y = load()
    vals, counts = np.unique(Y, return_counts=True)
    classes = sorted(vals[counts >= MIN_CLASS])
    keep = np.isin(Y, classes)
    LON, DOY, Y = LON[keep], DOY[keep], Y[keep]
    print(f"n={len(Y)}, classes={ {c:int((Y==c).sum()) for c in classes} }, chance={1/len(classes):.3f}\n")
    idx = {k: i for i, k in enumerate(FAST)}
    test("all fast (Su,Me,Ve,Ma)", np.array([circ(l) for l in LON]), Y, classes)
    test("Sun only (seasonal)", np.array([circ([l[idx['sun']]]) for l in LON]), Y, classes)
    test("Mercury+Venus (seasonal)", np.array([circ([l[idx['mercury']], l[idx['venus']]]) for l in LON]), Y, classes)
    test("MARS only (season-free)", np.array([circ([l[idx['mars']]]) for l in LON]), Y, classes)
    test("day-of-year (pure season)", np.array([circ([d]) for d in DOY]), Y, classes)
    print("\nIf Sun/day-of-year carry it and Mars-only is at chance -> seasonal confound.")


if __name__ == "__main__":
    main()
