
from atlas.autonomous.scheduler import (
    build_schedule,
    create_research_queue,
    enqueue_many,
)


def test_scheduler_queue_and_schedule():
    queue = create_research_queue()
    questions = [
        {
            "question_id": "q1",
            "question": "Does A relate to B?",
            "x_field": "a",
            "y_field": "b",
            "kind": "numeric_correlation",
            "rank_score": 0.9,
        }
    ]

    queue = enqueue_many(queue, questions)
    schedule = build_schedule(queue, max_items=1)

    assert schedule["success"] is True
    assert schedule["scheduled_count"] == 1
    assert schedule["scheduled_items"][0]["status"] == "scheduled"
