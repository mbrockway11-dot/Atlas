"""Dashboard dataframe helpers."""

import pandas as pd


def dict_to_dataframe(data: dict, key_name: str, value_name: str) -> pd.DataFrame:
    """Convert dictionary to dataframe."""
    return pd.DataFrame(
        [
            {
                key_name: key,
                value_name: value,
            }
            for key, value in data.items()
        ]
    )