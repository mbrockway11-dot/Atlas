
"""Action Engine voting."""

from __future__ import annotations

from atlas.investment.action_engine.votes import VOTE_WEIGHTS, empty_score


def aggregate_votes(position_id: str, votes: list[dict]) -> dict:
    scores = empty_score()

    for vote in votes:
        source = vote.get("source")
        action = vote.get("action")
        confidence = float(vote.get("confidence") or 0.0)
        weight = VOTE_WEIGHTS.get(source, 0.05)

        if action not in scores:
            action = "HOLD"

        scores[action] += weight * confidence

    total = sum(scores.values())

    if total <= 0:
        final_action = "HOLD"
        final_confidence = 0.0
    else:
        final_action = max(scores, key=scores.get)
        final_confidence = scores[final_action] / total

    return {
        "position_id": position_id,
        "final_action": final_action,
        "final_confidence": round(float(final_confidence), 6),
        "scores": {k: round(float(v), 6) for k, v in scores.items()},
        "votes": votes,
    }
