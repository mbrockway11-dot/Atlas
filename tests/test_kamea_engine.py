from atlas.kamea.projection import get_kamea, project_values_to_kamea
from atlas.kamea.squares import KAMEAS


def test_all_kameas_validate_on_import():
    assert len(KAMEAS) == 7


def test_saturn_projection():
    saturn = get_kamea("saturn")

    assert saturn.reduce_value(10) == 1
    assert saturn.coordinate_for(1) == (2, 1)
    assert saturn.coordinate_for(5) == (1, 1)


def test_projection_path():
    path = project_values_to_kamea([1, 5, 10], "saturn")

    assert path.reduced_values == (1, 5, 1)
    assert path.coordinates[0] == (2, 1)
    assert path.length == 3


def test_moon_is_valid():
    moon = get_kamea("moon")

    assert moon.size == 9
    assert moon.magic_sum == 369
    assert moon.square_total == 3321
    assert len(moon.coordinate_lookup) == 81