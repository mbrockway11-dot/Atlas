from atlas.kamea.path import KameaPath


def test_kamea_path_edges_and_repeats():
    path = KameaPath(
        raw_values=(1, 5, 10),
        reduced_values=(1, 5, 1),
        coordinates=((2, 1), (1, 1), (2, 1)),
    )

    assert path.length == 3
    assert path.edges == (((2, 1), (1, 1)), ((1, 1), (2, 1)))
    assert path.repeated_nodes == {(2, 1): 2}