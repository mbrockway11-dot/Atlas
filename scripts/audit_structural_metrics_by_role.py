
"""Audit structural metrics by role."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles


FIELDS = [
    "motif_richness",
    "raw_node_count",
    "raw_edge_count",
    "truth_node_count",
    "truth_edge_count",
]


def main() -> None:
    groups = defaultdict(list)

    for key in list_saved_profiles():
        payload = compile_canonical_profile(key, force=False)
        cls = payload.get("classification", {})
        role = cls.get("structural_role", "missing")
        basis = cls.get("basis", {})
        groups[role].append((key, basis))

    for role, rows in sorted(groups.items()):
        print()
        print(f"# {role}")
        print(f"count: {len(rows)}")

        for field in FIELDS:
            vals = [float(b.get(field) or 0) for _k, b in rows]
            if not vals:
                continue
            print(
                f"{field}: min={min(vals):.3f} avg={mean(vals):.3f} max={max(vals):.3f}"
            )

        densities = [
            float(b.get("raw_edge_count") or 0) / max(float(b.get("raw_node_count") or 1), 1)
            for _k, b in rows
        ]
        truth_densities = [
            float(b.get("truth_edge_count") or 0) / max(float(b.get("truth_node_count") or 1), 1)
            for _k, b in rows
        ]

        print(
            f"raw_density: min={min(densities):.3f} avg={mean(densities):.3f} max={max(densities):.3f}"
        )
        print(
            f"truth_density: min={min(truth_densities):.3f} avg={mean(truth_densities):.3f} max={max(truth_densities):.3f}"
        )


if __name__ == "__main__":
    main()
