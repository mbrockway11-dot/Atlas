"""Test whether the normalized Kamea shape-flow discriminates profession.

Loads the cached per-subject 2D path_distance (and reversals / vertices) and,
per (profession, body), tests the cohort mean against the analytic null for a
subgroup mean (normal approximation, finite-population correction). Reports the
full grid with a Bonferroni threshold, so a lone p<0.05 among many is not read
as a hit.
"""
import math
import numpy as np

CACHE=("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad")
d=np.load(f"{CACHE}/kamea_flow.npz", allow_pickle=True)
cats=d["cats"]; n=len(cats)
bodies=["mars","sun","venus","mercury","moon"]
profs=["sports","aviation","science","medicine","writers"]


def two_sided_p(z: float) -> float:
    return 2*(1-0.5*(1+math.erf(abs(z)/math.sqrt(2))))


def grid(prefix: str, label: str) -> list[float]:
    print(f"\n=== {label} by profession x body (analytic p) ===")
    print(f"{'body':9}{'pool':>8}  " + "".join(f"{p[:6]:>13}" for p in profs))
    allp=[]
    for b in bodies:
        f=d[f"{prefix}_{b}"].astype(float); pool=f.mean(); var=f.var(ddof=1)
        row=f"{b:9}{pool:>8.2f}  "
        for c in profs:
            m=f[cats==c]; size=len(m); auth=m.mean()
            se=math.sqrt(var/size*(n-size)/(n-1)) if size>1 and var>0 else float("inf")
            z=(auth-pool)/se if se>0 and math.isfinite(se) else 0.0
            p=two_sided_p(z); allp.append(p)
            star="*" if p<0.05 else " "
            row+=f"{auth:>7.2f}{star}p{p:<3.2f}"[:13]
        print(row)
    return allp


allp=grid("pd","2D path-distance (flow)")+grid("rev","reversals (folding)")
allp=np.array(allp); bonf=0.05/len(allp)
print(f"\n{len(allp)} tests | #p<0.05={(allp<0.05).sum()} (chance ~{0.05*len(allp):.1f})"
      f" | Bonferroni a={bonf:.4f} | #p<Bonf={(allp<bonf).sum()} | min p={allp.min():.4f}")
print("Interpretation: if #p<0.05 is around the chance count and none beats "
      "Bonferroni, the shape-flow does not discriminate profession.")
