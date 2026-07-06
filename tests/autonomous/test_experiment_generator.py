
from atlas.autonomous.experiment_generator import (
    build_experiment_plan,
    generate_experiment_questions,
    rank_experiment_questions,
)


def test_experiment_generation_and_ranking():
    questions = generate_experiment_questions(
        variables=["a", "b", "c"],
        max_questions=10,
    )

    assert len(questions) == 3

    ranked = rank_experiment_questions(questions)
    assert ranked[0]["rank_score"] >= ranked[-1]["rank_score"]

    plan = build_experiment_plan(
        variables=["a", "b", "c"],
        top_n=2,
    )

    assert plan["success"] is True
    assert plan["selected_count"] == 2
