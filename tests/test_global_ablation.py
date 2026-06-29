import pandas as pd

from atlas.ablation.experiments import AblationExperiment
from atlas.ablation.global_harness import (
    global_ablation_result_to_dict,
    run_global_ablation_experiment,
)


def test_run_global_ablation_experiment():
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

    result = run_global_ablation_experiment(
        dataframe=dataframe,
        experiment=experiment,
        top_n=2,
    )

    assert result.profile_count == 3
    assert result.profile_results
    assert result.summary["experiment_name"] == "remove_saturn"
    assert "importance_score" in result.summary


def test_global_ablation_result_to_dict():
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

    result = run_global_ablation_experiment(
        dataframe=dataframe,
        experiment=experiment,
        top_n=2,
    )

    data = global_ablation_result_to_dict(result)

    assert data["summary"]["experiment_name"] == "remove_saturn"
    assert data["profile_count"] == 3