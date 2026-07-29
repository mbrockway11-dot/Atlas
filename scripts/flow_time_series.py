"""Is the kamea flow, read as a time series, self-similar (fractal in time)?

The temporal completion of the self-similarity work, and uncomfoundable -- it is a
property of the ephemeris, not a claim about history. Sample the total flow (sum of
path_distance over the seven classical bodies, W3D window) at regular intervals
over decades, then ask what KIND of time series it is:

  * DFA Hurst exponent H:  0.5 = uncorrelated white noise; H != 0.5 = long-range
    (self-similar) correlations; ~1.0+ = strongly persistent / fractal.
  * Power spectrum S(f) ~ 1/f^beta:  beta~0 white; beta~1 = 1/f scale-free
    (fractal); discrete sharp PEAKS instead = quasi-periodic (planetary cycles),
    which is real structure but NOT self-similar.

The reduction (mod arithmetic) is scale-free; planetary motion is quasi-periodic.
This decides which one wins in the flow.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from atlas.validation.temporal_kamea import build_trajectory, canonical_spec, CLASSICAL_BODIES

SPEC = canonical_spec("R1-W3D")
BODIES = sorted(CLASSICAL_BODIES)
N = 8192          # power of two for the FFT
STEP_DAYS = 3
START = datetime(1900, 1, 1, 12, tzinfo=timezone.utc)


def flow_series():
    xs = np.empty(N)
    for i in range(N):
        dt = START + timedelta(days=i * STEP_DAYS)
        total = 0
        for b in BODIES:
            total += build_trajectory(dt, b, SPEC).diagnostics()["path_distance"]
        xs[i] = total
    return xs


def dfa(x):
    x = x - x.mean()
    y = np.cumsum(x)
    n = len(y)
    scales = np.unique(np.floor(np.logspace(np.log10(8), np.log10(n // 4), 20)).astype(int))
    F = []
    for s in scales:
        segs = n // s
        rms = []
        for k in range(segs):
            seg = y[k * s:(k + 1) * s]
            t = np.arange(s)
            fit = np.polyval(np.polyfit(t, seg, 1), t)
            rms.append(np.sqrt(((seg - fit) ** 2).mean()))
        F.append(np.mean(rms))
    H, _ = np.polyfit(np.log(scales), np.log(F), 1)
    return float(H)


def main():
    print(f"sampling {N} points at {STEP_DAYS}-day steps "
          f"({N*STEP_DAYS/365.25:.0f} years from {START.year})...")
    x = flow_series()
    print(f"flow series: mean {x.mean():.1f}  sd {x.std():.1f}  range [{x.min():.0f},{x.max():.0f}]\n")

    H = dfa(x)
    print(f"=== DFA Hurst exponent: H = {H:.3f} ===")
    print(f"  {'white noise (H~0.5): no long-range structure' if abs(H-0.5) < 0.08 else 'long-range correlations (H != 0.5): structured, not white'}")

    # power spectrum
    xf = x - x.mean()
    S = np.abs(np.fft.rfft(xf)) ** 2
    freqs = np.fft.rfftfreq(N, d=STEP_DAYS)   # cycles per day
    mask = (freqs > 0)
    lf, ls = np.log(freqs[mask]), np.log(S[mask])
    beta, _ = np.polyfit(lf, ls, 1)
    print(f"\n=== power spectrum: S(f) ~ 1/f^beta,  beta = {-beta:.2f} ===")
    print(f"  {'~1/f scale-free (fractal)' if 0.6 < -beta < 1.4 else 'white (beta~0)' if abs(beta) < 0.4 else 'steep/other'}")

    # top periodic peaks -- quasi-periodicity vs fractal
    order = np.argsort(S[mask])[::-1][:6]
    print("\n  dominant spectral peaks (period in days):")
    fpos = freqs[mask]
    for o in order:
        period = 1.0 / fpos[o]
        power_frac = S[mask][o] / S[mask].sum()
        print(f"    {period:8.1f} d  ({power_frac*100:4.1f}% of power)")

    print("\nSharp dominant peaks -> quasi-periodic (planetary cycles): real, NOT")
    print("self-similar. A smooth 1/f with H>0.5 and no dominant peak -> fractal.")


if __name__ == "__main__":
    main()
