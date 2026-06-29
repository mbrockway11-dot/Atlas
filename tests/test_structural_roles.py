from collections import Counter

from atlas.measurement.structural_roles import (
    STRUCTURAL_ROLES,
    measure_structural_roles,
)


def test_measure_structural_roles_returns_all_roles():
    path = [
        (0, 0),
        (0, 1),
        (0, 0),
        (1, 1),
        (1, 1),
        (2, 2),
    ]

    nodes = Counter(path)
    edges = Counter(zip(path[:-1], path[1:]))

    measurement = measure_structural_roles(
        path=path,
        nodes=nodes,
        edges=edges,
    )

    assert set(measurement.roles) == set(STRUCTURAL_ROLES)

    for value in measurement.roles.values():
        assert 0.0 <= value <= 1.0


def test_oscillator_detects_aba_pattern():
    path = [
        (0, 0),
        (0, 1),
        (0, 0),
        (0, 1),
        (0, 0),
    ]

    nodes = Counter(path)
    edges = Counter(zip(path[:-1], path[1:]))

    measurement = measure_structural_roles(
        path=path,
        nodes=nodes,
        edges=edges,
    )

    assert measurement.roles["oscillator"] > 0.0