from atlas.acf.builder import build_acf_profile
from atlas.explanation import (
    explain_identity_vector,
    explain_metric,
    explain_metric_value,
)
from atlas.ive import build_identity_vector


def test_explain_metric():
    assert "distributed" in explain_metric("planet_balance_index")


def test_explain_metric_value():
    text = explain_metric_value("graph_coherence", 0.8)

    assert "high" in text
    assert "graph_coherence" in text


def test_explain_identity_vector():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf, normalization_mode="raw")

    lines = explain_identity_vector(identity_vector)

    assert len(lines) >= 5
    assert any("Identity Vector" in line for line in lines)