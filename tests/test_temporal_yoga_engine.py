from atlas.temporal.aspects import build_aspect_chart
from atlas.temporal.dignity import build_dignity_chart
from atlas.temporal.houses import build_house_chart
from atlas.temporal.models import BirthData
from atlas.temporal.natal_chart import build_natal_chart
from atlas.temporal.yoga_engine import (
    YOGA_ENGINE_VERSION,
    evaluate_all_yogas,
    yoga_evaluation_to_dict,
)


def _birth():
    return BirthData(
        name="Albert Einstein",
        birth_date="1879-03-14",
        birth_time="11:30",
        birth_place="Ulm",
        latitude=48.3984,
        longitude=9.9916,
        timezone="Europe/Berlin",
        time_known=True,
    )


def test_evaluate_all_yogas():

    natal = build_natal_chart(_birth())
    houses = build_house_chart(natal)
    dignity = build_dignity_chart(natal)
    aspects = build_aspect_chart(houses)

    evaluation = evaluate_all_yogas(
        natal=natal,
        houses=houses,
        dignity=dignity,
        aspects=aspects,
    )

    assert evaluation.version == YOGA_ENGINE_VERSION
    assert evaluation.name == "Albert Einstein"
    assert evaluation.summary["evaluated"] > 0


def test_serialization():

    natal = build_natal_chart(_birth())
    houses = build_house_chart(natal)
    dignity = build_dignity_chart(natal)
    aspects = build_aspect_chart(houses)

    evaluation = evaluate_all_yogas(
        natal=natal,
        houses=houses,
        dignity=dignity,
        aspects=aspects,
    )

    data = yoga_evaluation_to_dict(evaluation)

    assert data["version"] == YOGA_ENGINE_VERSION
    assert "matches" in data
    assert "summary" in data