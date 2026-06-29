import pandas as pd

from atlas.ablation.experiments import (
    AblationExperiment,
    build_feature_family_experiments,
    build_planet_experiments,
)
from atlas.ablation.harness import (
    apply_ablation,
    run_ablation_experiment,
)


def test_apply_ablation_removes_prefix_columns():
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "saturn_entropy": 0.1,
                "mars_entropy": 0.2,
            }
        ]
    )

    experiment = AblationExperiment(
        name="remove_saturn",
        description="Remove Saturn.",
        remove_prefixes=("saturn_",),
    )

    ablated, removed = apply_ablation(dataframe, experiment)

    assert "saturn_entropy" not in ablated.columns
    assert "saturn_entropy" in removed
    assert "mars_entropy" in ablated.columns


def test_build_default_experiments():
    assert build_planet_experiments()
    assert build_feature_family_experiments()


def test_run_ablation_experiment():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "saturn_entropy": 0.1, "mars_entropy": 0.1},
            {"name": "B", "saturn_entropy": 0.2, "mars_entropy": 0.2},
            {"name": "C", "saturn_entropy": 0.9, "mars_entropy": 0.9},
        ]
    )

    experiment = AblationExperiment(
        name="remove_saturn",
        description="Remove Saturn.",
        remove_prefixes=("saturn_",),
    )

    result = run_ablation_experiment(
        dataframe=dataframe,
        reference_profile="A",
        experiment=experiment,
        top_n=2,
    )

    assert result.reference_profile == "A"
    assert result.removed_columns == ["saturn_entropy"]
    assert result.summary["removed_column_count"] == 1