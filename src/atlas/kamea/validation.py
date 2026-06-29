"""Kamea validation reporting."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    size: int
    magic_sum: int
    square_total: int
    unique_values: int
    missing: tuple[int, ...]
    extra: tuple[int, ...]
    duplicates: tuple[int, ...]
    row_sums: tuple[int, ...]
    column_sums: tuple[int, ...]
    diagonal_sums: tuple[int, int]