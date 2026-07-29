"""Predictive harness: does the structural profile predict a real outcome,
beyond name length and era?

The general test of "how a profile acts in real life": given an independently
measured outcome per person (a behavioral score, a trait rating, or -- here, as a
no-fabrication DEMONSTRATION -- longevity from the recorded death date), ask
whether the composite shape predicts it above chance AND above the confounds
(name length, birth year/era). Any supplied behavioral dataset plugs into
`evaluate` unchanged.

DEMONSTRATION OUTCOME: age at death. This is a life OUTCOME, not "behavior in a
situation" -- it proves the harness and gives a real (no-fabrication) result while
we wait for a genuine behavioral dataset (e.g. expert Big-Five ratings).
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.composite_shape import composite_shape_from_values

IV = "output/compiled/identity_vectors"
PROF = "output/library/profiles"
SEED, PERMS = 20260728, 4000


def meta(key, field, sub=None):
    for p in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(p):
            j = json.load(open(p, encoding="utf-8"))
            v = j.get(field)
            if sub and isinstance(v, dict):
                v = v.get(sub)
            if v and str(v).strip():
                return str(v).strip()
    return ""


def _r2(X, y):
    """R^2 of OLS y ~ X (X already has intercept column)."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    ss_tot = ((y - y.mean()) ** 2).sum()
    return 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else 0.0


def evaluate(shape, outcome, covariates, rng, label):
    """Does shape predict outcome, raw and after removing covariates?"""
    n = len(outcome)
    Xs = np.column_stack([shape, np.ones(n)])
    # covariates alone
    Xc = np.column_stack([covariates, np.ones(n)])
    r2_cov = _r2(Xc, outcome)
    # raw: shape -> outcome
    obs = _r2(Xs, outcome)
    null = np.array([_r2(Xs, rng.permutation(outcome)) for _ in range(PERMS)])
    p_raw = ((null >= obs).sum() + 1) / (PERMS + 1)
    # controlled: residualize outcome AND shape on covariates, then shape -> residual
    y_res = outcome - Xc @ np.linalg.lstsq(Xc, outcome, rcond=None)[0]
    S_res = np.column_stack([
        shape[:, j] - Xc @ np.linalg.lstsq(Xc, shape[:, j], rcond=None)[0]
        for j in range(shape.shape[1])
    ] + [np.ones(n)])
    obs_c = _r2(S_res, y_res)
    null_c = np.array([_r2(S_res, rng.permutation(y_res)) for _ in range(PERMS)])
    p_ctrl = ((null_c >= obs_c).sum() + 1) / (PERMS + 1)
    print(f"=== {label} (n={n}) ===")
    print(f"  covariates alone (name length + era) explain R^2 = {r2_cov:.4f}")
    print(f"  RAW   shape -> outcome:      R^2 = {obs:.4f}   null {null.mean():.4f}   p = {p_raw:.4f}  {'*' if p_raw < 0.05 else ''}")
    print(f"  CTRL  shape -> outcome|cov:  R^2 = {obs_c:.4f}   null {null_c.mean():.4f}   p = {p_ctrl:.4f}  {'*' if p_ctrl < 0.05 else ''}")
    return p_raw, p_ctrl


def main():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    shape, age, length, byear = [], [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        bd = meta(key, "birth_date")
        dd = meta(key, "metadata", "death_date") or meta(key, "death_date")
        if not (len(bd) >= 4 and bd[:4].isdigit() and len(dd) >= 4 and dd[:4].isdigit()):
            continue
        by, dy = int(bd[:4]), int(dd[:4])
        if not (0 < dy - by < 120):
            continue
        name = json.load(open(f"{IV}/{fn}", encoding="utf-8")).get("profile_name") or key
        seq = english_ordinal_sequence(name)
        shape.append(composite_shape_from_values(seq).vector())
        age.append(dy - by); length.append(len(seq)); byear.append(by)
    S = np.array(shape); y = np.array(age, float)
    Sz = (S - S.mean(0)) / (S.std(0) + 1e-12)
    cov = np.column_stack([np.array(length, float), np.array(byear, float)])
    covz = (cov - cov.mean(0)) / cov.std(0)

    print("HARNESS DEMONSTRATION on longevity (age at death) -- a life outcome,")
    print("not situational behavior. Real behavioral data plugs into evaluate() the same way.\n")
    evaluate(Sz, y, covz, np.random.default_rng(SEED), "longevity: does structural shape predict age at death?")
    print("\nRAW significant but CTRL at null = the profile 'predicts' the outcome only")
    print("through name length / era, not through structure. CTRL significant = a real,")
    print("confound-independent link -- the signal a behavioral dataset would need to show.")


if __name__ == "__main__":
    main()
