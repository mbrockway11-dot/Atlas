"""Create behavioral classifications from the Vedic behavior model, then measure
whether the structural (Kamea) shape lines up with them.

The vedic_behavior_service maps each behavioral theme to a graha placement:
identity->Sun, cognitive->Mercury, relational->Venus, drive->Mars, growth->Jupiter,
discipline->Saturn (emotional->Moon is excluded: it needs a birth time we lack;
strongest_function/dignity come back 'unknown' for the same reason). So the
reliable, date-robust behavioral signature is those six graha placements, computed
here directly under the admitted Lahiri ayanamsa -- the same values the service
extracts.

Classification: cluster the behavioral signatures into behavioral TYPES.
Measurement (the point -- does interpretive meaning line up?): can the Kamea
composite shape predict a person's behavioral type, above a label-permutation null?
Kamea is name-derived and Vedic is chart-derived, so the honest prior is null.
Confound note: the behavioral types are chart-derived, hence largely birth-season
(fast grahas) and era (slow grahas) -- a classification of the sky, not the person.
"""

from __future__ import annotations

import glob
import json
import os

import numpy as np
import swisseph as swe

from atlas.kamea.composite_shape import composite_shape_from_name

IV = "output/compiled/identity_vectors"
PROF = "output/library/profiles"
SEED, FOLDS, PERMS = 20260728, 5, 500
swe.set_sid_mode(swe.SIDM_LAHIRI)
# behavioral theme -> graha (date-robust set the service uses)
BEHAVIOR = {"identity": swe.SUN, "cognitive": swe.MERCURY, "relational": swe.VENUS,
            "drive": swe.MARS, "growth": swe.JUPITER, "discipline": swe.SATURN}
SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]


def _meta(key, field):
    for path in [f"{PROF}/{key}/profile.intake.json"] + glob.glob(f"{PROF}/{key}_q*/profile.intake.json"):
        if os.path.exists(path):
            v = (json.load(open(path, encoding="utf-8")).get(field) or "").strip()
            if v:
                return v
    return ""


def load():
    files = sorted(f for f in os.listdir(IV) if f.endswith(".identity-vector.json"))
    feats, shapes, cats, names, lons = [], [], [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        bd = _meta(key, "birth_date")
        if not (len(bd) == 10 and bd[:4].isdigit()):
            continue
        try:
            y, m, d = (int(x) for x in bd.split("-"))
            jd = swe.julday(y, m, d, 12.0, swe.GREG_CAL)
        except (ValueError, TypeError):
            continue
        name = json.load(open(f"{IV}/{fn}", encoding="utf-8")).get("profile_name") or key
        L = [swe.calc_ut(jd, g, swe.FLG_SIDEREAL)[0][0] for g in BEHAVIOR.values()]
        vec = []
        for lon in L:
            r = np.radians(lon)
            vec += [np.sin(r), np.cos(r)]
        feats.append(vec)
        lons.append(L)
        shapes.append(composite_shape_from_name(name).vector())
        cats.append(_meta(key, "category").lower())
        names.append(name)
    return (np.array(feats), np.array(shapes), np.array(cats), names, np.array(lons))


def kmeans(X, k, rng, iters=50):
    n = len(X)
    C = [X[rng.integers(n)]]
    for _ in range(k - 1):
        dd = np.min([((X - c) ** 2).sum(1) for c in C], axis=0)
        C.append(X[rng.choice(n, p=dd / dd.sum() if dd.sum() else np.ones(n) / n)])
    C = np.array(C); lab = np.zeros(n, int)
    for _ in range(iters):
        new = ((X[:, None] - C[None]) ** 2).sum(2).argmin(1)
        if (new == lab).all():
            break
        lab = new
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return lab


def bal_acc(X, y, classes, rng):
    n = len(y); fid = np.zeros(n, int); fid[rng.permutation(n)] = np.arange(n) % FOLDS
    rec = {c: [] for c in classes}
    for f in range(FOLDS):
        tr, te = fid != f, fid == f
        cs = [c for c in classes if (tr & (y == c)).sum()]
        C = np.stack([X[tr & (y == c)].mean(0) for c in cs])
        pred = np.array(cs)[((X[te][:, None] - C[None]) ** 2).sum(2).argmin(1)]
        for c in classes:
            mm = y[te] == c
            if mm.sum():
                rec[c].append(float((pred[mm] == c).mean()))
    return float(np.mean([np.mean(v) if v else 0.0 for v in rec.values()]))


def main():
    F, SH, C, names, LON = load()
    print(f"profiles with birth dates: {len(names)}\n")

    K = 5
    labels = kmeans((F - F.mean(0)) / (F.std(0) + 1e-12), K, np.random.default_rng(SEED))
    print(f"=== vedic BEHAVIORAL classification: {K} types (chart-derived) ===")
    print(f"{'type':6} {'n':>5}  characteristic dominant signs (Sun/Me/Ve/Ma/Ju/Sa)")
    for j in range(K):
        m = labels == j
        modes = []
        for gi in range(6):
            signs = (LON[m][:, gi] // 30).astype(int)
            modes.append(SIGNS[np.bincount(signs, minlength=12).argmax()])
        top_cat = ""
        cc = C[m]
        if (cc != "").any():
            vals, cnts = np.unique(cc[cc != ""], return_counts=True)
            top_cat = f"{vals[cnts.argmax()]} ({cnts.max()})"
        print(f"  T{j:<4} {int(m.sum()):>5}  {'/'.join(modes)}   top-occ: {top_cat}")

    y = np.array([f"T{l}" for l in labels]); classes = sorted(set(y))
    rng = np.random.default_rng(SEED)

    print("\n=== MEASURE: does the Kamea structural shape line up with behavior type? ===")
    SHz = (SH - SH.mean(0)) / (SH.std(0) + 1e-12)
    obs = bal_acc(SHz, y, classes, np.random.default_rng(SEED))
    null = np.array([bal_acc(SHz, rng.permutation(y), classes, np.random.default_rng(9000 + i)) for i in range(PERMS)])
    p = ((null >= obs).sum() + 1) / (PERMS + 1)
    print(f"  Kamea shape -> behavior type: acc {obs:.4f}  chance {1/K:.3f}  null {null.mean():.4f}  p={p:.4f}  {'*' if p < 0.05 else ''}")

    have = C != ""
    if have.sum() > 100:
        yc = C[have]; cats = sorted({c for c in yc if (yc == c).sum() >= 30})
        keep = np.isin(C, cats) & have
        Fz = (F[keep] - F[keep].mean(0)) / (F[keep].std(0) + 1e-12)
        obs2 = bal_acc(Fz, C[keep], cats, np.random.default_rng(SEED))
        null2 = np.array([bal_acc(Fz, rng.permutation(C[keep]), cats, np.random.default_rng(8000 + i)) for i in range(PERMS)])
        p2 = ((null2 >= obs2).sum() + 1) / (PERMS + 1)
        print(f"\n=== context: does the behavioral signature predict OCCUPATION? (expect birth-season confound) ===")
        print(f"  behavior -> occupation: acc {obs2:.4f}  chance {1/len(cats):.3f}  null {null2.mean():.4f}  p={p2:.4f}  {'*' if p2 < 0.05 else ''}")

    print("\nBehavioral types are chart-derived (birth-season + era); Kamea shape is")
    print("name-derived. Alignment at chance = interpretive meaning does not carry across.")


if __name__ == "__main__":
    main()
