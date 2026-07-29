"""Do civilizational turning points cluster in the slow planetary cycles?

The classic historical-astrology claim about the 'life of civilizations': major
events track the Jupiter-Saturn synodic cycle (~19.86 yr 'great conjunctions')
and the outer-planet configurations. Testable directly.

Curated major dated turning points (foundings, revolutions, wars, collapses).
For each: the Jupiter-Saturn angular separation (the synodic phase, 0..360) and
Saturn's longitude. Rayleigh test for circular clustering, against a null of the
same number of uniformly random dates across the span (which controls for the
cycle's own geometry and the event span, but not for uneven event density -- so a
positive would still need a density check). Honest prior after this session: null.
"""

from __future__ import annotations

import numpy as np
import swisseph as swe

SEED = 20260728
EVENTS = [
    "0476-09-04", "0800-12-25", "1066-10-14", "1095-11-27", "1215-06-15",
    "1291-05-18", "1347-10-01", "1453-05-29", "1492-10-12", "1517-10-31",
    "1588-08-08", "1618-05-23", "1648-10-24", "1660-05-29", "1688-11-05",
    "1707-05-01", "1776-07-04", "1783-09-03", "1789-07-14", "1791-08-22",
    "1804-12-02", "1815-06-18", "1821-09-15", "1848-02-24", "1861-04-12",
    "1865-04-09", "1867-07-01", "1871-01-18", "1885-02-26", "1898-04-25",
    "1901-01-01", "1910-05-31", "1914-06-28", "1914-07-28", "1917-11-07",
    "1918-11-11", "1919-06-28", "1922-10-28", "1929-10-29", "1933-01-30",
    "1936-07-17", "1939-09-01", "1941-12-07", "1945-05-08", "1945-08-06",
    "1945-09-02", "1947-08-15", "1948-05-14", "1949-10-01", "1955-04-18",
    "1957-03-25", "1959-01-01", "1962-10-16", "1963-11-22", "1969-07-20",
    "1971-12-16", "1975-04-30", "1979-02-11", "1979-12-24", "1989-11-09",
    "1990-08-02", "1991-12-26", "1994-04-27", "1997-07-01", "2001-09-11",
    "2003-03-20", "2008-09-15", "2011-12-17", "2016-06-23", "2022-02-24",
]


def jd_of(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    cal = swe.GREG_CAL if (y, m, d) >= (1582, 10, 15) else swe.JUL_CAL
    return swe.julday(y, m, d, 12.0, cal)


def js_phase_and_saturn(jd):
    ju = swe.calc_ut(jd, swe.JUPITER)[0][0]
    sa = swe.calc_ut(jd, swe.SATURN)[0][0]
    return (ju - sa) % 360.0, sa % 360.0


def rayleigh(angles_deg):
    a = np.radians(angles_deg)
    n = len(a)
    R = np.sqrt(np.cos(a).sum() ** 2 + np.sin(a).sum() ** 2) / n
    # Rayleigh p-value approximation
    z = n * R ** 2
    p = np.exp(-z) * (1 + (2 * z - z ** 2) / (4 * n))
    return float(R), float(p)


def main():
    jds = np.array([jd_of(e) for e in EVENTS])
    js = np.array([js_phase_and_saturn(j) for j in jds])
    js_phase, sat = js[:, 0], js[:, 1]
    n = len(EVENTS)
    print(f"events: {n}   span {EVENTS[0]} .. {EVENTS[-1]}\n")

    R_js, p_js = rayleigh(js_phase)
    R_sa, p_sa = rayleigh(sat)
    print("=== Rayleigh test for circular clustering (R near 0 = uniform) ===")
    print(f"  Jupiter-Saturn synodic phase:  R = {R_js:.3f}  Rayleigh p = {p_js:.4f}")
    print(f"  Saturn longitude:              R = {R_sa:.3f}  Rayleigh p = {p_sa:.4f}")

    # permutation null: same-size samples of uniformly random dates in the span
    rng = np.random.default_rng(SEED)
    lo, hi = jds.min(), jds.max()
    null_js, null_sa = [], []
    for _ in range(5000):
        rj = rng.uniform(lo, hi, size=n)
        ph = np.array([js_phase_and_saturn(j) for j in rj])
        null_js.append(rayleigh(ph[:, 0])[0])
        null_sa.append(rayleigh(ph[:, 1])[0])
    null_js, null_sa = np.array(null_js), np.array(null_sa)
    pperm_js = float((null_js >= R_js).mean())
    pperm_sa = float((null_sa >= R_sa).mean())
    print("\n=== permutation null (random dates, same span) ===")
    print(f"  Jupiter-Saturn: observed R {R_js:.3f}  null R {null_js.mean():.3f}  "
          f"p = {pperm_js:.4f}  {'<-- clusters' if pperm_js < 0.05 else 'AT NULL'}")
    print(f"  Saturn:         observed R {R_sa:.3f}  null R {null_sa.mean():.3f}  "
          f"p = {pperm_sa:.4f}  {'<-- clusters' if pperm_sa < 0.05 else 'AT NULL'}")

    print("\nAT NULL = turning points fall at no preferred phase of the cycle; the")
    print("'great conjunction governs history' claim is not supported by these events.")


if __name__ == "__main__":
    main()
