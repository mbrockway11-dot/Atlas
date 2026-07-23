"""Event/control-window construction and falsification randomizations."""

from __future__ import annotations

from datetime import date, timedelta
import random
from typing import Any


CONTROL_SHIFTS = (-364, -182, 182, 364)


def build_event_control_windows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    events = {row["event_id"]: row for row in registry.get("historical_events", [])}
    known_event_dates = {date.fromisoformat(row["start_date"]) for row in events.values()}
    windows: list[dict[str, Any]] = []
    for participation in registry.get("profile_participation", []):
        event = events[participation["event_id"]]
        anchor = date.fromisoformat(event["start_date"])
        base = {
            "profile_key": participation["profile_key"],
            "event_id": event["event_id"],
            "event_family": event.get("event_family"),
            "outcome_category": participation.get("outcome_category"),
            "outcome_direction": participation.get("outcome_direction"),
            "source_citations": participation.get("source_citations", []),
        }
        windows.append({**base, "window_id": f"event:{participation['profile_key']}:{event['event_id']}", "window_kind": "event", "anchor_date": anchor.isoformat(), "outcome_present": 1, "match_method": "documented event date"})
        for shift in CONTROL_SHIFTS:
            control = anchor + timedelta(days=shift)
            if any(abs((control - known).days) <= 30 for known in known_event_dates):
                continue
            windows.append({**base, "window_id": f"control:{participation['profile_key']}:{event['event_id']}:{shift:+d}", "window_kind": "within_person_control", "anchor_date": control.isoformat(), "outcome_present": 0, "match_method": f"same person; event date shifted {shift:+d} days; excludes ±30 days around registered events"})
    return windows


def placebo_dates(event_dates: list[str], *, iterations: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    result: list[list[str]] = []
    for _ in range(iterations):
        shifted = []
        for value in event_dates:
            point = date.fromisoformat(value)
            magnitude = rng.randint(30, 365)
            direction = -1 if rng.random() < 0.5 else 1
            shifted.append((point + timedelta(days=direction * magnitude)).isoformat())
        result.append(shifted)
    return result


def shuffled_birth_assignments(profile_keys: list[str], birth_dates: list[str], *, iterations: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    outputs = []
    for _ in range(iterations):
        values = list(birth_dates)
        rng.shuffle(values)
        outputs.append(dict(zip(profile_keys, values, strict=True)))
    return outputs


def shuffled_relationship_edges(profile_keys: list[str], edge_count: int, *, seed: int) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    possible = [(a, b) for index, a in enumerate(profile_keys) for b in profile_keys[index + 1:]]
    rng.shuffle(possible)
    return sorted(possible[: min(edge_count, len(possible))])


def holdout_split(profile_keys: list[str]) -> dict[str, list[str]]:
    ordered = sorted(set(profile_keys))
    cut = max(1, int(len(ordered) * 0.67)) if ordered else 0
    return {"discovery": ordered[:cut], "holdout": ordered[cut:]}
