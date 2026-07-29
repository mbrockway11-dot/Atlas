"""The seven planets as structural operators, not meanings.

Feed the SAME inputs through each planetary square and measure the shape each
generates. Any difference is purely the operator. Two claims, both measurable:

  A. "each larger square permits a larger family of admissible structures" --
     with inputs SCALED to each square (length ~ 3*n^2), does shape-space
     diversity grow Saturn -> Moon?
  B. "planets are distinct generators of topology" -- with FIXED inputs shared
     across planets, can the planet be recovered from the 8-axis shape alone?
     This is a pure-mathematics test: no demographics, no season, no external
     label, so it cannot be confounded. Chance = 1/7.

Both use the shape_vector module. Diversity = total variance (trace of the axis
covariance) over non-degenerate shapes.
"""

from __future__ import annotations

import numpy as np

from atlas.kamea.projection import project_values_to_all_kameas, project_values_to_kamea
from atlas.kamea.shape_vector import shape_vector, AXES
from atlas.kamea.squares import KAMEAS

SEED = 20260728
ORDER = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"]
SIZES = {k: KAMEAS[k].size for k in ORDER}


def shapes_for(sequences):
    """Return {planet: (axis_matrix, degenerate_mask)} for a set of value seqs."""
    per = {k: [] for k in ORDER}
    deg = {k: [] for k in ORDER}
    for seq in sequences:
        paths = project_values_to_all_kameas(list(seq), use_planetary_transform=True)
        for k in ORDER:
            sv = shape_vector(paths[k].coordinates)
            per[k].append(sv.axis_vector())
            deg[k].append(sv.degenerate)
    return {k: (np.array(per[k]), np.array(deg[k])) for k in ORDER}


def bal_acc(X, y, classes, folds, rng):
    n = len(y)
    fid = np.zeros(n, int); fid[rng.permutation(n)] = np.arange(n) % folds
    rec = {c: [] for c in classes}
    for f in range(folds):
        tr, te = fid != f, fid == f
        cs = [c for c in classes if (tr & (y == c)).sum()]
        C = np.stack([X[tr & (y == c)].mean(0) for c in cs])
        pred = np.array(cs)[((X[te][:, None] - C[None]) ** 2).sum(2).argmin(1)]
        for c in classes:
            m = y[te] == c
            if m.sum():
                rec[c].append(float((pred[m] == c).mean()))
    return float(np.mean([np.mean(v) if v else 0.0 for v in rec.values()]))


def main():
    rng = np.random.default_rng(SEED)

    # ---- Claim A: admissible family vs square size (inputs SCALED per square) ----
    print("=== CLAIM A: does the admissible shape-family grow with square size? ===")
    print("(inputs scaled to each square: length 3*n^2, values 1..2*n^2, 300 draws)\n")
    print(f"{'planet':9} {'size':>4} {'degen%':>7} {'diversity':>10} {'distinct':>9}")
    div_by_size = []
    for k in ORDER:
        n2 = SIZES[k] ** 2
        rows, degs = [], []
        for _ in range(300):
            seq = rng.integers(1, 2 * n2 + 1, size=3 * n2)
            sv = shape_vector(project_values_to_kamea(list(seq), k, use_planetary_transform=True).coordinates)
            rows.append(sv.axis_vector()); degs.append(sv.degenerate)
        mat, deg = np.array(rows), np.array(degs)
        live = mat[~deg]
        diversity = float(live.var(axis=0).sum()) if len(live) > 1 else 0.0
        distinct = len({tuple(np.round(r, 3)) for r in live})
        div_by_size.append((SIZES[k], diversity))
        print(f"{k:9} {SIZES[k]:>4} {100*deg.mean():>6.1f}% {diversity:>10.4f} {distinct:>9}")
    sizes = np.array([s for s, _ in div_by_size]); divs = np.array([d for _, d in div_by_size])
    r = float(np.corrcoef(sizes, divs)[0, 1])
    print(f"\n  diversity-vs-size correlation: r = {r:+.3f}  "
          f"({'grows with size' if r > 0.3 else 'does NOT grow with size' if r < 0.3 else 'flat'})")

    # ---- Claim B: distinct generators (FIXED inputs shared across planets) ----
    print("\n=== CLAIM B: are the planets distinct generators? (pure-math, unconfoundable) ===")
    fixed = [rng.integers(1, 101, size=30) for _ in range(600)]
    per = shapes_for(fixed)
    X, y = [], []
    for k in ORDER:
        mat, deg = per[k]
        X.append(mat[~deg]); y += [k] * int((~deg).sum())
    X = np.vstack(X); y = np.array(y)
    sd = X.std(0); Xz = (X[:, sd > 0] - X[:, sd > 0].mean(0)) / sd[sd > 0]
    classes = ORDER
    obs = bal_acc(Xz, y, classes, 5, np.random.default_rng(SEED))
    null = np.array([bal_acc(Xz, rng.permutation(y), classes, 5, np.random.default_rng(2000 + i))
                     for i in range(300)])
    p = ((null >= obs).sum() + 1) / 301
    print(f"  planet-from-shape balanced accuracy: {obs:.4f}   chance={1/7:.3f}   "
          f"null={null.mean():.4f}   p={p:.4f}  {'<-- p<0.05' if p < 0.05 else ''}")

    # ---- Characteristic profile per planet (fixed inputs) ----
    print("\n=== characteristic flow geometry per planet (mean 8-axis, fixed inputs) ===")
    print(f"{'planet':9} " + " ".join(f"{a[:5]:>6}" for a in AXES) + f" {'degen%':>7}")
    for k in ORDER:
        mat, deg = per[k]
        live = mat[~deg]
        prof = live.mean(0) if len(live) else np.zeros(8)
        print(f"{k:9} " + " ".join(f"{v:>6.2f}" for v in prof) + f" {100*deg.mean():>6.1f}%")


if __name__ == "__main__":
    main()
