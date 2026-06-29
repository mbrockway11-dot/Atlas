from atlas.classification.meanings import (
    get_expression_meaning,
    get_functional_role_meaning,
    get_planetary_topology_meaning,
    get_structural_state_meaning,
)


def test_functional_role_meanings():
    meaning = get_functional_role_meaning("Driver")

    assert meaning["core_function"] == "Initiates change."
    assert meaning["topological_indicators"]


def test_hybrid_functional_role_meaning():
    meaning = get_functional_role_meaning("Driver-Amplifier Hybrid")

    assert meaning["core_function"] == "Hybrid function."
    assert len(meaning["components"]) == 2


def test_expression_meaning():
    meaning = get_expression_meaning("Radiating")

    assert "outward" in meaning["description"].lower()
    assert meaning["traits"]


def test_structural_state_meaning():
    meaning = get_structural_state_meaning("Stable")

    assert "coherence" in meaning["description"].lower()
    assert meaning["traits"]


def test_planetary_topology_meaning():
    meaning = get_planetary_topology_meaning("Saturn")

    assert "constraint" in meaning["topological_theme"].lower()