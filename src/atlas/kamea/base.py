"""Core Kamea data structures and validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.kamea.path import KameaPath
from atlas.kamea.planetary_transform import transform_values_for_planet
from atlas.kamea.validation import ValidationReport


Coordinate = tuple[int, int]


@dataclass(frozen=True)
class PlanetaryKamea:
    """Immutable planetary Kamea square."""

    key: str
    name: str
    planet: str
    size: int
    magic_sum: int
    square_total: int
    square: tuple[tuple[int, ...], ...]

    coordinate_lookup: dict[int, Coordinate] = field(init=False)

    def __post_init__(self) -> None:
        self._validate_square()

        lookup = {}
        for row_index, row in enumerate(self.square):
            for col_index, value in enumerate(row):
                lookup[value] = (row_index, col_index)

        object.__setattr__(self, "coordinate_lookup", lookup)

    @property
    def max_value(self) -> int:
        """Highest valid value in this Kamea."""
        return self.size * self.size

    def reduce_value(self, value: int) -> int:
        """Reduce a positive integer into this Kamea's valid range."""
        if value <= 0:
            raise ValueError("Kamea values must be positive integers.")

        return ((value - 1) % self.max_value) + 1

    def coordinate_for(self, value: int) -> Coordinate:
        """Return the coordinate for a raw value after reduction."""
        reduced_value = self.reduce_value(value)
        return self.coordinate_lookup[reduced_value]

    def project_values(
        self,
        values: list[int],
        use_planetary_transform: bool = False,
    ) -> KameaPath:
        """Project raw numeric values into this Kamea path.

        By default this preserves legacy direct projection behavior.

        When use_planetary_transform=True, values are expanded through a
        deterministic planet-specific transform before reduction. This prevents
        large Kameas from receiving nearly identical low-range paths.
        """
        raw_values = tuple(values)

        projection_values = (
            tuple(transform_values_for_planet(values, self.key))
            if use_planetary_transform
            else raw_values
        )

        reduced_values = tuple(
            self.reduce_value(value)
            for value in projection_values
        )

        coordinates = tuple(
            self.coordinate_lookup[reduced_value]
            for reduced_value in reduced_values
        )

        return KameaPath(
            raw_values=raw_values,
            reduced_values=reduced_values,
            coordinates=coordinates,
        )

    def validation_report(self) -> ValidationReport:
        """Return a structured validation report for this Kamea."""
        values = [
            value
            for row in self.square
            for value in row
        ]

        expected_values = set(range(1, self.max_value + 1))
        actual_values = set(values)

        duplicates = sorted(
            value
            for value in actual_values
            if values.count(value) > 1
        )

        row_sums = tuple(sum(row) for row in self.square)
        column_sums = tuple(
            sum(row[col_index] for row in self.square)
            for col_index in range(self.size)
        )

        diagonal_a = sum(
            self.square[index][index]
            for index in range(self.size)
        )
        diagonal_b = sum(
            self.square[index][self.size - 1 - index]
            for index in range(self.size)
        )

        missing = tuple(sorted(expected_values - actual_values))
        extra = tuple(sorted(actual_values - expected_values))

        valid = (
            not missing
            and not extra
            and not duplicates
            and all(total == self.magic_sum for total in row_sums)
            and all(total == self.magic_sum for total in column_sums)
            and sum(values) == self.square_total
        )

        return ValidationReport(
            valid=valid,
            size=self.size,
            magic_sum=self.magic_sum,
            square_total=self.square_total,
            unique_values=len(actual_values),
            missing=missing,
            extra=extra,
            duplicates=tuple(duplicates),
            row_sums=row_sums,
            column_sums=column_sums,
            diagonal_sums=(diagonal_a, diagonal_b),
        )

    def _validate_square(self) -> None:
        """Validate shape, values, magic sum, and total."""
        if len(self.square) != self.size:
            raise ValueError(f"{self.name} must have {self.size} rows.")

        for row in self.square:
            if len(row) != self.size:
                raise ValueError(f"{self.name} must be {self.size}x{self.size}.")

        values = [
            value
            for row in self.square
            for value in row
        ]

        expected_values = set(range(1, self.max_value + 1))
        actual_values = set(values)

        if actual_values != expected_values:
            missing = sorted(expected_values - actual_values)
            extra = sorted(actual_values - expected_values)
            raise ValueError(
                f"Invalid {self.name} square. Missing={missing}, Extra={extra}"
            )

        if len(values) != len(actual_values):
            raise ValueError(f"{self.name} contains duplicate values.")

        for row in self.square:
            if sum(row) != self.magic_sum:
                raise ValueError(f"{self.name} row does not match magic sum.")

        for col_index in range(self.size):
            col_sum = sum(row[col_index] for row in self.square)
            if col_sum != self.magic_sum:
                raise ValueError(f"{self.name} column does not match magic sum.")

        if sum(values) != self.square_total:
            raise ValueError(f"{self.name} square total is invalid.")