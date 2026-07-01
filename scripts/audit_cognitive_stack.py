"""Audit Atlas cognitive stack services."""

from __future__ import annotations

import traceback


TEST_PROFILE = "nikola_tesla"
TEST_PROFILE_B = "thomas_edison"
TEST_QUERY = "Explain Nikola Tesla"
TEST_RELATIONSHIP_QUERY = "Compare Nikola Tesla and Thomas Edison"


def main() -> None:
    """Run cognitive stack audit."""
    print()
    print("ATLAS COGNITIVE STACK AUDIT")
    print("=" * 80)

    checks = [
        ("Query Planner", audit_query_planner),
        ("Atlas AI Profile", audit_atlas_ai_profile),
        ("Atlas AI Relationship", audit_atlas_ai_relationship),
        ("Reasoning Service", audit_reasoning),
        ("Hypothesis Engine", audit_hypothesis),
        ("Falsification Engine", audit_falsification),
        ("Experiment Planner", audit_experiment_planner),
        ("Discovery Engine", audit_discovery),
        ("Research Memory", audit_research_memory),
        ("Vedic Behavior Overlay", audit_vedic_behavior),
    ]

    failures = []

    for label, fn in checks:
        try:
            result = fn()
            print_result(label, result)
            if not result.get("success"):
                failures.append((label, result))
        except Exception as exc:  # noqa: BLE001
            failures.append((label, {"success": False, "error": str(exc)}))
            print_result(
                label,
                {
                    "success": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )

    print()
    print("=" * 80)

    if failures:
        print(f"COGNITIVE STACK FAILED: {len(failures)} failure(s)")
        for label, result in failures:
            print(f"- {label}: {result.get('error') or result.get('errors')}")
        raise SystemExit(1)

    print("COGNITIVE STACK PASSED")
    raise SystemExit(0)


def audit_query_planner() -> dict:
    """Audit query planner."""
    from atlas.services.query_planner_service import build_query_plan_payload

    payload = build_query_plan_payload(TEST_QUERY)
    plan = payload.get("data", {}).get("plan", {})

    return {
        "success": payload.get("success") is True
        and plan.get("scope") == "profile"
        and TEST_PROFILE in plan.get("profiles", []),
        "intent": plan.get("intent"),
        "scope": plan.get("scope"),
        "profiles": plan.get("profiles", []),
        "services": plan.get("services", []),
    }


def audit_atlas_ai_profile() -> dict:
    """Audit Atlas AI profile mode."""
    from atlas.services.atlas_ai_service import build_profile_ai_payload

    payload = build_profile_ai_payload(TEST_PROFILE)

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "services_requested": payload.get("services_requested", []),
    }


def audit_atlas_ai_relationship() -> dict:
    """Audit Atlas AI relationship mode."""
    from atlas.services.atlas_ai_service import build_relationship_ai_payload

    payload = build_relationship_ai_payload(TEST_PROFILE, TEST_PROFILE_B)

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "services_requested": payload.get("services_requested", []),
    }


def audit_reasoning() -> dict:
    """Audit reasoning service."""
    from atlas.services.reasoning_service import build_reasoning_payload

    payload = build_reasoning_payload(TEST_QUERY)

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "final_answer_present": bool(
            payload.get("data", {}).get("reasoning", {}).get("final_answer")
        ),
    }


def audit_hypothesis() -> dict:
    """Audit hypothesis engine."""
    from atlas.services.hypothesis_engine_service import build_hypothesis_payload

    payload = build_hypothesis_payload(TEST_QUERY)
    model = payload.get("data", {}).get("hypothesis_model", {})

    return {
        "success": payload.get("success") is True
        and len(model.get("hypotheses", [])) > 0,
        "metrics": payload.get("metrics", {}),
        "best_hypothesis": model.get("best_supported_hypothesis", {}).get("title"),
    }


def audit_falsification() -> dict:
    """Audit falsification engine."""
    from atlas.services.falsification_engine_service import build_falsification_payload

    payload = build_falsification_payload(TEST_QUERY)
    model = payload.get("data", {}).get("falsification_model", {})

    return {
        "success": payload.get("success") is True
        and len(model.get("cases", [])) > 0,
        "metrics": payload.get("metrics", {}),
        "highest_priority_case": model.get("highest_priority_case", {}).get(
            "hypothesis_title"
        ),
    }


def audit_experiment_planner() -> dict:
    """Audit experiment planner."""
    from atlas.services.experiment_planner_service import build_experiment_plan_payload

    payload = build_experiment_plan_payload(TEST_QUERY)
    model = payload.get("data", {}).get("experiment_model", {})

    return {
        "success": payload.get("success") is True
        and len(model.get("experiments", [])) > 0,
        "metrics": payload.get("metrics", {}),
        "recommended_next_experiment": model.get(
            "recommended_next_experiment",
            {},
        ).get("title"),
    }


def audit_discovery() -> dict:
    """Audit discovery engine."""
    from atlas.services.discovery_engine_service import build_discovery_payload

    payload = build_discovery_payload(limit=5)
    model = payload.get("data", {}).get("discovery_model", {})

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
        "summary": model.get("summary", {}),
    }


def audit_research_memory() -> dict:
    """Audit research memory."""
    from atlas.services.research_memory_service import (
        build_research_memory_payload,
        list_research_memory_records,
    )

    payload = build_research_memory_payload(TEST_QUERY)
    records = list_research_memory_records()

    return {
        "success": payload.get("success") is True and len(records) > 0,
        "metrics": payload.get("metrics", {}),
        "latest_record": records[0] if records else {},
    }


def audit_vedic_behavior() -> dict:
    """Audit Vedic behavior overlay."""
    from atlas.services.vedic_behavior_service import build_vedic_behavior_payload

    payload = build_vedic_behavior_payload(TEST_PROFILE)

    return {
        "success": payload.get("success") is True,
        "metrics": payload.get("metrics", {}),
    }


def print_result(label: str, result: dict) -> None:
    """Print compact result."""
    status = "PASS" if result.get("success") else "FAIL"
    print()
    print(f"{label}: {status}")

    for key, value in result.items():
        if key == "success":
            continue
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()