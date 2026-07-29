"""Phase 12 test: are Driver / Amplifier / Regulator real, and whose property?

The document proposes functional classes DERIVED from graph metrics, not assigned.
One defensible derivation from the 8-axis shape vector:

  Driver     = flow + centralization + hierarchy   (directs/pushes flow through hubs)
  Amplifier  = topology + redundancy + complexity   (branches, reuses, multiplies paths)
  Regulator  = symmetry + resilience                (balances, stays robust)

Each person x planet graph gets a dominant functional type. Two questions:

  A. Is the functional type a property of the PLANET (the operator we know is
     real, p=0.003) -- i.e. Saturn tends one type, Mars another? Test: recover the
     planet from the 3 functional scores, vs a permutation null.
  B. Is it a property of the PERSON -- does someone carry one functional type
     across all seven of their planets more than chance? Test: within-person type
     purity vs a label-shuffled null.

If A holds and B is at null, the functional classification is operator-determined
structure (real, unconfoundable), not a personal trait.
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.projection import project_values_to_all_kameas
from atlas.kamea.shape_vector import shape_vector, AXES
from atlas.kamea.composite_shape import PLANET_ORDER

IV = "output/compiled/identity_vectors"
SEED, N = 20260728, 600
IX = {a: i for i, a in enumerate(AXES)}
TYPES = ["driver", "amplifier", "regulator"]


def functional_scores(v):
    v = np.asarray(v)
    return np.array([
        v[[IX["flow"], IX["centralization"], IX["hierarchy"]]].mean(),
        v[[IX["topology"], IX["redundancy"], IX["complexity"]]].mean(),
        v[[IX["symmetry"], IX["resilience"]]].mean(),
    ])


def bal_acc(X, y, classes, rng, folds=5):
    n = len(y); fid = np.zeros(n, int); fid[rng.permutation(n)] = np.arange(n) % folds
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
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))[:N]
    scores, planets, persons = [], [], []
    for pid, fn in enumerate(files):
        name = json.load(open(f"{IV}/{fn}", encoding="utf-8")).get("profile_name") or fn
        paths = project_values_to_all_kameas(list(english_ordinal_sequence(name)), use_planetary_transform=True)
        for p in PLANET_ORDER:
            sv = shape_vector(paths[p].coordinates)
            if sv.degenerate:
                continue
            scores.append(functional_scores(sv.axis_vector()))
            planets.append(p); persons.append(pid)
    S = np.array(scores); planets = np.array(planets); persons = np.array(persons)
    Sz = (S - S.mean(0)) / (S.std(0) + 1e-12)
    dom = np.array(TYPES)[Sz.argmax(1)]
    print(f"graphs: {len(S)}  (people x planets)\n")

    print("=== dominant functional type by planet (is it operator-determined?) ===")
    print(f"{'planet':9} {'driver':>7} {'amp':>7} {'reg':>7}   dominant")
    for p in PLANET_ORDER:
        m = planets == p
        frac = [float((dom[m] == t).mean()) for t in TYPES]
        print(f"{p:9} " + " ".join(f"{f:>7.2f}" for f in frac) + f"   {TYPES[int(np.argmax(frac))]}")

    rng = np.random.default_rng(SEED)
    print("\n=== A: does the PLANET fall out of the functional scores? ===")
    obs = bal_acc(Sz, planets, list(PLANET_ORDER), np.random.default_rng(SEED))
    null = np.array([bal_acc(Sz, rng.permutation(planets), list(PLANET_ORDER), np.random.default_rng(700 + i)) for i in range(300)])
    pA = ((null >= obs).sum() + 1) / 301
    print(f"  planet-from-functional-scores: acc {obs:.4f}  chance {1/7:.3f}  null {null.mean():.4f}  p={pA:.4f}  {'*' if pA < 0.05 else ''}")

    print("\n=== B: is functional type a consistent PERSON trait? ===")
    # within-person purity: fraction of a person's planet-graphs sharing their modal type
    def purity(labels):
        pur = []
        for pid in np.unique(persons):
            t = labels[persons == pid]
            if len(t):
                pur.append(np.bincount([TYPES.index(x) for x in t], minlength=3).max() / len(t))
        return float(np.mean(pur))
    obsP = purity(dom)
    nullP = np.array([purity(rng.permutation(dom)) for _ in range(300)])
    pB = ((nullP >= obsP).sum() + 1) / 301
    print(f"  within-person type purity: {obsP:.4f}  null {nullP.mean():.4f}  p={pB:.4f}  {'*' if pB < 0.05 else ''}")

    print("\nRead: high A + null B = the functional classification is a property of the")
    print("planetary OPERATOR (real, unconfoundable), not a personal trait.")


if __name__ == "__main__":
    main()
