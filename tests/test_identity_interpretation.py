from atlas.acf.builder import build_acf_profile
from atlas.interpretation import (
    identity_interpretation_to_dict,
    interpret_identity_vector,
)
from atlas.ive import build_identity_vector


def test_interpret_identity_vector():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf, normalization_mode="raw")

    interpretation = interpret_identity_vector(identity_vector)

    assert interpretation.name == "Michael Elvis Brockway"
    assert interpretation.summary_lines
    assert interpretation.global_interpretation
    assert interpretation.planet_interpretations
    assert interpretation.archetype_interpretations


def test_identity_interpretation_to_dict():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf, normalization_mode="raw")

    interpretation = interpret_identity_vector(identity_vector)
    data = identity_interpretation_to_dict(interpretation)

    assert data["name"] == "Michael Elvis Brockway"
    assert data["summary_lines"]
    assert data["planet_interpretations"]