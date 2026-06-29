import csv

from atlas.export.csv import export_signature_csv
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import TopologyGraph


def test_export_signature_csv(tmp_path):
    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(((0, 0), (1, 1)), ((1, 1), (0, 0))),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={
            ((0, 0), (1, 1)): 1,
            ((1, 1), (0, 0)): 1,
        },
    )

    signature = build_topology_signature(graph)

    output_path = tmp_path / "signature.csv"
    export_signature_csv(signature, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["node_count"] == "2"
    assert rows[0]["edge_count"] == "2"
    assert rows[0]["dominant_pattern"] == "reciprocal"
    assert rows[0]["reciprocity_level"] == "high"
    assert rows[0]["dominant_motif"] == "chains"
    assert rows[0]["reciprocal_pairs"] == "1"