"""The shape manifold: every profile as a point in composite-shape space.

The next-phase, meaning-free analysis. Compute each profile's normalized composite
shape (8 axes), then characterize the population manifold:

  * PCA -- the dominant axes of structural variation and effective dimensionality.
  * clustering -- how many natural structural groups exist, and what defines them.
  * structure vs null -- is the manifold genuinely clustered, or one diffuse blob?
    (Null shuffles each axis independently, destroying cross-axis structure.)

No labels, no meaning. Clusters here are structural types; whether any maps to an
external construct is a separate hypothesis, not asserted here. (The composite is
name-derived, so structural groups will correlate with name properties -- flagged.)
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.kamea.composite_shape import composite_shape_from_name
from atlas.kamea.shape_vector import AXES

IV = "output/compiled/identity_vectors"
SEED = 20260728


def load_shapes():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    names, rows = [], []
    for fn in files:
        d = json.load(open(f"{IV}/{fn}", encoding="utf-8"))
        name = d.get("profile_name") or fn.replace(".identity-vector.json", "")
        cs = composite_shape_from_name(name)
        names.append(name)
        rows.append(cs.vector())
    return names, np.array(rows)


def kmeans(X, k, rng, iters=50):
    n = len(X)
    # k-means++ init
    centers = [X[rng.integers(n)]]
    for _ in range(k - 1):
        d = np.min([((X - c) ** 2).sum(1) for c in centers], axis=0)
        probs = d / d.sum() if d.sum() > 0 else np.ones(n) / n
        centers.append(X[rng.choice(n, p=probs)])
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
    return labels, C


def silhouette(D, labels):
    n = len(labels)
    ks = np.unique(labels)
    s = np.zeros(n)
    for i in range(n):
        same = labels == labels[i]
        same[i] = False
        a = D[i, same].mean() if same.any() else 0.0
        b = min((D[i, labels == j].mean() for j in ks if j != labels[i]), default=0.0)
        s[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0
    return float(s.mean())


def main():
    names, X = load_shapes()
    print(f"profiles in shape space: {len(names)}\n")

    Xz = (X - X.mean(0)) / (X.std(0) + 1e-12)

    # ---- PCA ----
    U, S, Vt = np.linalg.svd(Xz - Xz.mean(0), full_matrices=False)
    var = S ** 2 / (S ** 2).sum()
    print("=== PCA: axes of structural variation ===")
    cum = 0.0
    for i in range(len(var)):
        cum += var[i]
        top = sorted(zip(AXES, Vt[i]), key=lambda t: -abs(t[1]))[:3]
        loads = ", ".join(f"{a}{'+' if w > 0 else '-'}{abs(w):.2f}" for a, w in top)
        print(f"  PC{i+1}: {var[i]*100:5.1f}%  (cum {cum*100:5.1f}%)   {loads}")
    eff = int((var.cumsum() < 0.9).sum() + 1)
    print(f"  effective dimensionality (90% var): {eff} of 8 axes\n")

    # ---- clustering + structure-vs-null ----
    rng = np.random.default_rng(SEED)
    D = np.sqrt(((Xz[:, None, :] - Xz[None, :, :]) ** 2).sum(2))
    print("=== clustering: how many natural structural groups? ===")
    best = None
    for k in range(2, 7):
        labels, _ = kmeans(Xz, k, np.random.default_rng(SEED + k))
        sil = silhouette(D, labels)
        # null: independently shuffle each axis, recluster
        nulls = []
        for t in range(10):
            Xs = np.column_stack([rng.permutation(Xz[:, j]) for j in range(Xz.shape[1])])
            Dn = np.sqrt(((Xs[:, None, :] - Xs[None, :, :]) ** 2).sum(2))
            ln, _ = kmeans(Xs, k, np.random.default_rng(500 + t))
            nulls.append(silhouette(Dn, ln))
        nm = np.mean(nulls)
        flag = " <-- above null" if sil > np.max(nulls) else ""
        print(f"  k={k}: silhouette {sil:.4f}  (null {nm:.4f})  {flag}")
        if best is None or sil > best[1]:
            best = (k, sil, labels)

    k, sil, labels = best
    print(f"\n=== best k={k}: structural types (mean shape per cluster) ===")
    print(f"{'cluster':9} {'n':>5} " + " ".join(f"{a[:5]:>6}" for a in AXES))
    for j in range(k):
        m = labels == j
        prof = X[m].mean(0)
        print(f"  type {j:>2} {int(m.sum()):>5} " + " ".join(f"{v:>6.2f}" for v in prof))

    print("\nClusters are structural types in name-derived shape space; mapping any"
          "\nto an external construct is a separate hypothesis, not asserted here.")


if __name__ == "__main__":
    main()
