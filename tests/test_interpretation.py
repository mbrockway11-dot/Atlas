from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.interpretation.rules import interpret_signature
from atlas.profiles.summary import build_individual_profile_summary
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import TopologyGraph


def test_interpret_signature_returns_lines():
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
    lines = interpret_signature(signature)

    assert len(lines) == 5
    assert any("driver" in line.lower() for line in lines)
    assert any("reciprocal" in line.lower() for line in lines)


def test_interpret_profile_summary():
    summary = build_individual_profile_summary("Michael Elvis Brockway")
    interpretation = interpret_profile_summary(summary)

    assert interpretation.name == "Michael Elvis Brockway"
    assert interpretation.analysis_count == 21
    assert interpretation.dominant_patterns
    assert interpretation.dominant_motifs
    assert interpretation.strongest_driver
    assert interpretation.strongest_amplifier
    assert interpretation.strongest_regulator
    assert interpretation.summary_lines


def test_profile_interpretation_to_dict():
    summary = build_individual_profile_summary("Michael Elvis Brockway")
    interpretation = interpret_profile_summary(summary)

    data = profile_interpretation_to_dict(interpretation)

    assert data["name"] == "Michael Elvis Brockway"
    assert data["analysis_count"] == 21
    assert "dominant_patterns" in data
    assert "dominant_motifs" in data
    assert "summary_lines" in data