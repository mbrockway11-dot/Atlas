"""The normalized composite shape as the canonical structural fingerprint.

Per person: one size-independent eight-axis fingerprint aggregated across all
seven planetary operators, its decomposition (which planet drives each axis), and
distances in shape space -- the next-phase object of analysis.

    .venv/Scripts/python.exe scripts/composite_shape_demo.py
"""

from __future__ import annotations

import numpy as np

from atlas.kamea.composite_shape import composite_shape_from_name, composite_distance
from atlas.kamea.composite_shape import PLANET_ORDER
from atlas.kamea.shape_vector import AXES

NAMES = [
    "Michael Elvis Brockway",
    "Nikola Tesla",
    "Thomas Edison",
    "Thomas Jefferson",
    "Alexander Hamilton",
    "Ada Lovelace",
    "Marie Curie",
]


def main():
    shapes = {n: composite_shape_from_name(n) for n in NAMES}

    print("=== composite fingerprint per person (8 normalized axes) ===")
    print(f"{'person':24} " + " ".join(f"{a[:5]:>6}" for a in AXES))
    for n in NAMES:
        cs = shapes[n]
        print(f"{n:24} " + " ".join(f"{cs.composite[a]:>6.2f}" for a in AXES))

    lead = "Nikola Tesla"
    cs = shapes[lead]
    print(f"\n=== decomposition for {lead}: which planet drives each axis ===")
    print(f"{'axis':14} " + " ".join(f"{p[:3]:>5}" for p in PLANET_ORDER) + "   dominant")
    for a in AXES:
        shares = cs.contributions[a]
        row = " ".join(f"{shares[p]:>5.2f}" for p in PLANET_ORDER)
        print(f"{a:14} {row}   {cs.dominant_planet(a)}")

    print("\n=== distance in shape space (composite, Euclidean) ===")
    names = list(shapes)
    D = np.array([[composite_distance(shapes[a], shapes[b]) for b in names] for a in names])
    print(f"{'':22}" + "".join(f"{n.split()[-1][:7]:>8}" for n in names))
    for i, n in enumerate(names):
        print(f"{n:22}" + "".join(f"{D[i, j]:>8.2f}" for j in range(len(names))))

    print("\n=== nearest structural neighbour ===")
    for i, n in enumerate(names):
        j = np.argsort(D[i])[1]
        print(f"  {n:24} -> {names[j]:24} (dist {D[i, j]:.3f})")


if __name__ == "__main__":
    main()
