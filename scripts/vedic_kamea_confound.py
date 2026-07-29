"""Stress-test the tiny kamea<->Vedic correlation (r=0.018, p=0.02).

Two questions decide whether it means anything:
  1. STABILITY -- does p stay low across independent random subsamples, or was
     0.02 a lucky draw?
  2. SEASONALITY CONFOUND -- Sun/Mercury/Venus track birth MONTH; birth months
     are not uniform across cultures, and culture drives naming (hence kamea).
     So the correlation could be a birth-season x culture artifact. Mars barely
     tracks season (2-yr cycle). If the effect lives only in the seasonal trio
     and Mars-only is null, it is the confound. We also correlate kamea directly
     against birth day-of-year distance -- the seasonal channel itself.

Full-sample Mantel (n=all) via scipy pdist for the stable r; subsample multi-seed
for the stability check. Same loading as vedic_kamea_correlation.py.
"""

from __future__ import annotations

import json
import os

import numpy as np
import swisseph as swe

IV_DIR = "output/compiled/identity_vectors"
PROF_DIR = "output/library/profiles"
swe.set_sid_mode(swe.SIDM_LAHIRI)
BODIES = {"Sun": swe.SUN, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS}


def load():
    files = sorted(f for f in os.listdir(IV_DIR) if f.endswith(".identity-vector.json"))
    d0 = json.load(open(f"{IV_DIR}/{files[0]}", encoding="utf-8"))
    groups = sorted({(v["cipher"], v["planet"]) for v in d0["vectors"]})
    feats = sorted(d0["vectors"][0]["features"].keys())
    K, LON, DOY = [], [], []
    for fn in files:
        key = fn.replace(".identity-vector.json", "")
        ip = f"{PROF_DIR}/{key}/profile.intake.json"
        if not os.path.exists(ip):
            continue
        bd = (json.load(open(ip, encoding="utf-8")).get("birth_date") or "").strip()
        if not (len(bd) == 10 and bd[4] == "-" and bd[:4].isdigit() and bd[:4] != "0000"):
            continue
        iv = json.load(open(f"{IV_DIR}/{fn}", encoding="utf-8"))
        bg = {(v["cipher"], v["planet"]): v["features"] for v in iv["vectors"]}
        if any(g not in bg for g in groups):
            continue
        row = [float(bg[g][f]) for g in groups for f in feats]
        y, m, dd = (int(x) for x in bd.split("-"))
        jd = swe.julday(y, m, dd, 12.0, swe.GREG_CAL)
        lon = [swe.calc_ut(jd, c, swe.FLG_SIDEREAL)[0][0] for c in BODIES.values()]
        K.append(row)
        LON.append(lon)
        DOY.append((jd - swe.julday(y, 1, 1, 12.0, swe.GREG_CAL)) / 365.25 * 360.0)
    return np.array(K), np.array(LON), np.array(DOY), list(BODIES)


def kamea_D(Kz: np.ndarray) -> np.ndarray:
    G = Kz @ Kz.T
    sq = np.diag(G).copy()
    D2 = sq[:, None] + sq[None, :] - 2.0 * G
    np.maximum(D2, 0.0, out=D2)
    return np.sqrt(D2)


def circ_D(A: np.ndarray) -> np.ndarray:
    n, k = A.shape
    D = np.zeros((n, n))
    for c in range(k):
        a = A[:, c]
        diff = np.abs(a[:, None] - a[None, :]) % 360.0
        D += np.minimum(diff, 360.0 - diff)
    return D / k


def mantel(Dk: np.ndarray, Dv: np.ndarray, iu, n: int, perms: int, seed: int):
    dk = Dk[iu]
    obs = np.corrcoef(dk, Dv[iu])[0, 1]
    if perms == 0:
        return obs, None
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(perms):
        p = rng.permutation(n)
        if np.corrcoef(dk, Dv[np.ix_(p, p)][iu])[0, 1] >= obs:
            cnt += 1
    return obs, (cnt + 1) / (perms + 1)


def main():
    K, LON, DOY, names = load()
    n = len(K)
    print(f"loaded n={n}; fast bodies={names}\n")
    sd = K.std(axis=0)
    Kz = (K[:, sd > 0] - K[:, sd > 0].mean(axis=0)) / sd[sd > 0]

    Dk = kamea_D(Kz)
    iu = np.triu_indices(n, k=1)

    def full(cols, label, perms):
        Dv = circ_D(LON[:, cols])
        r, p = mantel(Dk, Dv, iu, n, perms, 7)
        ps = f"p={p:.4f}" if p is not None else "p=--"
        flag = "<-- p<0.05" if (p is not None and p < 0.05) else ""
        print(f"  {label:26} r={r:+.4f}  {ps}  {flag}")

    print(f"=== FULL-SAMPLE Mantel (n={n}) ===")
    full([0, 1, 2, 3], "all fast (Sun,Me,Ve,Ma)", 499)
    full([0], "Sun only (seasonal)", 0)
    full([1, 2], "Mercury+Venus (seasonal)", 0)
    full([3], "MARS only (season-free)", 499)
    full([1, 2, 3], "Me+Ve+Mars (no Sun)", 0)

    Dv_doy = circ_D(DOY.reshape(-1, 1))
    r, p = mantel(Dk, Dv_doy, iu, n, 499, 7)
    print(f"  {'kamea vs day-of-year':26} r={r:+.4f}  p={p:.4f}  {'<-- p<0.05' if p < 0.05 else ''}")

    print(f"\n=== STABILITY: all-fast Mantel across 6 subsamples (n=600, 1999 perms) ===")
    for s in range(6):
        rng = np.random.default_rng(100 + s)
        idx = rng.choice(n, size=600, replace=False)
        dk = kamea_D(Kz[idx])
        dv = circ_D(LON[idx][:, [0, 1, 2, 3]])
        iu2 = np.triu_indices(600, k=1)
        r, p = mantel(dk, dv, iu2, 600, 1999, 200 + s)
        print(f"  seed {s}: r={r:+.4f}  p={p:.4f}  {'*' if p < 0.05 else ''}")

    print("\nRead: if 'all fast' is p<0.05 but 'Mars only' is null while the seasonal "
          "columns and day-of-year carry the signal, the correlation is a "
          "birth-season x culture confound, not a real name<->chart link.")


if __name__ == "__main__":
    main()
