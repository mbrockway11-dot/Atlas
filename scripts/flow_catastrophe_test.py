"""Pre-registered test: do mass-casualty catastrophes fall on low non-Moon kamea flow?

BACKGROUND
    An earlier exploratory pass (n=10) hinted that catastrophes cluster at low
    non-Moon kamea flow (p ~ 0.02-0.04). n=10 with a direction chosen after
    looking is not evidence. This script fixes the analysis in advance and runs
    it once, at scale, against an era-controlled null.

PRE-REGISTRATION  (fixed before any flow value is computed)
    H1 (directional): dated mass-casualty catastrophes have LOWER mean non-Moon
        kamea flow than random days drawn from the same calendar years.
    H0: catastrophe dates are no lower-flow than chance.

    METRIC (frozen):
        flow(date) = mean over the six non-Moon classical bodies
        {Sun, Mercury, Venus, Mars, Jupiter, Saturn} of
        build_trajectory(date 12:00 UTC, body, canonical_spec("R1-W3D"))
        .diagnostics()["path_distance"].
        The Moon is excluded by design -- the hint was specifically non-Moon.

    PRIMARY NULL (era-controlled): for each catastrophe, substitute a uniformly
        random day within its OWN calendar year. This removes any secular/era
        structure entirely and tests only the day-of-year selection. 10,000
        permutation cohorts; one-tailed p = fraction of cohorts whose mean flow
        is <= the observed catastrophe mean.

    SECONDARY NULL (broad): random days drawn uniformly across the full span of
        the catastrophe dates. Reported for context only.

    DECISION RULE: reject H0 iff primary p < 0.05. One primary test; the
        secondary null is descriptive and does not get its own claim.

    SEED: 20260727 (fixed). No metric, direction, or threshold may change after
        this point -- if the result is null, it is reported as null.

The catastrophe list is well-known dated mass-casualty events (natural
disasters, major accidents, attacks, war onsets) taken from the historical
record. Dates are the conventional calendar date of the event; a few (e.g.
Titanic) use the date the loss completed. No date was chosen for its flow value
-- the list was assembled before the metric was run.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np

from atlas.validation.temporal_kamea import build_trajectory, canonical_spec


SEED = 20260727
SPEC = canonical_spec("R1-W3D")
NON_MOON = ["sun", "mercury", "venus", "mars", "jupiter", "saturn"]
YEAR_SAMPLES = 40      # random day-of-year draws precomputed per catastrophe year
BROAD_POOL = 1500      # random dates across the full span for the secondary null
PERMS = 10000

# Dated mass-casualty catastrophes (assembled before the metric was computed).
DISASTERS = [
    ("1666-09-02", "Great Fire of London"),
    ("1755-11-01", "Lisbon earthquake"),
    ("1871-10-08", "Great Chicago Fire"),
    ("1883-08-27", "Krakatoa eruption"),
    ("1889-05-31", "Johnstown Flood"),
    ("1900-09-08", "Galveston hurricane"),
    ("1906-04-18", "San Francisco earthquake"),
    ("1908-06-30", "Tunguska event"),
    ("1911-03-25", "Triangle Shirtwaist fire"),
    ("1912-04-15", "Titanic sinking"),
    ("1915-05-07", "Lusitania sinking"),
    ("1923-09-01", "Great Kanto earthquake"),
    ("1928-03-12", "St. Francis Dam collapse"),
    ("1937-03-18", "New London School explosion"),
    ("1937-05-06", "Hindenburg disaster"),
    ("1940-11-07", "Tacoma Narrows collapse"),
    ("1941-12-07", "Pearl Harbor attack"),
    ("1945-08-06", "Hiroshima bombing"),
    ("1945-08-09", "Nagasaki bombing"),
    ("1947-04-16", "Texas City disaster"),
    ("1948-06-28", "no"),  # placeholder removed below
    ("1960-05-22", "Valdivia earthquake"),
    ("1963-11-09", "Miike / Tsurumi rail (Japan)"),
    ("1964-03-27", "Great Alaska earthquake"),
    ("1966-10-21", "Aberfan disaster"),
    ("1970-11-12", "Bhola cyclone"),
    ("1972-12-23", "Nicaragua (Managua) earthquake"),
    ("1976-07-28", "Tangshan earthquake"),
    ("1977-03-27", "Tenerife airport disaster"),
    ("1979-03-28", "Three Mile Island"),
    ("1980-05-18", "Mount St. Helens"),
    ("1981-07-17", "Hyatt Regency walkway collapse"),
    ("1984-12-03", "Bhopal disaster"),
    ("1985-09-19", "Mexico City earthquake"),
    ("1985-11-13", "Nevado del Ruiz (Armero)"),
    ("1986-01-28", "Challenger disaster"),
    ("1986-04-26", "Chernobyl disaster"),
    ("1987-12-20", "MV Dona Paz"),
    ("1988-12-07", "Spitak (Armenia) earthquake"),
    ("1988-12-21", "Lockerbie bombing"),
    ("1989-03-24", "Exxon Valdez spill"),
    ("1989-10-17", "Loma Prieta earthquake"),
    ("1991-04-29", "Bangladesh cyclone"),
    ("1993-02-26", "WTC bombing"),
    ("1994-01-17", "Northridge earthquake"),
    ("1994-09-28", "MS Estonia sinking"),
    ("1995-01-17", "Great Hanshin (Kobe) earthquake"),
    ("1995-04-19", "Oklahoma City bombing"),
    ("1996-07-17", "TWA Flight 800"),
    ("1998-08-07", "US embassy bombings"),
    ("1999-08-17", "Izmit earthquake"),
    ("2001-01-26", "Gujarat earthquake"),
    ("2001-09-11", "September 11 attacks"),
    ("2001-11-12", "American Airlines 587"),
    ("2002-09-26", "Le Joola sinking"),
    ("2003-02-01", "Columbia disaster"),
    ("2003-12-26", "Bam earthquake"),
    ("2004-03-11", "Madrid train bombings"),
    ("2004-12-26", "Indian Ocean tsunami"),
    ("2005-07-07", "London 7/7 bombings"),
    ("2005-08-29", "Hurricane Katrina landfall"),
    ("2005-10-08", "Kashmir earthquake"),
    ("2008-05-12", "Sichuan earthquake"),
    ("2008-11-26", "Mumbai attacks"),
    ("2009-04-06", "L'Aquila earthquake"),
    ("2009-06-01", "Air France 447"),
    ("2010-01-12", "Haiti earthquake"),
    ("2010-02-27", "Maule (Chile) earthquake"),
    ("2010-04-20", "Deepwater Horizon explosion"),
    ("2011-02-22", "Christchurch earthquake"),
    ("2011-03-11", "Tohoku earthquake/tsunami"),
    ("2011-07-22", "Norway attacks"),
    ("2013-04-24", "Rana Plaza collapse"),
    ("2013-11-08", "Typhoon Haiyan"),
    ("2014-03-08", "MH370 disappearance"),
    ("2014-04-16", "MV Sewol sinking"),
    ("2014-07-17", "MH17 shootdown"),
    ("2015-04-25", "Nepal (Gorkha) earthquake"),
    ("2015-11-13", "Paris attacks"),
    ("2017-06-14", "Grenfell Tower fire"),
    ("2017-08-25", "Hurricane Harvey landfall"),
    ("2017-09-19", "Puebla (Mexico) earthquake"),
    ("2018-11-08", "Camp Fire (California)"),
    ("2019-03-15", "Christchurch mosque attacks"),
    ("2020-08-04", "Beirut port explosion"),
    ("2021-06-24", "Surfside condo collapse"),
    ("2023-02-06", "Turkey-Syria earthquake"),
]
# Drop the intentional placeholder so the list stays honest and auditable.
DISASTERS = [(d, name) for d, name in DISASTERS if name != "no"]


def flow(dt: datetime) -> float:
    vals = [
        build_trajectory(dt, body, SPEC).diagnostics()["path_distance"]
        for body in NON_MOON
    ]
    return float(np.mean(vals))


def noon_utc(year: int, doy: int) -> datetime:
    base = datetime(year, 1, 1, 12, tzinfo=timezone.utc)
    return base + timedelta(days=doy)


def main() -> None:
    print(__doc__)
    rng = np.random.default_rng(SEED)

    dates = [datetime.fromisoformat(d).replace(tzinfo=timezone.utc) for d, _ in DISASTERS]
    n = len(dates)
    print(f"=== running | n={n} catastrophes | perms={PERMS} | seed={SEED} ===\n")

    # Observed flow per catastrophe (its actual date, 12:00 UTC).
    observed = np.array([flow(dt.replace(hour=12, minute=0, second=0)) for dt in dates])
    obs_mean = float(observed.mean())

    # Primary null: per catastrophe, precompute YEAR_SAMPLES random-day flows in
    # that catastrophe's own calendar year.
    years = [dt.year for dt in dates]
    span = 366
    year_pool = np.empty((n, YEAR_SAMPLES))
    for i, y in enumerate(years):
        for k in range(YEAR_SAMPLES):
            year_pool[i, k] = flow(noon_utc(y, int(rng.integers(0, span))))

    # Permutation: each cohort picks one same-year day per catastrophe.
    cohort_means = np.empty(PERMS)
    for j in range(PERMS):
        pick = rng.integers(0, YEAR_SAMPLES, size=n)
        cohort_means[j] = year_pool[np.arange(n), pick].mean()
    p_primary = float((cohort_means <= obs_mean).mean())

    # Secondary null: random dates across the full span (context only).
    lo, hi = min(dates), max(dates)
    total_days = (hi - lo).days
    broad = np.array([
        flow((lo + timedelta(days=int(rng.integers(0, total_days)))).replace(hour=12))
        for _ in range(BROAD_POOL)
    ])
    broad_cohorts = np.array([
        broad[rng.choice(BROAD_POOL, size=n, replace=False)].mean() for _ in range(PERMS)
    ])
    p_broad = float((broad_cohorts <= obs_mean).mean())

    print(f"observed catastrophe mean flow : {obs_mean:.4f}")
    print(f"primary null  (same-year days) : mean {cohort_means.mean():.4f}  "
          f"sd {cohort_means.std():.4f}")
    print(f"secondary null (full span)     : mean {broad_cohorts.mean():.4f}  "
          f"sd {broad_cohorts.std():.4f}")
    print()
    verdict = "REJECT H0 (p<0.05)" if p_primary < 0.05 else "FAIL TO REJECT H0"
    print(f"PRIMARY   one-tailed p (obs <= null) = {p_primary:.4f}   -> {verdict}")
    print(f"secondary one-tailed p               = {p_broad:.4f}   (context only)")
    print()
    print("Direction check: negative effect = catastrophes lower-flow than null.")
    print(f"  observed - primary null mean = {obs_mean - cohort_means.mean():+.4f}")

    out = {
        "n": n,
        "seed": SEED,
        "observed_mean": obs_mean,
        "primary_null_mean": float(cohort_means.mean()),
        "secondary_null_mean": float(broad_cohorts.mean()),
        "p_primary": p_primary,
        "p_secondary": p_broad,
        "effect": obs_mean - float(cohort_means.mean()),
        "disasters": [
            {"date": d, "name": name, "flow": float(f)}
            for (d, name), f in zip(DISASTERS, observed)
        ],
    }
    path = (
        "C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
        "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/flow_catastrophe_result.json"
    )
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
