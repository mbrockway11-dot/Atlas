"""Cross-level self-similarity: is a person's shape the same at every scale?

The deep form of self-similitude. A person's Kamea representation exists at three
nesting levels:

  cipher x planet  ->  21 traversal graphs (finest)
  planet           ->   7 per-planet shapes
  composite        ->   1 aggregate shape

If the STRUCTURE looks statistically the same at each level -- same 8-axis
correlation geometry -- the person is self-similar under aggregation. This
compares the 8x8 axis-correlation matrix across levels (pooled over many names),
against a shuffled null. Means are preserved trivially by averaging; the test is
whether the *correlation shape* survives aggregation.
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.ciphers import run_all_ciphers
from atlas.kamea.projection import project_values_to_all_kameas
from atlas.kamea.shape_vector import shape_vector, AXES
from atlas.kamea.composite_shape import composite_shape_from_values, PLANET_ORDER

IV = "output/compiled/identity_vectors"
SEED = 20260728
N = 500


def corr_matrix(rows):
    X = np.array(rows)
    keep = X.std(0) > 0
    R = np.eye(len(AXES))
    C = np.corrcoef(X[:, keep], rowvar=False)
    idx = np.where(keep)[0]
    for a in range(len(idx)):
        for b in range(len(idx)):
            R[idx[a], idx[b]] = C[a, b]
    return R


def upper(M):
    iu = np.triu_indices(M.shape[0], k=1)
    return M[iu]


def main():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))[:N]
    cipher_rows, planet_rows, comp_rows = [], [], []
    for fn in files:
        name = json.load(open(f"{IV}/{fn}", encoding="utf-8")).get("profile_name") or fn
        ciph = run_all_ciphers(name)
        # cipher x planet level
        for cname, values in ciph.items():
            if not values:
                continue
            paths = project_values_to_all_kameas(list(values), use_planetary_transform=True)
            for p in PLANET_ORDER:
                sv = shape_vector(paths[p].coordinates)
                if not sv.degenerate:
                    cipher_rows.append(sv.axis_vector())
        # planet level + composite (ordinal cipher)
        ordv = ciph.get("ordinal") or []
        if ordv:
            paths = project_values_to_all_kameas(list(ordv), use_planetary_transform=True)
            for p in PLANET_ORDER:
                sv = shape_vector(paths[p].coordinates)
                if not sv.degenerate:
                    planet_rows.append(sv.axis_vector())
            comp_rows.append(composite_shape_from_values(list(ordv)).vector())

    print(f"names: {len(files)}   cipherxplanet shapes: {len(cipher_rows)}   "
          f"planet shapes: {len(planet_rows)}   composites: {len(comp_rows)}\n")

    Rc = corr_matrix(cipher_rows)
    Rp = corr_matrix(planet_rows)
    Rk = corr_matrix(comp_rows)

    def sim(A, B):
        return float(np.corrcoef(upper(A), upper(B))[0, 1])

    print("=== self-similarity of the 8-axis correlation geometry across levels ===")
    print(f"  cipherxplanet  vs  planet     : r = {sim(Rc, Rp):+.3f}")
    print(f"  planet         vs  composite  : r = {sim(Rp, Rk):+.3f}")
    print(f"  cipherxplanet  vs  composite  : r = {sim(Rc, Rk):+.3f}")

    # null: shuffle each axis independently at the finest level, rebuild matrix
    rng = np.random.default_rng(SEED)
    X = np.array(cipher_rows)
    nulls = []
    for _ in range(200):
        Xs = np.column_stack([rng.permutation(X[:, j]) for j in range(X.shape[1])])
        nulls.append(sim(corr_matrix(Xs), Rk))
    nulls = np.array(nulls)
    obs = sim(Rc, Rk)
    p = float((np.abs(nulls) >= abs(obs)).mean())
    print(f"\n  cross-level correlation-geometry match (finest vs composite):")
    print(f"    observed r = {obs:+.3f}   null |r| mean {np.abs(nulls).mean():.3f}   p = {p:.3f}"
          f"   {'<-- self-similar beyond null' if p < 0.05 else 'at null'}")

    print("\n=== per-level structure (variance shrinks; does the shape persist?) ===")
    for label, rows in [("cipherxplanet", cipher_rows), ("planet", planet_rows), ("composite", comp_rows)]:
        X = np.array(rows)
        tot_var = float(X.var(0).sum())
        U, S, _ = np.linalg.svd(X - X.mean(0), full_matrices=False)
        eff = int((np.cumsum(S**2 / (S**2).sum()) < 0.9).sum() + 1)
        print(f"  {label:14} n={len(rows):>5}  total_var {tot_var:.3f}  effective_dim {eff}/8")

    print("\nMeans are preserved by averaging; if the correlation geometry also"
          "\npersists (high cross-level r above null) the person is self-similar in"
          "\nSHAPE across scales even as variance shrinks with aggregation.")


if __name__ == "__main__":
    main()
