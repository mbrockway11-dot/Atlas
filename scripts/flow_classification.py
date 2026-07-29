"""Does the temporal Kamea FLOW separate classification? (parallel to compare_by_classification)

Third representation through the same lens as kamea-structural and vedic:
per profile, the birth-year flow fingerprint -- for each of the 7 classical
bodies, [path_distance, reversal_count, reduced_path_length] at the R1-W1Y window
(all bodies trace real figures; coarse sampling is robust to the unknown birth
hour). Nearest-centroid 5-fold balanced accuracy vs a label-permutation null.

Flow at birth is a function of the birth instant, so it encodes birth SEASON just
like the vedic longitudes did. Confound check by body group: seasonal bodies
(Sun/Mercury/Venus) vs season-free (Mars/Jupiter/Saturn). If seasonal carries the
signal and season-free is at chance, flow classification is the same birth-month
confound, not the flow itself.
"""

from __future__ import annotations

import glob
import json
import os
from datetime import datetime, timezone

import numpy as np

from atlas.validation.temporal_kamea import build_trajectory, canonical_spec

IV = "output/compiled/identity_vectors"
PROF = "output/library/profiles"
SEED, FOLDS, PERMS, MIN_CLASS = 20260728, 5, 500, 30
DROP = {"prominent_figure", ""}
W1Y = canonical_spec("R1-W1Y")
BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
SEASONAL = ["sun", "mercury", "venus"]
SEASON_FREE = ["mars", "jupiter", "saturn"]


def _meta(key, field):
    for path in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(path):
            v = (json.load(open(path, encoding="utf-8")).get(field) or "").strip()
            if v:
                return v
    return ""


def load():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    feats = {b: [] for b in BODIES}
    Y = []
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
            dt = datetime(y, m, d, 12, tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        row = {}
        for b in BODIES:
            diag = build_trajectory(dt, b, W1Y).diagnostics()
            row[b] = [diag["path_distance"], diag["reversal_count"], diag["reduced_path_length"]]
        for b in BODIES:
            feats[b].append(row[b])
        Y.append(cat)
    return {b: np.array(v, float) for b, v in feats.items()}, np.array(Y)


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
            mm = y[te] == c
            if mm.sum():
                rec[c].append(float((pred[mm] == c).mean()))
    return float(np.mean([np.mean(v) if v else 0.0 for v in rec.values()]))


def test(name, X, y, classes):
    sd = X.std(0)
    Xz = (X[:, sd > 0] - X[:, sd > 0].mean(0)) / sd[sd > 0]
    obs = bal_acc(Xz, y, classes, np.random.default_rng(SEED))
    rng = np.random.default_rng(SEED)
    null = np.array([bal_acc(Xz, rng.permutation(y), classes, np.random.default_rng(1000 + i)) for i in range(PERMS)])
    p = ((null >= obs).sum() + 1) / (PERMS + 1)
    print(f"  {name:34} acc={obs:.4f}  null={null.mean():.4f}  p={p:.4f}  {'*' if p < 0.05 else ''}")


def main():
    feats, Y = load()
    vals, counts = np.unique(Y, return_counts=True)
    classes = sorted(vals[counts >= MIN_CLASS])
    keep = np.isin(Y, classes)
    feats = {b: v[keep] for b, v in feats.items()}
    Y = Y[keep]
    print(f"n={len(Y)}, classes={ {c:int((Y==c).sum()) for c in classes} }, chance={1/len(classes):.3f}\n")

    def cat_bodies(bs):
        return np.concatenate([feats[b] for b in bs], axis=1)

    test("ALL flow (7 bodies)", cat_bodies(BODIES), Y, classes)
    test("SEASONAL bodies (Sun/Me/Ve)", cat_bodies(SEASONAL), Y, classes)
    test("SEASON-FREE bodies (Ma/Ju/Sa)", cat_bodies(SEASON_FREE), Y, classes)
    test("MARS flow only (season-free)", feats["mars"], Y, classes)
    test("MOON flow only (birth-hour noise)", feats["moon"], Y, classes)
    print("\nIf seasonal bodies carry it and season-free/Mars are at chance,"
          "\nflow classification is the birth-month confound, not the flow.")


if __name__ == "__main__":
    main()
