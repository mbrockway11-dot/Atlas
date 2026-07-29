"""Pytest bootstrap.

Force a complete pandas import before any test module is collected. pandas
3.0.x (a pre-release line) intermittently raises a ``_pandas_datetime_CAPI``
circular-import error when several test modules import it during the same
collection pass -- each file passes alone, but a multi-file run can catch pandas
mid-initialization. Importing it once here, before collection begins, fully
initializes the C extension and removes the race.

A durable alternative is to pin ``pandas < 3.0`` in pyproject until 3.0 is
stable; this bootstrap fixes the symptom without requiring a reinstall.
"""

import pandas  # noqa: F401  (import-for-side-effect: full init before collection)
