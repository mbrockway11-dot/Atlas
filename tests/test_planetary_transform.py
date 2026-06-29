from atlas.ciphers import run_all_ciphers
from atlas.kamea.projection import project_values_to_all_kameas
from atlas.kamea.planetary_transform import transform_values_for_planet


def test_planetary_transform_changes_values_by_planet():
    values = run_all_ciphers("Michael Elvis Brockway")["ordinal"]

    transformed = {
        planet: transform_values_for_planet(values, planet)
        for planet in [
            "saturn",
            "jupiter",
            "mars",
            "sun",
            "venus",
            "mercury",
            "moon",
        ]
    }

    assert transformed["saturn"] != transformed["jupiter"]
    assert transformed["jupiter"] != transformed["mars"]
    assert transformed["mars"] != transformed["sun"]
    assert transformed["sun"] != transformed["venus"]
    assert transformed["venus"] != transformed["mercury"]
    assert transformed["mercury"] != transformed["moon"]


def test_projected_reduced_values_differ_across_large_kameas():
    values = run_all_ciphers("Alan Turing")["ordinal"]
    paths = project_values_to_all_kameas(
        values,
        use_planetary_transform=True,
    )

    reduced = {
        planet: path.reduced_values
        for planet, path in paths.items()
    }

    assert reduced["jupiter"] != reduced["mars"]
    assert reduced["mars"] != reduced["sun"]
    assert reduced["sun"] != reduced["venus"]
    assert reduced["venus"] != reduced["mercury"]
    assert reduced["mercury"] != reduced["moon"]


def test_projected_coordinates_differ_across_large_kameas():
    values = run_all_ciphers("Alan Turing")["ordinal"]
    paths = project_values_to_all_kameas(
        values,
        use_planetary_transform=True,
    )

    coordinates = {
        planet: path.coordinates
        for planet, path in paths.items()
    }

    assert coordinates["jupiter"] != coordinates["mars"]
    assert coordinates["mars"] != coordinates["sun"]
    assert coordinates["sun"] != coordinates["venus"]
    assert coordinates["venus"] != coordinates["mercury"]
    assert coordinates["mercury"] != coordinates["moon"]