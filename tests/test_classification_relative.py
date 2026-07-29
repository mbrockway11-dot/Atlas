"""Population-relative classification: roles/states must not collapse.

The pre-fix classifiers compared driver/amplifier/regulator on non-overlapping
scales, so every profile came out Regulator + Adaptive. These lock in that the
labels are now decided relative to the corpus and actually vary.
"""

from atlas.classification.functional_role import classify_functional_role
from atlas.classification.structural_state import classify_structural_state
from atlas.signatures.topology_signature import TopologySignature


def _sig(driver, amplifier, regulator, symmetry=0.29, component_count=1):
    """A TopologySignature with the classification-relevant scores set."""
    return TopologySignature(
        driver=driver, amplifier=amplifier, regulator=regulator,
        node_count=5, edge_count=6, edge_density=0.06, symmetry=symmetry,
        component_count=component_count, entropy=0.9,
        dominant_pattern="radiating", branching_level="low",
        reciprocity_level="low", compression_level="low",
        dominant_motif="chains", motif_density=0.5, chains=3, hubs=1, loops=0,
        bridges=0, dead_ends=0, reciprocal_pairs=0, isolated_nodes=0,
    )


# Corpus means (from the default calibration): driver .082, amplifier .490,
# regulator .726. Regulator is the raw-max for BOTH of these, so the old
# argmax would have labelled both "Regulator".
_DRIVER_LEANING = _sig(driver=0.12, amplifier=0.45, regulator=0.68)
_REGULATOR_LEANING = _sig(driver=0.07, amplifier=0.47, regulator=0.90)


def test_role_is_population_relative_not_a_constant():
    driver_role = classify_functional_role(_DRIVER_LEANING).role
    regulator_role = classify_functional_role(_REGULATOR_LEANING).role
    # Raw regulator is the largest score in both, so the old code returned
    # Regulator for both. Relative scoring must separate them.
    assert driver_role == "Driver"
    assert regulator_role == "Regulator"
    assert driver_role != regulator_role


def test_role_carries_z_scores_and_basis():
    role = classify_functional_role(_DRIVER_LEANING)
    assert role.driver_z > role.regulator_z  # relatively high on driver
    assert role.basis.startswith("population-relative")


def test_state_stable_when_regulation_and_symmetry_high():
    state = classify_structural_state(_sig(driver=0.08, amplifier=0.49,
                                           regulator=0.85, symmetry=0.55))
    assert state.state == "Stable"


def test_state_fragile_when_regulation_and_symmetry_low():
    state = classify_structural_state(_sig(driver=0.08, amplifier=0.49,
                                           regulator=0.64, symmetry=0.10))
    assert state.state == "Fragile"


def test_state_adaptive_near_the_corpus_centre():
    state = classify_structural_state(_sig(driver=0.082, amplifier=0.490,
                                           regulator=0.726, symmetry=0.293))
    assert state.state == "Adaptive"
    assert state.basis.startswith("population-relative")


def test_fragmentation_still_wins():
    state = classify_structural_state(_sig(driver=0.08, amplifier=0.49,
                                           regulator=0.85, symmetry=0.55,
                                           component_count=3))
    assert state.state == "Fragmented"
