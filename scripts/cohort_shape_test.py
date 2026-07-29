"""Do cohorts have distinct aggregate shapes -- beyond name length?

The document's collective hypothesis, tested honestly. Each occupation cohort is
represented by its aggregate (mean) composite shape. Two questions:

  RAW:   do the cohort aggregate shapes differ more than a label-shuffled null?
  CONTROLLED: after residualizing name length out of every shape axis, do they
              STILL differ? Name length is the confound that has swallowed every
              person-level claim, so this is the decisive test. If the cohort
              separation vanishes under length control, it was never collective
              structure -- just how long the names are.

Separation metric: between-cohort sum of squares (MANOVA-style), permutation null.
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.composite_shape import composite_shape_from_values
from atlas.kamea.shape_vector import AXES

IV = "output/compiled/identity_vectors"
PROF = "output/library/profiles"
SEED, PERMS, MIN = 20260728, 2000, 40
DROP = {"prominent_figure", ""}


def category_for(key):
    for p in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(p):
            c = (json.load(open(p, encoding="utf-8")).get("category") or "").strip().lower()
            if c:
                return c
    return ""


def between_ss(X, labels, classes):
    grand = X.mean(0)
    tot = 0.0
    for c in classes:
        m = labels == c
        if m.sum():
            tot += m.sum() * ((X[m].mean(0) - grand) ** 2).sum()
    return tot / len(X)


def perm_p(X, labels, classes, rng):
    obs = between_ss(X, labels, classes)
    null = np.array([between_ss(X, rng.permutation(labels), classes) for _ in range(PERMS)])
    return obs, float(((null >= obs).sum() + 1) / (PERMS + 1)), float(null.mean())


def residualize(X, L):
    R = np.empty_like(X)
    A = np.column_stack([L, np.ones_like(L)])
    for j in range(X.shape[1]):
        coef, *_ = np.linalg.lstsq(A, X[:, j], rcond=None)
        R[:, j] = X[:, j] - A @ coef
    return R


def main():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    rows, L, cats = [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        c = category_for(key)
        if c in DROP:
            continue
        name = json.load(open(f"{IV}/{fn}", encoding="utf-8")).get("profile_name") or key
        seq = english_ordinal_sequence(name)
        rows.append(composite_shape_from_values(seq).vector())
        L.append(len(seq)); cats.append(c)
    X = np.array(rows); L = np.array(L, float); cats = np.array(cats)
    vals, cnt = np.unique(cats, return_counts=True)
    classes = sorted(vals[cnt >= MIN])
    keep = np.isin(cats, classes)
    X, L, cats = X[keep], L[keep], cats[keep]
    print(f"cohorts (n>={MIN}): { {c:int((cats==c).sum()) for c in classes} }\n")

    print("=== per-cohort mean NAME LENGTH (the confound) ===")
    for c in classes:
        print(f"  {c:12} mean length {L[cats==c].mean():5.1f}")

    Xz = (X - X.mean(0)) / (X.std(0) + 1e-12)
    rng = np.random.default_rng(SEED)
    obs, p, nm = perm_p(Xz, cats, classes, np.random.default_rng(SEED))
    print(f"\n=== RAW: do cohort aggregate shapes differ? ===")
    print(f"  between-cohort SS {obs:.4f}  null {nm:.4f}  p={p:.4f}  {'<-- differ' if p < 0.05 else 'at null'}")

    Rz = residualize(X, L)
    Rz = (Rz - Rz.mean(0)) / (Rz.std(0) + 1e-12)
    obs2, p2, nm2 = perm_p(Rz, cats, classes, np.random.default_rng(SEED + 1))
    print(f"\n=== LENGTH-CONTROLLED: after residualizing name length ===")
    print(f"  between-cohort SS {obs2:.4f}  null {nm2:.4f}  p={p2:.4f}  {'<-- still differ' if p2 < 0.05 else 'collapses to null'}")
    print(f"  separation retained: {obs2/obs*100:.0f}% of the raw between-cohort SS")

    print("\nIf RAW differs but LENGTH-CONTROLLED collapses to null, the cohorts'")
    print("'aggregate shape' was name length, not collective structure.")


if __name__ == "__main__":
    main()
