"""Compare the flow between the seven kameas.

The system forbids comparing trajectories on different squares directly
(temporal_kamea.path_similarity raises: different squares are not comparable) --
each square has its own size and geometry. The only defined cross-kamea
comparison is by TRANSLATION-NORMALIZED SHAPE: scale each kamea's flow figure to
a common frame and compare the figures (Jaccard of occupied cells), exactly as
kamea_flow.cross_planet_similarity does.

So: at an instant, build each body's temporal flow, take its core_shape (already
translation-normalized), rescale uniformly (aspect preserved) to a common R x R
raster, and Jaccard every pair. Repeat across many instants to ask whether the
cross-kamea flow structure is STABLE (a property of the squares) or CHURNS with
the sky (a property of the moment).
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from atlas.validation.temporal_kamea import build_trajectory, canonical_spec

SPEC = canonical_spec("R1-W3D")
BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
R = 12  # common raster resolution


def normalized_cells(core_shape) -> frozenset:
    """Uniformly rescale a translation-normalized cell figure into an R x R raster."""
    if not core_shape:
        return frozenset()
    xs = [c[0] for c in core_shape]
    ys = [c[1] for c in core_shape]
    minx, miny = min(xs), min(ys)
    ext = max(max(xs) - minx, max(ys) - miny, 1)
    out = set()
    for x, y in core_shape:
        gx = round((x - minx) / ext * (R - 1))
        gy = round((y - miny) / ext * (R - 1))
        out.add((gx, gy))
    return frozenset(out)


def jaccard(a: frozenset, b: frozenset) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def shapes_at(dt: datetime):
    out = {}
    for b in BODIES:
        d = build_trajectory(dt, b, SPEC).diagnostics()
        out[b] = (normalized_cells([tuple(c) for c in d["core_shape"]]),
                  d["path_distance"], d["stationary"])
    return out


def main():
    # A year of monthly instants (tz-aware, noon UTC).
    instants = [datetime(2026, m, 14, 12, tzinfo=timezone.utc) for m in range(1, 13)]
    n = len(BODIES)
    pair_jacc = {(BODIES[i], BODIES[j]): [] for i in range(n) for j in range(i + 1, n)}

    print("=== single instant: 2026-07-14 12:00 UTC ===")
    S = shapes_at(datetime(2026, 7, 14, 12, tzinfo=timezone.utc))
    print("  body     path_dist  still  |shape|")
    for b in BODIES:
        cells, pd, st = S[b]
        print(f"  {b:8} {pd:6}     {'Y' if st else '.'}     {len(cells):3}")
    print("\n  pairwise normalized-shape Jaccard (this instant):")
    for i in range(n):
        for j in range(i + 1, n):
            jv = jaccard(S[BODIES[i]][0], S[BODIES[j]][0])
            print(f"    {BODIES[i]:8}~{BODIES[j]:8} {jv:.3f}")

    # Stability across the year.
    for dt in instants:
        S = shapes_at(dt)
        for i in range(n):
            for j in range(i + 1, n):
                pair_jacc[(BODIES[i], BODIES[j])].append(
                    jaccard(S[BODIES[i]][0], S[BODIES[j]][0]))

    print(f"\n=== stability across 12 monthly instants (mean +- sd of pair Jaccard) ===")
    rows = []
    for pair, vals in pair_jacc.items():
        v = np.array(vals)
        rows.append((v.mean(), v.std(), pair))
    rows.sort(reverse=True)
    print("  most-alike -> least-alike kamea flow pairs:")
    for mean, sd, pair in rows:
        print(f"    {pair[0]:8}~{pair[1]:8}  mean {mean:.3f}  sd {sd:.3f}")

    allv = np.array([v for vals in pair_jacc.values() for v in vals])
    print(f"\n  overall pair Jaccard: mean {allv.mean():.3f}  sd {allv.std():.3f}")
    within = np.mean([np.std(v) for v in pair_jacc.values()])
    print(f"  mean within-pair sd across instants: {within:.3f}")
    print("  Read: if within-pair sd is large relative to the spread of pair means,"
          "\n  the cross-kamea flow structure is a property of the moment, not the squares.")


if __name__ == "__main__":
    main()
