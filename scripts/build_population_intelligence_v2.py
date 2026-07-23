
"""Build Atlas Population Intelligence v2 corpus summary."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.services.profile_path_service import PROJECT_ROOT


OUT = PROJECT_ROOT / "output" / "population" / "population_intelligence_v2.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    profiles = []
    roles = Counter()
    topologies = Counter()
    subtypes = Counter()

    role_metrics = defaultdict(list)

    for key in list_saved_profiles():
        payload = compile_canonical_profile(key, force=False)

        cls = payload.get("classification", {})
        basis = cls.get("basis", {})
        graph = payload.get("graph", {}).get("summary", {})

        role = cls.get("structural_role", "missing")
        subtype = cls.get("structural_subtype", "missing")
        topology = basis.get("topology_class", "missing")

        roles[role] += 1
        subtypes[subtype] += 1
        topologies[topology] += 1

        record = {
            "profile_key": key,
            "name": cls.get("name", key),
            "role": role,
            "subtype": subtype,
            "topology_class": topology,
            "dominant_axis": basis.get("dominant_topology_axis"),
            "dominant_motif": basis.get("dominant_motif"),
            "resonance_class": basis.get("resonance_class"),
            "dominant_resonance_axis": basis.get("dominant_resonance_axis"),
            "motif_richness": float(basis.get("motif_richness") or 0),
            "raw_nodes": int(basis.get("raw_node_count") or 0),
            "raw_edges": int(basis.get("raw_edge_count") or 0),
            "truth_nodes": int(basis.get("truth_node_count") or 0),
            "truth_edges": int(basis.get("truth_edge_count") or 0),
            "raw_density": density(basis.get("raw_edge_count"), basis.get("raw_node_count")),
            "truth_density": density(basis.get("truth_edge_count"), basis.get("truth_node_count")),
            "confidence": cls.get("confidence", {}),
        }

        profiles.append(record)
        role_metrics[role].append(record)

    output = {
        "version": "2.0",
        "profile_count": len(profiles),
        "role_distribution": dict(roles.most_common()),
        "subtype_distribution": dict(subtypes.most_common()),
        "topology_distribution": dict(topologies.most_common()),
        "role_summaries": {
            role: summarize_role(rows)
            for role, rows in sorted(role_metrics.items())
        },
        "profiles": profiles,
    }

    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"wrote {OUT}")
    print(f"profiles: {len(profiles)}")
    print("roles:")
    for role, count in roles.most_common():
        print(f"- {role}: {count}")


def density(edges, nodes) -> float:
    try:
        return round(float(edges or 0) / max(float(nodes or 1), 1), 6)
    except Exception:
        return 0.0


def summarize_role(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "examples": [row["profile_key"] for row in rows[:10]],
        "avg_motif_richness": avg(row["motif_richness"] for row in rows),
        "avg_raw_density": avg(row["raw_density"] for row in rows),
        "avg_truth_density": avg(row["truth_density"] for row in rows),
        "avg_raw_nodes": avg(row["raw_nodes"] for row in rows),
        "avg_raw_edges": avg(row["raw_edges"] for row in rows),
        "avg_truth_nodes": avg(row["truth_nodes"] for row in rows),
        "avg_truth_edges": avg(row["truth_edges"] for row in rows),
    }


def avg(values) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    return round(mean(vals), 6)


if __name__ == "__main__":
    main()
