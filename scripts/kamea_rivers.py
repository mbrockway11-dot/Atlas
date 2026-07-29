"""A person's kamea 'rivers' -- the flow figures, drawn and compared.

Two things, both using the DEFINED cross-comparison (same square only --
temporal_kamea.path_similarity refuses different squares):

  1. WITHIN-SQUARE dyad comparison. For each historical dyad, compare member A's
     river to member B's on the SAME square, via path_similarity's core_geometry
     (shape-level Jaccard). Two windows:
       - Moon at W3D (the one body that flows at a birth instant)
       - all seven at W1Y (opened window; every body traces a real river)
     Against a null of random library pairs. Does river-shape track relationship?

  2. RIVER GEOMETRY export. For a few people, dump every body's path polyline at
     W1Y so the shapes can be drawn -- 'the true shape of a person, like a river.'

Birth times are mostly unknown (noon); the wide W1Y window is coarse-sampled and
robust to the start hour, but the narrow-window Moon test is hour-sensitive --
flagged, not hidden.
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.validation.temporal_kamea import (
    build_trajectory, canonical_spec, path_similarity, CLASSICAL_BODIES, KAMEAS,
)
from atlas.kamea.path_views import build_kamea_path_views
from datetime import datetime, timezone

IV_DIR = "output/compiled/identity_vectors"
PROF_DIR = "output/library/profiles"
BODIES = sorted(CLASSICAL_BODIES)
SEED = 20260728

W3D = canonical_spec("R1-W3D")
W1Y = canonical_spec("R1-W1Y")

# Exact where known; else pulled from intake at noon.
KNOWN = {"michael": datetime(1993, 8, 16, 22, 30, tzinfo=timezone.utc)}

POSITIVE = [("steve_jobs", "steve_wozniak"), ("karl_marx", "friedrich_engels"),
            ("thomas_jefferson", "james_madison"), ("george_washington", "alexander_hamilton"),
            ("albert_einstein", "niels_bohr")]
NEGATIVE = [("nikola_tesla", "thomas_edison"), ("thomas_jefferson", "alexander_hamilton"),
            ("john_adams", "alexander_hamilton"), ("sigmund_freud", "carl_jung"),
            ("vincent_van_gogh", "paul_gauguin")]


def birth_instant(key):
    if key in KNOWN:
        return KNOWN[key]
    ip = f"{PROF_DIR}/{key}/profile.intake.json"
    if not os.path.exists(ip):
        return None
    bd = (json.load(open(ip, encoding="utf-8")).get("birth_date") or "").strip()
    if not (len(bd) == 10 and bd[:4].isdigit()):
        return None
    try:
        y, m, d = (int(x) for x in bd.split("-"))
        return datetime(y, m, d, 12, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def moon_geom(a_dt, b_dt):
    a = build_trajectory(a_dt, "moon", W3D)
    b = build_trajectory(b_dt, "moon", W3D)
    return path_similarity(a, b)["core_geometry"]


def all_geom(a_dt, b_dt):
    vals = []
    for body in BODIES:
        a = build_trajectory(a_dt, body, W1Y)
        b = build_trajectory(b_dt, body, W1Y)
        vals.append(path_similarity(a, b)["core_geometry"])
    return float(np.mean(vals))


def main():
    rng = np.random.default_rng(SEED)

    # ---- Null: random library pairs ----
    keys = [f.replace(".identity-vector.json", "") for f in os.listdir(IV_DIR)
            if f.endswith(".identity-vector.json")]
    inst = {}

    def get(k):
        if k not in inst:
            inst[k] = birth_instant(k)
        return inst[k]

    moon_null, all_null = [], []
    tries = 0
    while len(moon_null) < 200 and tries < 1200:
        tries += 1
        a, b = rng.choice(keys, size=2, replace=False)
        ia, ib = get(a), get(b)
        if ia is None or ib is None:
            continue
        moon_null.append(moon_geom(ia, ib))
        all_null.append(all_geom(ia, ib))
    moon_null, all_null = np.array(moon_null), np.array(all_null)

    print(f"=== NULL random pairs (n={len(moon_null)}) ===")
    print(f"  Moon core_geometry (W3D): mean {moon_null.mean():.3f} sd {moon_null.std():.3f}")
    print(f"  All-7   core_geometry (W1Y): mean {all_null.mean():.3f} sd {all_null.std():.3f}")

    def run(group, tag):
        print(f"\n=== {tag} dyads (Moon@W3D | All7@W1Y  core_geometry, %ile in null) ===")
        mo, al = [], []
        for a, b in group:
            ia, ib = get(a), get(b)
            if ia is None or ib is None:
                print(f"  {a}+{b}: missing birthdate"); continue
            m, x = moon_geom(ia, ib), all_geom(ia, ib)
            mo.append(m); al.append(x)
            pm = (moon_null <= m).mean() * 100
            px = (all_null <= x).mean() * 100
            print(f"  {a:18}+{b:18} Moon {m:.3f} (p{pm:4.0f}) | All7 {x:.3f} (p{px:4.0f})")
        return np.array(mo), np.array(al)

    pm, pa = run(POSITIVE, "POSITIVE")
    nm, na = run(NEGATIVE, "NEGATIVE")

    def perm_p(x, y):
        pool = np.concatenate([x, y]); L = len(x); obs = x.mean() - y.mean()
        d = [abs((s := rng.permutation(pool))[:L].mean() - s[L:].mean()) for _ in range(5000)]
        return obs, float((np.array(d) >= abs(obs)).mean())

    print("\n=== discrimination (positive vs negative) ===")
    o1, p1 = perm_p(pm, nm); o2, p2 = perm_p(pa, na)
    print(f"  Moon: pos {pm.mean():.3f} neg {nm.mean():.3f} diff {o1:+.3f} p={p1:.3f}")
    print(f"  All7: pos {pa.mean():.3f} neg {na.mean():.3f} diff {o2:+.3f} p={p2:.3f}")
    lab_m = np.concatenate([pm, nm]); lab_a = np.concatenate([pa, na])
    print(f"  labelled Moon mean {lab_m.mean():.3f} vs null {moon_null.mean():.3f}")
    print(f"  labelled All7 mean {lab_a.mean():.3f} vs null {all_null.mean():.3f}")

    # ---- River geometry export for drawing ----
    people = {"Michael Brockway": "michael", "Nikola Tesla": "nikola_tesla",
              "Thomas Edison": "thomas_edison", "Thomas Jefferson": "thomas_jefferson",
              "Alexander Hamilton": "alexander_hamilton"}
    rivers = {}
    for name, key in people.items():
        dt = get(key)
        if dt is None:
            continue
        rivers[name] = {}
        for body in BODIES:
            t = build_trajectory(dt, body, W1Y)
            views = build_kamea_path_views(t.path)
            rivers[name][body] = {
                "raw": [[int(x), int(y)] for x, y in views["analysis_path"]["coordinates"]],
                "render": [[int(x), int(y)] for x, y in views["render_path"]["coordinates"]],
                "core_shape": [[int(x), int(y)] for x, y in t.core_shape],
                "grid": KAMEAS[body].size,
                "path_distance": t.diagnostics()["path_distance"],
            }
    out = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
           "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers.json")
    with open(out, "w", encoding="utf-8") as h:
        json.dump(rivers, h)
    print(f"\nwrote rivers for {list(rivers)} -> {out}")


if __name__ == "__main__":
    main()
