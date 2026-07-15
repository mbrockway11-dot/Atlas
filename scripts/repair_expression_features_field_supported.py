from pathlib import Path

import pandas as pd


feature_path = Path(
    "output/investment_morphology_expression_v3/"
    "morphology_expression_features.csv"
)

score_path = Path(
    "output/investment_morphology_field_walk_forward/"
    "field_walk_forward_scores.csv"
)

backup_path = feature_path.with_suffix(
    ".before_field_supported_fix.csv"
)

features = pd.read_csv(
    feature_path,
    low_memory=False,
)

scores = pd.read_csv(
    score_path,
    low_memory=False,
)

if "field_supported" in features.columns:
    print("field_supported already exists")
    raise SystemExit(0)

required = {
    "timestamp",
    "fold_id",
    "morphology_cluster_id",
    "field_supported",
}

missing = sorted(
    required - set(scores.columns)
)

if missing:
    raise ValueError(
        f"Score file missing columns: {missing}"
    )

features.to_csv(
    backup_path,
    index=False,
)

support = (
    scores[
        [
            "timestamp",
            "fold_id",
            "morphology_cluster_id",
            "field_supported",
        ]
    ]
    .drop_duplicates(
        subset=[
            "timestamp",
            "fold_id",
            "morphology_cluster_id",
        ],
        keep="last",
    )
)

repaired = features.merge(
    support,
    on=[
        "timestamp",
        "fold_id",
        "morphology_cluster_id",
    ],
    how="left",
    validate="many_to_one",
)

if repaired["field_supported"].isna().any():
    missing_count = int(
        repaired[
            "field_supported"
        ].isna().sum()
    )

    raise ValueError(
        "Could not map field_supported for "
        f"{missing_count} rows."
    )

repaired.to_csv(
    feature_path,
    index=False,
)

print(
    "rows=",
    len(repaired),
)

print(
    "field_supported_true=",
    int(
        repaired[
            "field_supported"
        ]
        .astype(str)
        .str.lower()
        .isin(
            {
                "true",
                "1",
                "yes",
            }
        )
        .sum()
    ),
)

print(
    "saved=",
    feature_path,
)

print(
    "backup=",
    backup_path,
)
