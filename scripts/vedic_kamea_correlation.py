"""Is there any correlation between the Vedic chart and the structural kamea?

Two representations of the same people, sharing NO mechanical input:
  - structural kamea : the person's NAME (gematria) walked through each planet's
    magic square -> 21 cipher x planet groups x 17 geometric features. Name-derived.
  - Vedic sidereal   : the planets' sidereal longitudes at birth. Birth-derived.

(The *temporal* kamea flow is deliberately NOT used here: it is computed from the
same birth instant and ephemeris as the Vedic chart, so any agreement between the
two would be a mechanical artifact, not a discovery. Only the name-derived
structural kamea is an independent representation worth correlating.)

METHOD -- Mantel test. For a sample of N people, build two pairwise distance
matrices and correlate their upper triangles; the null shuffles one labelling.

  D_kamea  : Euclidean distance between z-scored 357-dim structural feature vectors.
  D_vedic  : mean circular distance over the FAST planets {Sun, Mercury, Venus,
             Mars} (fast planets do not track birth era, so era cannot manufacture
             a correlation). A secondary D_vedic_all adds the slow planets and is
             reported WITH the era caveat.
  D_cat    : 0 if two people share an occupation category, else 1.

  Three Mantel tests, each a permutation null (labels of one matrix shuffled):
    A  kamea  vs vedic   -- the headline: name-structure vs birth-chart
    B  kamea  vs category -- does name-structure encode occupation?
    C  vedic  vs category -- does the birth chart encode occupation? (Gauquelin-ish)

  One-tailed p = fraction of permutations with r >= observed. Fixed seed; the
  direction (positive agreement) is the only one of interest. If null, reported null.
"""

from __future__ import annotations

import json
import os

import numpy as np
import swisseph as swe


