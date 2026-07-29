"""Precompute per-subject Kamea shape-flow (2D path_distance) over the Gauquelin
cohort, cached to npz so the by-profession test runs without re-sampling ephemeris."""
import csv
import numpy as np
from datetime import datetime
from atlas.validation.temporal_kamea import build_trajectory, canonical_spec

CACHE=("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad")
spec=canonical_spec("R1-W3D")
SPORT={"CYC","FOO","RUG","BOX","ATH","TEN","BAS","NAT","PEL","SKI","ESC","HAL","GYM",
       "HOC","EQU","LUT","TIR","BIL","AVR","GOL","MAR","HAN","GLA","VOI","CAN","VOL"}
CAT={**{c:"sports" for c in SPORT},"SC":"science","PH":"medicine","AVI":"aviation","AUT":"writers"}
bodies=["mars","sun","venus","mercury","moon"]
cats=[]; pd={b:[] for b in bodies}; rev={b:[] for b in bodies}; vx={b:[] for b in bodies}
for fn in ("A1","A2"):
    for r in csv.DictReader(open(f"{CACHE}/gauq_{fn}.csv",encoding="utf-8")):
        c=CAT.get(r.get("OCCU",""))
        if c is None: continue
        try: dt=datetime.fromisoformat(r["DATE"])
        except (ValueError,KeyError,TypeError): continue
        cats.append(c)
        for b in bodies:
            d=build_trajectory(dt,b,spec).diagnostics()
            pd[b].append(d["path_distance"]); rev[b].append(d["reversal_count"])
            vx[b].append(d["reduced_path_length"])
out={"cats":np.array(cats)}
for b in bodies:
    out[f"pd_{b}"]=np.array(pd[b],float); out[f"rev_{b}"]=np.array(rev[b],float)
    out[f"vx_{b}"]=np.array(vx[b],float)
np.savez(f"{CACHE}/kamea_flow.npz", **out)
print(f"cached {len(cats)} subjects x {len(bodies)} bodies -> kamea_flow.npz")
