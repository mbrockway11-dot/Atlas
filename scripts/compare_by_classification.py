"""Do profiles separate by classification (occupation category)?

The comparison the earlier passes deferred. Two feature sets, one honest test:

  * KAMEA structural -- the 357-dim name-derived signature (compiled identity
    vectors). NOTE: name-derived, so any signal is likely a demographic confound
    (occupation correlates with era/culture/language, which shape names).
  * VEDIC fast-planet -- sin/cos of the sidereal Sun/Mercury/Venus/Mars
    longitudes at birth. Era-free (fast planets don't track birth era), so this
    is the cleaner "is vocation in the chart" question, Gauquelin-style.

Test: 5-fold cross-validated nearest-centroid BALANCED accuracy, against a null
built by permuting the labels 1000x. Balanced accuracy handles class imbalance;
chance is 1/n_classes. p = fraction of label-permuted runs that meet/beat the
authentic accuracy. Categories: only meaningful classes with n>=30; the
'prominent_figure' catch-all is dropped.
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
SEED = 20260728
FOLDS = 5
PERMS = 1000
MIN_CLASS = 30
DROP = {"prominent_figure", ""}
swe.set_sid_mode(swe.SIDM_LAHIRI)
FAST = [swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS]


def category_for(key):
    for path in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(path):
            c = (json.load(open(path, encoding="utf-8")).get("category") or "").strip().lower()
            if c:
                return c
    return ""


def birth_date_for(key):
    for path in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(path):
            bd = (json.load(open(path, encoding="utf-8")).get("birth_date") or "").strip()
            if len(bd) == 10 and bd[:4].isdigit():
                try:
                    y, m, d = (int(x) for x in bd.split("-"))
                    return datetime(y, m, d, 12, tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
    return None


def load():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    d0 = json.load(open(f"{IV}/{files[0]}", encoding="utf-8"))
    groups = sorted({(v["cipher"], v["planet"]) for v in d0["vectors"]})
    feats = sorted(d0["vectors"][0]["features"].keys())
    K, VED, Y = [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        cat = category_for(key)
        if cat in DROP:
            continue
        iv = json.load(open(f"{IV}/{fn}", encoding="utf-8"))
        bg = {(v["cipher"], v["planet"]): v["features"] for v in iv["vectors"]}
        if any(g not in bg for g in groups):
            continue
        dt = birth_date_for(key)
        if dt is None:
            continue
        jd = swe.julday(dt.year, dt.month, dt.day, 12.0, swe.GREG_CAL)
        lons = [swe.calc_ut(jd, b, swe.FLG_SIDEREAL)[0][0] for b in FAST]
        ved = []
        for lon in lons:
            r = np.radians(lon)
            ved += [np.sin(r), np.cos(r)]
        K.append([float(bg[g][f]) for g in groups for f in feats])
        VED.append(ved)
        Y.append(cat)
    return np.array(K), np.array(VED), np.array(Y)


def balanced_cv_accuracy(X, y, classes, folds, rng):
    n = len(y)
    order = rng.permutation(n)
    fold_id = np.zeros(n, dtype=int)
    fold_id[order] = np.arange(n) % folds
    recalls = {c: [] for c in classes}
    for f in range(folds):
        tr, te = fold_id != f, fold_id == f
        cents = {}
        for c in classes:
            m = tr & (y == c)
            if m.sum() == 0:
                continue
            cents[c] = X[m].mean(axis=0)
        if not cents:
            continue
        cs = list(cents)
        C = np.stack([cents[c] for c in cs])
        Xte = X[te]
        d = ((Xte[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
        pred = np.array(cs)[d.argmin(axis=1)]
        yte = y[te]
        for c in classes:
            mask = yte == c
            if mask.sum():
                recalls[c].append(float((pred[mask] == c).mean()))
    per_class = {c: (np.mean(v) if v else 0.0) for c, v in recalls.items()}
    return float(np.mean(list(per_class.values()))), per_class


def run(name, X, y, classes):
    rng = np.random.default_rng(SEED)
    # standardize (unsupervised, no leakage)
    sd = X.std(axis=0)
    Xz = (X[:, sd > 0] - X[:, sd > 0].mean(axis=0)) / sd[sd > 0]
    obs, per_class = balanced_cv_accuracy(Xz, y, classes, FOLDS, np.random.default_rng(SEED))
    chance = 1.0 / len(classes)
    null = np.empty(PERMS)
    for i in range(PERMS):
        yp = rng.permutation(y)
        null[i], _ = balanced_cv_accuracy(Xz, yp, classes, FOLDS, np.random.default_rng(1000 + i))
    p = float(((null >= obs).sum() + 1) / (PERMS + 1))
    print(f"\n=== {name} ===  (n={len(y)}, {len(classes)} classes, chance={chance:.3f})")
    print(f"  balanced accuracy: {obs:.4f}   null {null.mean():.4f}+-{null.std():.4f}   "
          f"p={p:.4f}  {'<-- p<0.05' if p < 0.05 else ''}")
    print("  per-class recall:", {c: round(v, 2) for c, v in sorted(per_class.items())})
    return obs, p


def main():
    K, VED, Y = load()
    vals, counts = np.unique(Y, return_counts=True)
    classes = sorted(vals[counts >= MIN_CLASS])
    keep = np.isin(Y, classes)
    K, VED, Y = K[keep], VED[keep], Y[keep]
    print(f"loaded n={len(Y)} with classes (>= {MIN_CLASS}): "
          f"{ {c: int((Y==c).sum()) for c in classes} }")
    run("KAMEA structural (name-derived; demographic confound likely)", K, Y, classes)
    run("VEDIC fast-planet (era-free; cleaner vocation-in-chart test)", VED, Y, classes)
    print("\nA balanced accuracy at chance with p~0.5 means the classification does "
          "not separate in that representation.")


if __name__ == "__main__":
    main()
