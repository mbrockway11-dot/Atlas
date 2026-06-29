"""Export research matrix to CSV."""

from pathlib import Path

import pandas as pd

from atlas.research.matrix import build_research_matrix


def export_research_matrix(
    names: list[str],
    output_path: str | Path,
) -> Path:
    """
    Build and export the Atlas research matrix.

    One row is produced for every:
        Person × Cipher × Planet

    Returns
    -------
    Path
        Path to the written CSV.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = build_research_matrix(names)

    dataframe = pd.DataFrame(rows)

    dataframe.sort_values(
        by=[
            "name",
            "cipher",
            "planet",
        ],
        inplace=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path