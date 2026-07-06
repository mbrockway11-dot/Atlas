
from atlas.autonomous.memory import (
    create_research_memory,
    remember_evidence,
    remember_experiment,
    remember_hypothesis,
    search_memory,
)


def test_research_memory_stores_items():
    memory = create_research_memory()

    memory = remember_experiment(memory, {"experiment_id": "exp1", "question": "recovery"})
    memory = remember_evidence(memory, {"evidence_id": "ev1", "question": "recovery"})
    memory = remember_hypothesis(memory, {"hypothesis_id": "hyp1", "hypothesis": "recovery matters"})

    assert len(memory["experiments"]) == 1
    assert len(memory["evidence"]) == 1
    assert len(memory["hypotheses"]) == 1
    assert search_memory(memory, "recovery")["result_count"] >= 1
