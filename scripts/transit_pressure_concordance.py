"""Do the systems react in concord to live transit pressure? (sanctioned edge)

The construction, made honest against the 1D finding: Kamea carries no planetary
meaning -- only a dynamic-axis structural claim (repetition/stabilization vs
disruption). The sanctioned concordance edge is Kamea-dynamic <-> Vedic-transit.
So this asks: under TODAY's transit, does each person's Kamea structural dynamic
agree with the Vedic-transit claim more than the null controls allow?

Subjects: library profiles with birth dates (birth time unknown -> noon, so the
Moon sign and thus gochara house-from-Moon are approximate; flagged). Kamea
expression = the birth-moment Moon trajectory (the one body with real dynamic at
an instant). Transit = sidereal Lahiri signs for 2026-07-28.

run_synthesis scores the authentic set against shuffled_systems / decoy_labels /
mismatched_pairs. The verdict is exceeds_every_control -- the bar the project
requires before any denotational claim counts.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone

import swisseph as swe

from atlas.validation.denotation.synthesis import SynthesisSubject, run_synthesis
from atlas.validation.denotation.kamea_denotation import kamea_expression
from atlas.validation.temporal_kamea import build_trajectory, canonical_spec

PROF_DIR = "output/library/profiles"
IV_DIR = "output/compiled/identity_vectors"
swe.set_sid_mode(swe.SIDM_LAHIRI)
W3D = canonical_spec("R1-W3D")
GRAHA_BODY = {"sun": swe.SUN, "moon": swe.MOON, "mars": swe.MARS, "mercury": swe.MERCURY,
              "jupiter": swe.JUPITER, "venus": swe.VENUS, "saturn": swe.SATURN}
TRANSIT_WHEN = "2026-07-28"
N_SUBJECTS = 80
KNOWN = {"michael": (datetime(1993, 8, 16, 22, 30, tzinfo=timezone.utc), "Michael Brockway")}


def sidereal_sign(jd, body):
    lon = swe.calc_ut(jd, body, swe.FLG_SIDEREAL)[0][0]
    return int(lon // 30) + 1


def birth_and_name(key):
    if key in KNOWN:
        dt, name = KNOWN[key]
        return dt, name, date(dt.year, dt.month, dt.day)
    ip = f"{PROF_DIR}/{key}/profile.intake.json"
    if not os.path.exists(ip):
        return None
    j = json.load(open(ip, encoding="utf-8"))
    bd = (j.get("birth_date") or "").strip()
    name = (j.get("name") or key).strip()
    try:
        y, m, d = (int(x) for x in bd.split("-"))
        return datetime(y, m, d, 12, tzinfo=timezone.utc), name, date(y, m, d)
    except (ValueError, TypeError):
        return None


def main():
    # Today's transit signs (same for everyone), sidereal Lahiri.
    tjd = swe.julday(2026, 7, 28, 12.0, swe.GREG_CAL)
    transit_signs = {g: sidereal_sign(tjd, b) for g, b in GRAHA_BODY.items()}
    print(f"transit signs (Lahiri, {TRANSIT_WHEN}): {transit_signs}\n")

    keys = sorted(f.replace(".identity-vector.json", "")
                  for f in os.listdir(IV_DIR) if f.endswith(".identity-vector.json"))
    keys = ["michael"] + keys  # ensure the user is in the set

    subjects = []
    for key in keys:
        if len(subjects) >= N_SUBJECTS:
            break
        info = birth_and_name(key)
        if info is None:
            continue
        dt, name, bd = info
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60, swe.GREG_CAL)
        moon_sign = sidereal_sign(jd, swe.MOON)
        try:
            traj = build_trajectory(dt, "moon", W3D)
            kx = kamea_expression(traj)
        except Exception:
            continue
        subjects.append(SynthesisSubject(
            subject_id=key, name=name, birth_date=bd,
            natal_moon_sign=moon_sign,
            graha_transit_signs=transit_signs,
            transit_when=TRANSIT_WHEN,
            kamea_expression=kx,
        ))

    print(f"subjects assembled: {len(subjects)} (birth time unknown -> noon; Moon sign approximate)\n")
    gap = run_synthesis(subjects, seed=20260728)
    d = gap.to_dict()
    print("=== agreement gap (Kamea-dynamic <-> Vedic-transit, under today's transit) ===")
    print(json.dumps(d, indent=2, default=str))
    ex = getattr(gap, "exceeds_every_control", None)
    print(f"\nexceeds_every_control = {ex}")
    print("Verdict:", "CONCORDANCE beyond null" if ex else
          "NO concordance beyond the null controls -- the systems react independently.")


if __name__ == "__main__":
    main()
