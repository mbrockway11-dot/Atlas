from atlas.invariant.rotations import (
    all_invariant_orientations,
    mirror_x,
    mirror_y,
    rotate_90,
    rotate_180,
    rotate_270,
    transform_path,
)


def test_rotate_90():
    assert rotate_90((0, 0), 3) == (0, 2)
    assert rotate_90((2, 0), 3) == (0, 0)


def test_rotate_180():
    assert rotate_180((0, 0), 3) == (2, 2)
    assert rotate_180((1, 2), 3) == (1, 0)


def test_rotate_270():
    assert rotate_270((0, 0), 3) == (2, 0)
    assert rotate_270((0, 2), 3) == (0, 0)


def test_mirror_x():
    assert mirror_x((0, 1), 3) == (2, 1)


def test_mirror_y():
    assert mirror_y((1, 0), 3) == (1, 2)


def test_transform_path_identity():
    path = [(0, 0), (1, 1), (2, 2)]

    assert transform_path(path, 3, "identity") == path


def test_all_invariant_orientations():
    path = [(0, 0), (1, 1), (2, 2)]
    orientations = all_invariant_orientations(path, 3)

    assert set(orientations.keys()) == {
        "identity",
        "rotate_90",
        "rotate_180",
        "rotate_270",
        "mirror_x",
        "mirror_y",
    }
    assert len(orientations["identity"]) == 3