SEED = 20260728
N = 600
PERMS = 4000
ROOT = "output"
IV_DIR = f"{ROOT}/compiled/identity_vectors"
PROF_DIR = f"{ROOT}/library/profiles"
FAST = [("Sun", swe.SUN), ("Mercury", swe.MERCURY), ("Venus", swe.VENUS), ("Mars", swe.MARS)]
SLOW = [("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN)]

swe.set_sid_mode(swe.SIDM_LAHIRI)


def canonical_schema(sample_path: str):
    d = json.load(open(sample_path, encoding="utf-8"))
    groups, feats = [], None
    for v in d["vectors"]:
        groups.append((v["cipher"], v["planet"]))
        if feats is None:
            feats = sorted(v["features"].keys())
    return sorted(set(groups)), feats


def feature_vector(iv: dict, groups, feats):
    by_group = {(v["cipher"], v["planet"]): v["features"] for v in iv["vectors"]}
    out = []
    for g in groups:
        f = by_group.get(g)
        if f is None:
            return None  # incomplete profile -> drop
        for name in feats:
            if name not in f:
                return None
            out.append(float(f[name]))
    return out


def vedic_longitudes(birth_date: str, bodies):
    y, m, d = (int(x) for x in birth_date.split("-"))
    jd = swe.julday(y, m, d, 12.0, swe.GREG_CAL)
    return [swe.calc_ut(jd, code, swe.FLG_SIDEREAL)[0][0] for _, code in bodies]


def circular_mean_dist(a: np.ndarray, b: np.ndarray) -> float:
    diff = np.abs(a - b) % 360.0
    return float(np.minimum(diff, 360.0 - diff).mean())


def mantel(dk_upper: np.ndarray, dx_full: np.ndarray, iu, rng, perms: int):
    """Correlate dk (fixed, as upper-tri vector) with dx (full matrix, permuted)."""
    n = dx_full.shape[0]
    obs = np.corrcoef(dk_upper, dx_full[iu])[0, 1]
    null = np.empty(perms)
    for i in range(perms):
        p = rng.permutation(n)
        null[i] = np.corrcoef(dk_upper, dx_full[np.ix_(p, p)][iu])[0, 1]
    pval = float((null >= obs).mean())
    return obs, pval, float(null.mean()), float(null.std())


def main() -> None:
    rng = np.random.default_rng(SEED)
    files = sorted(f for f in os.listdir(IV_DIR) if f.endswith(".identity-vector.json"))
    groups, feats = canonical_schema(f"{IV_DIR}/{files[0]}")
    dim = len(groups) * len(feats)
    print(f"schema: {len(groups)} groups x {len(feats)} features = {dim} dims\n")

    keys, kamea_rows, vedic_fast, vedic_all, cats = [], [], [], [], []
    n_no_intake = n_no_date = n_incomplete = 0
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        intake_p = f"{PROF_DIR}/{key}/profile.intake.json"
        if not os.path.exists(intake_p):
            n_no_intake += 1
            continue
        intake = json.load(open(intake_p, encoding="utf-8"))
        bd = (intake.get("birth_date") or "").strip()
        if not (len(bd) == 10 and bd[4] == "-" and bd[:4].isdigit() and bd[:4] != "0000"):
            n_no_date += 1
            continue
        iv = json.load(open(f"{IV_DIR}/{fn}", encoding="utf-8"))
        fv = feature_vector(iv, groups, feats)
        if fv is None:
            n_incomplete += 1
            continue
        try:
            vf = vedic_longitudes(bd, FAST)
            va = vedic_longitudes(bd, FAST + SLOW)
        except Exception:
            continue
        keys.append(key)
        kamea_rows.append(fv)
        vedic_fast.append(vf)
        vedic_all.append(va)
        cats.append((intake.get("category") or "").strip().lower())

    print(f"usable profiles: {len(keys)}  "
          f"(dropped: no_intake={n_no_intake}, no_date={n_no_date}, incomplete={n_incomplete})")

    idx = rng.choice(len(keys), size=min(N, len(keys)), replace=False)
    K = np.array(kamea_rows)[idx]
    Vf = np.array(vedic_fast)[idx]
    Va = np.array(vedic_all)[idx]
    C = np.array(cats)[idx]
    n = len(idx)
    print(f"sampled n={n} for Mantel; perms={PERMS}; seed={SEED}\n")

    # Standardize kamea features, drop zero-variance columns.
    sd = K.std(axis=0)
    K = (K[:, sd > 0] - K[:, sd > 0].mean(axis=0)) / sd[sd > 0]

    iu = np.triu_indices(n, k=1)

    # Distance matrices.
    Dk = np.sqrt(((K[:, None, :] - K[None, :, :]) ** 2).sum(axis=2))
    Dvf = np.zeros((n, n)); Dva = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dvf = circular_mean_dist(Vf[i], Vf[j]); Dvf[i, j] = Dvf[j, i] = dvf
            dva = circular_mean_dist(Va[i], Va[j]); Dva[i, j] = Dva[j, i] = dva
    Dk_u = Dk[iu]

    print("=== Mantel tests (one-tailed p = P(null r >= observed)) ===\n")
    r, p, nm, ns = mantel(Dk_u, Dvf, iu, np.random.default_rng(SEED + 1), PERMS)
    print(f"A  kamea vs vedic(fast)  : r={r:+.4f}  null {nm:+.4f}+-{ns:.4f}  p={p:.4f}  "
          f"{'<-- p<0.05' if p < 0.05 else ''}")
    r2, p2, _, _ = mantel(Dk_u, Dva, iu, np.random.default_rng(SEED + 2), PERMS)
    print(f"   kamea vs vedic(all)   : r={r2:+.4f}                       p={p2:.4f}  (era caveat)")

    have = C != ""
    if have.sum() >= 30:
        m = have.sum()
        Kc = K[have]; sub = np.where(have)[0]
        Dkc = Dk[np.ix_(sub, sub)]
        Dvc = Dvf[np.ix_(sub, sub)]
        Cc = C[have]
        Dcat = (Cc[:, None] != Cc[None, :]).astype(float)
        iuc = np.triu_indices(m, k=1)
        rb, pb, _, _ = mantel(Dkc[iuc], Dcat, iuc, np.random.default_rng(SEED + 3), PERMS)
        rc, pc, _, _ = mantel(Dvc[iuc], Dcat, iuc, np.random.default_rng(SEED + 4), PERMS)
        cats_present = sorted(set(Cc))
        print(f"\n(category subset n={m}; categories={cats_present})")
        print(f"B  kamea vs category     : r={rb:+.4f}  p={pb:.4f}  "
              f"{'<-- p<0.05' if pb < 0.05 else ''}   "
              "(negative r = same-category people closer)")
        print(f"C  vedic vs category     : r={rc:+.4f}  p={pc:.4f}  "
              f"{'<-- p<0.05' if pc < 0.05 else ''}")
    else:
        print("\n(too few profiles carry an occupation category for tests B/C)")

    print("\nNote: a Mantel r near 0 with p ~ 0.5 means the two representations are "
          "geometrically independent. Fast-planet Vedic distance is era-free, so "
          "test A cannot be inflated by birth-era shared naming conventions.")


if __name__ == "__main__":
    main()
