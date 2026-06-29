"""Profile summary builders."""

from atlas.ciphers import run_all_ciphers
from atlas.export.json import graph_to_dict, signature_to_dict
from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph_builder import build_graph_from_kamea_path


KAMEA_NAMES = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]


def build_individual_profile_summary(name: str) -> dict:
    """Build one JSON-safe profile summary containing all 21 outputs."""
    cipher_results = run_all_ciphers(name)

    analyses = []

    for cipher_name, values in cipher_results.items():
        for kamea_name in KAMEA_NAMES:
            kamea = get_kamea(kamea_name)
            path = project_values_to_kamea(values, kamea_name)
            graph = build_graph_from_kamea_path(path)
            signature = build_topology_signature(graph)

            analyses.append(
                {
                    "cipher": cipher_name,
                    "kamea": kamea.key,
                    "planet": kamea.planet,
                    "kamea_size": kamea.size,
                    "raw_values": list(path.raw_values),
                    "reduced_values": list(path.reduced_values),
                    "coordinates": [
                        [row, col]
                        for row, col in path.coordinates
                    ],
                    "graph_summary": graph_to_dict(graph)["summary"],
                    "signature": signature_to_dict(signature),
                }
            )

    return {
        "name": name,
        "analysis_count": len(analyses),
        "ciphers": list(cipher_results.keys()),
        "kameas": KAMEA_NAMES,
        "analyses": analyses,
    }