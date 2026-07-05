
"""Audit Atlas structural role distribution."""

from __future__ import annotations

from collections import Counter, defaultdict

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles


def main() -> None:
    keys = list_saved_profiles()

    roles = Counter()
    subtypes = Counter()
    topology = Counter()
    motifs = Counter()
    axes = Counter()
    resonance = Counter()

    role_examples = defaultdict(list)

    for key in keys:
        payload = compile_canonical_profile(key, force=False)
        classification = payload.get("classification", {})
        basis = classification.get("basis", {})

        role = classification.get("structural_role", "missing")
        subtype = classification.get("structural_subtype", "missing")

        roles[role] += 1
        subtypes[subtype] += 1
        topology[basis.get("topology_class", "missing")] += 1
        motifs[basis.get("dominant_motif", "missing")] += 1
        axes[basis.get("dominant_topology_axis", "missing")] += 1
        resonance[basis.get("resonance_class", "missing")] += 1

        if len(role_examples[role]) < 10:
            role_examples[role].append(key)

    print("# Structural Classification Audit")
    print()
    print(f"profiles: {len(keys)}")
    print()

    print("## Roles")
    for key, value in roles.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Subtypes")
    for key, value in subtypes.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Topology Classes")
    for key, value in topology.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Dominant Motifs")
    for key, value in motifs.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Dominant Axes")
    for key, value in axes.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Resonance Classes")
    for key, value in resonance.most_common():
        print(f"- {key}: {value}")

    print()
    print("## Role Examples")
    for role, examples in role_examples.items():
        print(f"- {role}: {', '.join(examples)}")


if __name__ == "__main__":
    main()
