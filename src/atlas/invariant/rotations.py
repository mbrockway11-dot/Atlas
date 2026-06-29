"""Rotation and mirror transforms for Kamea coordinate paths."""

from typing import Iterable

Coordinate = tuple[int, int]


def rotate_90(coord: Coordinate, grid_size: int) -> Coordinate:
    """Rotate coordinate 90 degrees clockwise."""
    row, col = coord
    return col, grid_size - 1 - row


def rotate_180(coord: Coordinate, grid_size: int) -> Coordinate:
    """Rotate coordinate 180 degrees."""
    row, col = coord
    return grid_size - 1 - row, grid_size - 1 - col


def rotate_270(coord: Coordinate, grid_size: int) -> Coordinate:
    """Rotate coordinate 270 degrees clockwise."""
    row, col = coord
    return grid_size - 1 - col, row


def mirror_x(coord: Coordinate, grid_size: int) -> Coordinate:
    """Mirror coordinate across horizontal axis."""
    row, col = coord
    return grid_size - 1 - row, col


def mirror_y(coord: Coordinate, grid_size: int) -> Coordinate:
    """Mirror coordinate across vertical axis."""
    row, col = coord
    return row, grid_size - 1 - col


def transform_path(
    path: Iterable[Coordinate],
    grid_size: int,
    transform: str,
) -> list[Coordinate]:
    """Transform a coordinate path."""
    transforms = {
        "identity": lambda coord: coord,
        "rotate_90": lambda coord: rotate_90(coord, grid_size),
        "rotate_180": lambda coord: rotate_180(coord, grid_size),
        "rotate_270": lambda coord: rotate_270(coord, grid_size),
        "mirror_x": lambda coord: mirror_x(coord, grid_size),
        "mirror_y": lambda coord: mirror_y(coord, grid_size),
    }

    if transform not in transforms:
        raise ValueError(f"Unknown transform: {transform}")

    return [transforms[transform](coord) for coord in path]


def all_invariant_orientations(
    path: Iterable[Coordinate],
    grid_size: int,
) -> dict[str, list[Coordinate]]:
    """Return all required invariant orientations."""
    return {
        "identity": transform_path(path, grid_size, "identity"),
        "rotate_90": transform_path(path, grid_size, "rotate_90"),
        "rotate_180": transform_path(path, grid_size, "rotate_180"),
        "rotate_270": transform_path(path, grid_size, "rotate_270"),
        "mirror_x": transform_path(path, grid_size, "mirror_x"),
        "mirror_y": transform_path(path, grid_size, "mirror_y"),
    }