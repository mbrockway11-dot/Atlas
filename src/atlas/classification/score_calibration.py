"""Population calibration for the coarse classification scores.

The functional scores (driver / amplifier / regulator) and symmetry are each
produced by a different formula, and those formulas land on **non-overlapping
scales** across the corpus:

    driver     0.06 - 0.13   (mean 0.08)
    amplifier  0.38 - 0.59   (mean 0.49)
    regulator  0.62 - 0.93   (mean 0.73)

So an *absolute* comparison between them -- ``argmax(driver, amplifier,
regulator)`` -- is a constant: regulator's formula simply emits the biggest
number, for everyone. (The v2 classifier collapses the same way, to Explorer.)
The scores only carry information *relative to the population*: "is this profile
high on driver **for a person**," not "is driver > regulator on their private
scales."

This module supplies the (mean, sd) needed to z-score each score against the
corpus, so a label answers the relative question. The label is therefore
**relative to the corpus these statistics came from** -- a profile's role can
change as the library changes, which is a property of the method, not a bug, and
callers should surface it (see ``basis`` on the classification outputs).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreCalibration:
    """Per-score (mean, standard deviation) over a reference population."""

    driver: tuple[float, float]
    amplifier: tuple[float, float]
    regulator: tuple[float, float]
    symmetry: tuple[float, float]

    def z(self, name: str, value: float) -> float:
        """Standard score of ``value`` for score ``name`` against the corpus."""
        mean, sd = getattr(self, name)
        return (value - mean) / sd if sd > 0 else 0.0


# Corpus-derived default: mean/sd over a fixed 200-profile sample of the
# ~2,122-profile structural-identity library (measured 2026-07-29). Baked in so
# the coarse labels are population-relative out of the box. For a production
# deployment this should become a hashed calibration artifact refreshed from the
# live corpus, not constants that drift as the library grows -- the same
# discipline the identity-vector calibration layer already uses.
DEFAULT_SCORE_CALIBRATION = ScoreCalibration(
    driver=(0.082, 0.013),
    amplifier=(0.490, 0.034),
    regulator=(0.726, 0.045),
    symmetry=(0.293, 0.127),
)

CALIBRATION_BASIS = "population-relative:corpus-2026-07-29"
