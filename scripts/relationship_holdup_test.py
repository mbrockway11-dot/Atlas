"""Do the system's relationship descriptions hold up to real history?

The compare service scores any two profiles (composite / relationship similarity,
planet agreement). The report service writes a description (Overview, Tension
Vectors, Complementarity...). The identity vectors are NAME-derived, so the prior
is that these scores reflect name-geometry, not the lived relationship.

Test:
  1. A labelled set of historical dyads, both members in the library, tagged
     POSITIVE (sustained cooperative bond) or NEGATIVE (defining antagonism/rupture).
  2. Score each with the real compare service.
  3. NULL: many random library pairs -> the population distribution of the score.
  4. Ask: do labelled dyads differ from random pairs at all? Do POSITIVE dyads
     differ from NEGATIVE? If related people (allies AND rivals alike) sit on top
     of the random distribution, the score describes names, not relationships.
  5. Print the actual Tension / Complementarity text for four famous dyads so the
     qualitative description can be read against known history.
"""

from __future__ import annotations

import json
import os

import numpy as np

from atlas.services.compare_profiles_service import build_compare_profiles_payload
from atlas.services.relationship_report_service import build_relationship_report_payload

SEED = 20260728
N_NULL = 300
IV_DIR = "output/compiled/identity_vectors"

POSITIVE = [
    ("steve_jobs", "steve_wozniak", "Apple co-founders"),
    ("karl_marx", "friedrich_engels", "lifelong collaborators"),
    ("thomas_jefferson", "james_madison", "political allies / friends"),
    ("george_washington", "alexander_hamilton", "mentor & close ally"),
    ("albert_einstein", "niels_bohr", "friends & sparring partners"),
]
NEGATIVE = [
    ("nikola_tesla", "thomas_edison", "War of Currents rivals"),
    ("thomas_jefferson", "alexander_hamilton", "bitter political rivals"),
    ("john_adams", "alexander_hamilton", "Federalist enemies"),
    ("sigmund_freud", "carl_jung", "mentor->bitter rupture"),
    ("vincent_van_gogh", "paul_gauguin", "friendship->violent split"),
]


def score(a, b):
    p = build_compare_profiles_payload(a, b)
    if not p.success:
        return None
    s = p.summary
    return {
        "composite": s["composite_similarity"],
        "relationship": s["relationship_similarity"],
        "planet_agreement": s["overall_planet_agreement"],
        "dominant_match": p.diagnostics["planet_agreement"]["dominant_match"],
        "dominant_divergence": p.diagnostics["planet_agreement"]["dominant_divergence"],
    }


def pct(dist, v):
    return float((np.asarray(dist) <= v).mean() * 100.0)


def main():
    rng = np.random.default_rng(SEED)
    keys = [f.replace(".identity-vector.json", "")
            for f in os.listdir(IV_DIR) if f.endswith(".identity-vector.json")]

    print(f"=== NULL: {N_NULL} random library pairs ===")
    comp, rel, pa = [], [], []
    tries = 0
    while len(comp) < N_NULL and tries < N_NULL * 4:
        tries += 1
        a, b = rng.choice(keys, size=2, replace=False)
        r = score(a, b)
        if r:
            comp.append(r["composite"]); rel.append(r["relationship"]); pa.append(r["planet_agreement"])
    comp, rel, pa = map(np.array, (comp, rel, pa))
    print(f"  composite    : mean {comp.mean():.4f}  sd {comp.std():.4f}  "
          f"[{comp.min():.4f}, {comp.max():.4f}]")
    print(f"  relationship : mean {rel.mean():.4f}  sd {rel.std():.4f}  "
          f"[{rel.min():.4f}, {rel.max():.4f}]")
    print(f"  planet_agree : mean {pa.mean():.4f}  sd {pa.std():.4f}  "
          f"[{pa.min():.4f}, {pa.max():.4f}]")

    def run(group, tag):
        print(f"\n=== {tag} dyads (composite | %ile-in-null | planet_agree | dom match/diverge) ===")
        out = []
        for a, b, desc in group:
            r = score(a, b)
            if r is None:
                print(f"  {a} + {b}: NO DATA")
                continue
            out.append(r)
            print(f"  {a:20}+{b:20} {r['composite']:.4f} | p{pct(comp, r['composite']):5.1f} "
                  f"| PA {r['planet_agreement']:.3f} | {r['dominant_match']}/{r['dominant_divergence']}  ({desc})")
        return out

    pos = run(POSITIVE, "POSITIVE")
    neg = run(NEGATIVE, "NEGATIVE")

    pc = np.array([x["composite"] for x in pos]); nc = np.array([x["composite"] for x in neg])
    print(f"\n=== discrimination ===")
    print(f"  POSITIVE composite mean {pc.mean():.4f} | NEGATIVE mean {nc.mean():.4f} "
          f"| diff {pc.mean()-nc.mean():+.4f}")
    print(f"  null composite mean {comp.mean():.4f}  (labelled dyads vs random pairs)")
    # Permutation: are labelled dyads' composite different from random pairs?
    alllab = np.concatenate([pc, nc])
    obs = alllab.mean() - comp.mean()
    perm = np.array([rng.choice(comp, size=len(alllab)).mean() - comp.mean() for _ in range(5000)])
    p_lab = float((np.abs(perm) >= abs(obs)).mean())
    # positive vs negative permutation
    obs2 = pc.mean() - nc.mean()
    pool = np.concatenate([pc, nc]); L = len(pc)
    perm2 = []
    for _ in range(5000):
        sh = rng.permutation(pool)
        perm2.append(sh[:L].mean() - sh[L:].mean())
    p_pn = float((np.abs(perm2) >= abs(obs2)).mean())
    print(f"  labelled-vs-null   two-tailed p = {p_lab:.4f}")
    print(f"  positive-vs-negative two-tailed p = {p_pn:.4f}")

    # ---- Qualitative: read the Tension/Complementarity text against history ----
    print("\n=== QUALITATIVE: does the description name the real relationship? ===")
    for a, b, desc in [POSITIVE[0], POSITIVE[1], NEGATIVE[0], NEGATIVE[1]]:
        rep = build_relationship_report_payload(a, b)
        si = rep["data"]["structured_interpretation"]
        print(f"\n--- {a} + {b}  (HISTORY: {desc}) ---")
        for sec in si.get("sections", []):
            if sec.get("title") in ("Complementarity", "Tension Vectors", "Relationship Overview"):
                claims = sec.get("claims", [])
                texts = [c.get("statement", c) if isinstance(c, dict) else c for c in claims]
                print(f"  [{sec['title']}] " + " | ".join(str(t) for t in texts[:2]))


if __name__ == "__main__":
    main()
