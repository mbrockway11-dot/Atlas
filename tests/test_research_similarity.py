import pytest

from atlas.research.similarity import (
    absolute_distance,
    cosine_similarity,
    mean_absolute_distance,
    similarity_from_distance,
)


def test_cosine_similarity_identical():
    similarity = cosine_similarity(
        {"a": 1.0, "b": 2.0},
        {"a": 1.0, "b": 2.0},
    )

    assert similarity == pytest.approx(1.0, abs=1e-12)


def test_absolute_distance():
    distance = absolute_distance(
        {"a": 1.0},
        {"a": 0.25, "b": 0.5},
    )

    assert distance["a"] == pytest.approx(0.75)
    assert distance["b"] == pytest.approx(0.5)


def test_mean_absolute_distance():
    distance = mean_absolute_distance(
        {"a": 1.0},
        {"a": 0.0},
    )

    assert distance == pytest.approx(1.0)


def test_similarity_from_distance():
    assert similarity_from_distance(0.25) == pytest.approx(0.75)
    assert similarity_from_distance(2.0) == pytest.approx(0.0)