from atlas.invariant.features import extract_invariant_features
from atlas.invariant.subtype import (
    classify_invariant_subtype,
    invariant_subtype_to_dict,
    score_invariant_subtypes,
)


def test_score_invariant_subtypes():
    features = extract_invariant_features(
        [(0, 0), (1, 1), (2, 2)],
        3,
    )

    scores = score_invariant_subtypes(features)

    assert "Axial" in scores
    assert "Compressive" in scores
    assert "Expansive" in scores
    assert "Diffuse" in scores
    assert "Fragmented" in scores
    assert "Balanced" in scores
    assert "Directive" in scores
    assert "Radial" in scores

    for score in scores.values():
        assert 0.0 <= score <= 1.0


def test_classify_invariant_subtype():
    features = extract_invariant_features(
        [(0, 0), (1, 1), (2, 2)],
        3,
    )

    subtype = classify_invariant_subtype(features)

    assert subtype.primary_type
    assert subtype.secondary_modifier
    assert subtype.scores


def test_invariant_subtype_to_dict():
    features = extract_invariant_features(
        [(0, 0), (1, 1), (2, 2)],
        3,
    )

    subtype = classify_invariant_subtype(features)
    data = invariant_subtype_to_dict(subtype)

    assert "primary_type" in data
    assert "secondary_modifier" in data
    assert "scores" in data
    assert "ranked" in data