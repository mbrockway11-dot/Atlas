"""Is the shape manifold's structure just name length?

The composite is name-derived, so the dominant axis of variation (PC1, 53.6%) and
the two-type split may simply track how many letters the name has (short names
underfill large squares into paths; long names revisit and loop). This names the
axis honestly: correlate PC1 and each shape axis with name length, and check
whether length alone recovers the two clusters.
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.composite_shape import composite_shape_from_values
from atlas.kamea.shape_vector import AXES

IV = "output/compiled/identity_vectors"
SEED = 20260728


def kmeans(X, k, rng, iters=50):
    n = len(X)
    centers = [X[rng.integers(n)]]
    for _ in range(k - 1):
        d = np.min([((X - c) ** 2).sum(1) for c in centers], axis=0)
        p = d / d.sum() if d.sum() > 0 else np.ones(n) / n
        centers.append(X[rng.choice(n, p=p)])
    C = np.array(centers)
    labels = np.zeros(n, int)
    for _ in range(iters):
        new = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2).argmin(1)
        if (new == labels).all():
            break
        labels = new
        for j in range(k):
            if (labels == j).any():
                C[j] = X[labels == j].mean(0)
    return labels


def main():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    rows, lengths = [], []
    for fn in files:
        d = json.load(open(f"{IV}/{fn}", encoding="utf-8"))
        name = d.get("profile_name") or fn.replace(".identity-vector.json", "")
        seq = english_ordinal_sequence(name)
        rows.append(composite_shape_from_values(seq).vector())
        lengths.append(len(seq))
    X = np.array(rows)
    L = np.array(lengths, float)
    print(f"profiles: {len(L)}   name length: mean {L.mean():.1f}  range [{int(L.min())}, {int(L.max())}]\n")

    Xz = (X - X.mean(0)) / (X.std(0) + 1e-12)
    U, S, Vt = np.linalg.svd(Xz - Xz.mean(0), full_matrices=False)
    pc1 = (Xz - Xz.mean(0)) @ Vt[0]

    r_pc1 = float(np.corrcoef(pc1, L)[0, 1])
    print(f"=== PC1 vs name length ===")
    print(f"  Pearson r(PC1, length) = {r_pc1:+.3f}   R^2 = {r_pc1**2:.3f}  "
          f"({'PC1 IS essentially name length' if abs(r_pc1) > 0.7 else 'partly length' if abs(r_pc1) > 0.4 else 'not mainly length'})")

    print("\n=== each shape axis vs name length ===")
    for i, a in enumerate(AXES):
        r = float(np.corrcoef(X[:, i], L)[0, 1])
        print(f"  {a:14} r = {r:+.3f}")

    print("\n=== does name length recover the two clusters? ===")
    labels = kmeans(Xz, 2, np.random.default_rng(SEED + 2))
    m0, m1 = L[labels == 0].mean(), L[labels == 1].mean()
    # point-biserial = corr(length, cluster membership)
    r_pb = float(np.corrcoef(L, labels)[0, 1])
    # how well a pure length threshold reproduces the clustering
    thr = np.median(L)
    length_split = (L > thr).astype(int)
    agree = max((length_split == labels).mean(), (length_split != labels).mean())
    print(f"  mean name length: type0 {m0:.1f}  vs  type1 {m1:.1f}")
    print(f"  point-biserial r(length, cluster) = {r_pb:+.3f}")
    print(f"  a pure median-length split reproduces the 2 clusters {agree*100:.1f}% of the time")


if __name__ == "__main__":
    main()
