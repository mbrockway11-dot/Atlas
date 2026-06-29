from atlas.acf.builder import build_acf_profile
from atlas.ive import build_identity_vector
from atlas.ontology import (
    explain_structural_role,
    rank_archetypes,
    synthesize_identity_ontology,
)


def test_rank_archetypes():
    features = {
        "hub_ratio": 0.9,
        "graph_coherence": 0.8,
        "node_survival_auc": 0.7,
        "bridge_ratio": 0.2,
        "articulation_ratio": 0.2,
        "edge_survival_auc": 0.2,
    }

    ranked = rank_archetypes(features)

    assert ranked
    assert ranked[0]["score"] >= ranked[-1]["score"]


def test_explain_structural_role():
    explanation = explain_structural_role("hub")

    assert "connectivity" in explanation


def test_synthesize_identity_ontology():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf, normalization_mode="raw")

    ontology = synthesize_identity_ontology(identity_vector)

    assert ontology["name"] == "Michael Elvis Brockway"
    assert ontology["global_archetypes"]
    assert ontology["planet_archetypes"]
    assert ontology["summary"]