"""Fractal / self-similarity measures of a Kamea traversal.

A traversal is a set of points in the square. This module measures how it fills
space and whether that filling is self-similar across scales:

  * box_counting_dimension -- N(epsilon) ~ epsilon^-D; the capacity dimension.
  * correlation_dimension  -- Grassberger-Procaccia D2 from pair distances; more
    stable than box-counting for small point sets.
  * generalized_dimensions -- the Renyi dimensions D(q). A monofractal has D(q)
    constant; a multifractal has D(q) falling with q. The spread D(-)-D(+) is the
    multifractal width: a single scaling law vs a spectrum of local ones.

All measurements are licensed by mathematics only -- no interpretation attached.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

Point = Sequence[float]


def _normalized(points: Sequence[Point]) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or len(p) < 2:
        return p.reshape(-1, 2)
    lo = p.min(axis=0)
    ext = (p - lo).max()
    if ext <= 0:
        return np.zeros_like(p)
    return (p - lo) / ext


def _fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if len(xs) < 3:
        return float("nan"), 0.0
    a, b = np.polyfit(xs, ys, 1)
    pred = a * np.array(xs) + b
    yy = np.array(ys)
    ss = ((yy - yy.mean()) ** 2).sum()
    r2 = 1 - ((yy - pred) ** 2).sum() / ss if ss > 0 else 0.0
    return float(a), float(r2)


def _box_counts(p: np.ndarray, s: int) -> dict[tuple[int, int], int]:
    counts: Counter[tuple[int, int]] = Counter()
    for x, y in p:
        cx = min(s - 1, int(x * s))
        cy = min(s - 1, int(y * s))
        counts[(cx, cy)] += 1
    return dict(counts)


def box_counting_dimension(points: Sequence[Point]) -> tuple[float, float]:
    """Return (capacity dimension, log-log R^2)."""
    p = _normalized(points)
    n = len(p)
    if n < 4:
        return float("nan"), 0.0
    scales = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64]
    xs, ys = [], []
    for s in scales:
        occupied = len(_box_counts(p, s))
        if occupied >= 0.95 * n:  # saturated: each point ~ its own box
            break
        xs.append(np.log(s))
        ys.append(np.log(occupied))
    return _fit(xs, ys)


def correlation_dimension(points: Sequence[Point]) -> tuple[float, float]:
    """Grassberger-Procaccia D2 from the pair-distance correlation sum."""
    p = _normalized(points)
    n = len(p)
    if n < 8:
        return float("nan"), 0.0
    d = np.sqrt(((p[:, None, :] - p[None, :, :]) ** 2).sum(axis=2))
    iu = np.triu_indices(n, k=1)
    dist = d[iu]
    dist = dist[dist > 0]
    if len(dist) < 8:
        return float("nan"), 0.0
    lo, hi = np.percentile(dist, 5), np.percentile(dist, 60)
    radii = np.geomspace(lo, hi, 12)
    xs, ys = [], []
    for r in radii:
        c = float((dist < r).mean())
        if c > 0:
            xs.append(np.log(r))
            ys.append(np.log(c))
    return _fit(xs, ys)


def generalized_dimensions(
    points: Sequence[Point], qs: Sequence[float] | None = None
) -> tuple[dict[float, float], float]:
    """Return (D(q) for each q, multifractal width D(qmin)-D(qmax))."""
    if qs is None:
        qs = [-5, -3, -2, -1, 0, 1, 2, 3, 5]
    p = _normalized(points)
    n = len(p)
    if n < 8:
        return {}, float("nan")
    scales = [2, 3, 4, 6, 8, 12, 16]
    scales = [s for s in scales if len(_box_counts(p, s)) < 0.95 * n]
    if len(scales) < 3:
        return {}, float("nan")
    dq: dict[float, float] = {}
    for q in qs:
        log_eps, log_chi = [], []
        for s in scales:
            probs = np.array(list(_box_counts(p, s).values()), dtype=float) / n
            eps = 1.0 / s
            if abs(q - 1.0) < 1e-9:
                chi = float((probs * np.log(probs)).sum())  # numerator of D1
                log_eps.append(np.log(eps))
                log_chi.append(chi)
            else:
                chi = float((probs ** q).sum())
                log_eps.append(np.log(eps))
                log_chi.append(np.log(chi))
        slope, _ = _fit(log_eps, log_chi)
        dq[float(q)] = slope if abs(q - 1.0) < 1e-9 else slope / (q - 1.0)
    width = dq.get(float(min(qs)), float("nan")) - dq.get(float(max(qs)), float("nan"))
    return dq, float(width)


@dataclass(frozen=True, slots=True)
class FractalSignature:
    """A traversal's fractal fingerprint."""

    box_dimension: float
    box_r2: float
    correlation_dimension: float
    correlation_r2: float
    multifractal_width: float
    dq: dict[float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "box_dimension": self.box_dimension,
            "box_r2": self.box_r2,
            "correlation_dimension": self.correlation_dimension,
            "correlation_r2": self.correlation_r2,
            "multifractal_width": self.multifractal_width,
            "dq": {str(k): v for k, v in self.dq.items()},
        }


def fractal_signature(points: Sequence[Point]) -> FractalSignature:
    """Bundle every fractal measure for one traversal."""
    box_d, box_r2 = box_counting_dimension(points)
    corr_d, corr_r2 = correlation_dimension(points)
    dq, width = generalized_dimensions(points)
    return FractalSignature(
        box_dimension=round(box_d, 6) if box_d == box_d else box_d,
        box_r2=round(box_r2, 6),
        correlation_dimension=round(corr_d, 6) if corr_d == corr_d else corr_d,
        correlation_r2=round(corr_r2, 6),
        multifractal_width=round(width, 6) if width == width else width,
        dq={k: round(v, 6) for k, v in dq.items()},
    )
