"""Export the 3D visit paths (x, y, z=visit_depth) for the kamea rivers.

The z-axis is real: visit_history assigns each revisit of a node an increasing
visit_depth. So a cell the river returns to rises into a tower. This dumps, per
person per body, the visit sequence in 3D plus the per-cell tower heights.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from atlas.validation.temporal_kamea import (
    build_trajectory, canonical_spec, CLASSICAL_BODIES, KAMEAS,
)
from atlas.kamea.visit_history import build_node_visit_history

PROF_DIR = "output/library/profiles"
BODIES = sorted(CLASSICAL_BODIES)
WINDOWS = {w: canonical_spec(f"R1-{w}") for w in ("W3D", "W30D", "W180D", "W1Y")}
KNOWN = {"michael": datetime(1993, 8, 16, 22, 30, tzinfo=timezone.utc)}
PEOPLE = {"Michael Brockway": "michael", "Nikola Tesla": "nikola_tesla",
          "Thomas Edison": "thomas_edison", "Thomas Jefferson": "thomas_jefferson",
          "Alexander Hamilton": "alexander_hamilton"}
OUT = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers_3d.json")


def birth_instant(key):
    if key in KNOWN:
        return KNOWN[key]
    ip = f"{PROF_DIR}/{key}/profile.intake.json"
    if not os.path.exists(ip):
        return None
    bd = (json.load(open(ip, encoding="utf-8")).get("birth_date") or "").strip()
    try:
        y, m, d = (int(x) for x in bd.split("-"))
        return datetime(y, m, d, 12, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def main():
    out = {}
    for name, key in PEOPLE.items():
        dt = birth_instant(key)
        if dt is None:
            continue
        out[name] = {}
        for body in BODIES:
            out[name][body] = {"grid": KAMEAS[body].size, "windows": {}}
            for win, spec in WINDOWS.items():
                t = build_trajectory(dt, body, spec)
                vh = build_node_visit_history(t.path)
                visits = [[v["coordinate"][0], v["coordinate"][1], v["visit_depth"]]
                          for v in vh["visits"]]
                towers = {}
                for x, y, z in visits:
                    towers[f"{x},{y}"] = max(towers.get(f"{x},{y}", 0), z + 1)
                out[name][body]["windows"][win] = {
                    "visits": visits,
                    "towers": towers,
                    "max_depth": vh["max_depth"],
                    "path_distance": t.diagnostics()["path_distance"],
                }
    with open(OUT, "w", encoding="utf-8") as h:
        json.dump(out, h, separators=(",", ":"))
    print(f"wrote {OUT} for {list(out)}")
    # quick sanity: how z-depth (stacking) trades for flow as the window opens
    for body in ("saturn", "moon"):
        row = out["Michael Brockway"][body]["windows"]
        depths = {w: row[w]["max_depth"] for w in row}
        print(f"  Michael {body}: max_depth by window = {depths}")


if __name__ == "__main__":
    main()
