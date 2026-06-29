from atlas.features.cluster_interpretation import (
    describe_feature,
    interpret_cluster,
    interpret_cluster_report,
    parse_feature_name,
)


def test_parse_feature_name_planet():
    planet, label = parse_feature_name("saturn_hub_ratio")

    assert planet == "Saturn"
    assert label == "hub concentration"


def test_parse_feature_name_global():
    planet, label = parse_feature_name("global_mean_bridge_ratio")

    assert planet is None
    assert label == "bridge behavior"


def test_describe_feature():
    assert describe_feature("sun_bridge_ratio") == "Sun bridge behavior"


def test_interpret_cluster():
    cluster = {
        "cluster_id": 0,
        "size": 2,
        "representative": "A",
        "members": ["A", "B"],
        "dominant_features": [
            {
                "feature": "sun_bridge_ratio",
                "centroid_value": 1.2,
            },
            {
                "feature": "global_mean_hub_ratio",
                "centroid_value": -1.1,
            },
        ],
    }

    interpretation = interpret_cluster(cluster)

    assert interpretation["label"] == "Sun Bridge Behavior Type"
    assert interpretation["summary_lines"]


def test_interpret_cluster_report():
    report = {
        "cluster_count": 1,
        "feature_count": 2,
        "clusters": [
            {
                "cluster_id": 0,
                "size": 2,
                "representative": "A",
                "members": ["A", "B"],
                "dominant_features": [
                    {
                        "feature": "sun_bridge_ratio",
                        "centroid_value": 1.2,
                    }
                ],
            }
        ],
        "outliers": [],
    }

    interpretation = interpret_cluster_report(report)

    assert interpretation["cluster_count"] == 1
    assert interpretation["clusters"]