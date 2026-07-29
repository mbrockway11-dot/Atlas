"""A person's structural shape, and structural distance between people.

The R2 comparison object: reduce each person to their Kamea shape vector -- the
graph invariants of their name's traversal across the seven squares -- then
compare people by structural distance, not by sigil appearance or by any label.
Meaning is not assigned; structure is measured and compared.

    .venv/Scripts/python.exe scripts/person_shape_vectors.py
"""

from __future__ import annotations

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.projection import project_values_to_all_kameas
from atlas.kamea.shape_vector import shape_vector, AXES
from atlas.kamea.squares import KAMEAS

NAMES = [
    "Michael Elvis Brockway",
    "Nikola Tesla",
    "Thomas Edison",
    "Thomas Jefferson",
    "Alexander Hamilton",
]
BODIES = sorted(KAMEAS)


def person_shape(name):
    values = english_ordinal_sequence(name)
    paths = project_values_to_all_kameas(values, use_planetary_transform=True)
    per_body = {b: shape_vector(paths[b].coordinates) for b in BODIES}
    vector = np.concatenate([np.array(per_body[b].axis_vector()) for b in BODIES])
    return per_body, vector


def main():
    shapes = {name: person_shape(name) for name in NAMES}

    lead = NAMES[0]
    per_body, _ = shapes[lead]
    print(f"=== {lead}: shape vector per square (name traversal, ordinal cipher) ===")
    print(f"{'body':8} " + " ".join(f"{a[:5]:>6}" for a in AXES) + "  nodes cyc")
    for b in BODIES:
        sv = per_body[b]
        print(f"{b:8} " + " ".join(f"{getattr(sv, a):>6.2f}" for a in AXES)
              + f"   {sv.nodes:>3} {sv.cyclomatic_number:>3}"
              + ("  (degenerate)" if sv.degenerate else ""))

    print("\n=== structural distance between people (56-D shape, Euclidean) ===")
    names = list(shapes)
    V = np.stack([shapes[n][1] for n in names])
    D = np.sqrt(((V[:, None, :] - V[None, :, :]) ** 2).sum(axis=2))
    short = [n.split()[0] + " " + n.split()[-1] if len(n.split()) > 2 else n for n in names]
    header = "".join(f"{s.split()[-1][:8]:>9}" for s in names)
    print(f"{'':16}{header}")
    for i, n in enumerate(names):
        row = "".join(f"{D[i, j]:>9.2f}" for j in range(len(names)))
        print(f"{short[i]:16}{row}")

    print("\n=== nearest structural neighbour (who shares the most shape) ===")
    for i, n in enumerate(names):
        order = np.argsort(D[i])
        j = order[1]  # skip self
        print(f"  {n:24} -> {names[j]:24} (dist {D[i, j]:.2f})")

    print("\nThis is what an empirical phase compares: structural signatures, not"
          "\nmeanings. Clustering here groups by graph shape alone.")


if __name__ == "__main__":
    main()
