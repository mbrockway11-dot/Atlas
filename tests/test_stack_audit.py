from atlas.graph.stack_audit import (
    STACK_AUDIT_VERSION,
    audit_identity_stack,
    stack_audit_to_dict,
)


def _stack() -> dict:
    return {
        "name": "Audit Test",
        "cig": {
            "analyzed_graph": {
                "construction_passes": [
                    {
                        "cipher": "ordinal",
                        "planet": "Saturn",
                        "layer_id": "ordinal::Saturn",
                        "visit_count": 20,
                    }
                    for _ in range(21)
                ],
                "analysis": {
                    "component_count": 1,
                    "largest_component_size": 3,
                    "bridge_count": 1,
                    "articulation_point_count": 1,
                    "leaf_count": 1,
                    "hub_count": 1,
                },
                "nodes": {
                    "1": {"weight": 3},
                    "2": {"weight": 2},
                    "3": {"weight": 1},
                },
                "edges": {
                    "1->2": {"weight": 3},
                    "2->3": {"weight": 2},
                },
            },
        },
        "stg": {
            "nodes": {
                "1": {"weight": 3},
                "2": {"weight": 2},
            },
            "edges": {
                "1->2": {"weight": 3},
            },
        },
    }


def test_audit_identity_stack_returns_valid_audit():
    audit = audit_identity_stack(_stack())

    assert audit.version == STACK_AUDIT_VERSION
    assert audit.status in {"healthy", "warning", "error"}
    assert isinstance(audit.valid, bool)
    assert audit.issue_count >= 0

    data = stack_audit_to_dict(audit)

    assert data["version"] == STACK_AUDIT_VERSION
    assert "issues" in data
    assert "summary" in data


def test_audit_detects_visit_imbalance():
    stack = _stack()
    stack["cig"]["analyzed_graph"]["construction_passes"][0]["visit_count"] = 18

    audit = audit_identity_stack(stack)
    codes = {issue.code for issue in audit.issues}

    assert "cross_cipher_visit_imbalance" in codes


def test_audit_detects_high_hub_ratio():
    stack = _stack()
    stack["cig"]["analyzed_graph"]["nodes"] = {
        str(index): {"weight": 1}
        for index in range(10)
    }
    stack["cig"]["analyzed_graph"]["analysis"]["hub_count"] = 5

    audit = audit_identity_stack(stack)
    codes = {issue.code for issue in audit.issues}

    assert "high_hub_ratio" in codes